import json
import logging

import pytest

from minicode.agent import Agent, State


class SequenceModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.prompts = []

    def complete(self, prompt, *, response_model=None):
        self.prompts.append(prompt)
        return next(self.responses)


def test_agent_completes_spec_plan_implementation_and_verification(tmp_path, caplog):
    model = SequenceModel(
        [
            "Spec: calcule a resposta",
            "1. Criar o teste",
            json.dumps(
                {
                    "files": [
                        {
                            "path": "test_answer.py",
                            "content": "def test_answer():\n    assert 42 == 42\n",
                        }
                    ]
                }
            ),
            '{"accepted": true, "reason": "Critério coberto pelo teste"}',
        ]
    )
    agent = Agent(model, tmp_path)

    with caplog.at_level(logging.INFO):
        result = agent.run("Crie um teste simples")

    assert "passed" in result
    assert agent.state is State.DONE
    assert "Turno LLM 1 (especificação)" in caplog.text
    assert "Turno LLM 2 (plano)" in caplog.text
    assert "Turno LLM 3 (implementação/reparo)" in caplog.text


def test_agent_rejects_empty_task(tmp_path):
    agent = Agent(SequenceModel([]), tmp_path)

    with pytest.raises(ValueError):
        agent.run("  ")


def test_agent_limits_attempts_on_invalid_model_output(tmp_path):
    agent = Agent(SequenceModel(["spec", "plan", "not json"]), tmp_path, max_attempts=1)

    result = agent.run("Tarefa")

    assert "Resposta inválida" in result
    assert agent.state is State.FAILED


def test_agent_marks_empty_pytest_collection_as_unverified(tmp_path):
    model = SequenceModel(
        [
            "spec",
            "plan",
            json.dumps({"files": [{"path": "index.html", "content": "<h1>Snake</h1>"}]}),
        ]
    )
    agent = Agent(model, tmp_path / "web-project")

    result = agent.run("Crie uma página simples")

    assert "não encontrou testes" in result
    assert agent.state is State.UNVERIFIED
    assert (tmp_path / "web-project" / "index.html").exists()


def test_agent_repair_feedback_includes_current_files_and_test_error(tmp_path):
    agent = Agent(SequenceModel([]), tmp_path)
    agent.tools.write_file("main.py", "print('old')")

    feedback = agent._repair_feedback("Corrija main", "AssertionError", ["main.py"])

    assert "Corrija main" in feedback
    assert "AssertionError" in feedback
    assert "print('old')" in feedback
    assert "preserve os testes existentes" in feedback
    assert "isinstance(True, int)" in feedback


def test_implementation_prompt_allows_project_subdirectories():
    prompt = Agent._implementation_prompt("Crie um app", "spec", "plan")

    assert "raiz de trabalho do projeto" in prompt
    assert "Crie nessa pasta os arquivos e subpastas necessários" in prompt
    assert "nunca podem sair dela" in prompt
    assert "isinstance(True, int)" in prompt
    assert "Argumentos padrão mutáveis" in prompt


def test_agent_parses_file_payload():
    files = Agent._parse_files('{"files": [{"path": "x.py", "content": "x = 1"}]}')

    assert files.files[0].path == "x.py"
    assert files.files[0].content == "x = 1"


def test_agent_parses_json_wrapped_in_markdown():
    files = Agent._parse_files(
        'Resposta:\n```json\n{"files": [{"path": "x.py", "content": "ok"}]}\n```'
    )

    assert files.files[0].content == "ok"


def test_agent_project_context_includes_source_and_excludes_environment_files(tmp_path):
    agent = Agent(SequenceModel([]), tmp_path)
    agent.tools.write_file("src/app.py", "print('hello')")
    (tmp_path / ".env").write_text("API_KEY=secret", encoding="utf-8")

    context = agent._project_context()

    assert "src/app.py" in context
    assert "API_KEY" not in context


def test_agent_project_context_reads_tests_before_source_file_limit(tmp_path):
    agent = Agent(SequenceModel([]), tmp_path)
    for number in range(21):
        agent.tools.write_file(f"module_{number:02}.py", "value = 1\n")
    agent.tools.write_file("tests/test_required.py", "def test_required():\n    assert True\n")

    context = agent._project_context()

    assert "tests/test_required.py" in context
    assert context.startswith("--- tests/test_required.py ---")


def test_agent_prompts_preserve_explicit_task_constraints(tmp_path):
    model = SequenceModel(
        [
            "Spec incompleta",
            "Plano incompleto",
            json.dumps({"files": [{"path": "validation.py", "content": "pass\n"}]}),
        ]
    )
    agent = Agent(model, tmp_path)

    agent.run("Rejeite bool mesmo sendo subtipo de int")

    assert "restrições explícitas" in model.prompts[0]
    assert "Não inclua código" in model.prompts[0]
    assert "Tarefa original:\nRejeite bool" in model.prompts[1]
    assert "não inclua código pronto" in model.prompts[1]
    assert "A tarefa original prevalece" in model.prompts[2]


def test_agent_repair_prompt_repeats_task_and_failed_test(tmp_path):
    (tmp_path / "test_answer.py").write_text(
        "from answer import answer\n\ndef test_answer():\n    assert answer() == 42\n",
        encoding="utf-8",
    )
    first = json.dumps(
        {"files": [{"path": "answer.py", "content": "def answer():\n    return 0\n"}]}
    )
    repaired = json.dumps(
        {"files": [{"path": "answer.py", "content": "def answer():\n    return 42\n"}]}
    )
    model = SequenceModel(
        [
            "spec equivocada",
            "plano equivocado",
            first,
            repaired,
            '{"accepted": true, "reason": "Correção verificada"}',
        ]
    )

    result = Agent(model, tmp_path).run("Corrija answer para retornar 42")

    assert "passed" in result
    assert "Tarefa original e suas restrições:\nCorrija answer para retornar 42" in model.prompts[3]
    assert "FAILED test_answer.py" in model.prompts[3]
    assert "def answer():\n    return 0" in model.prompts[3]
    assert "--- test_answer.py ---" in model.prompts[3]
    assert "spec equivocada" not in model.prompts[3]
    assert "plano equivocado" not in model.prompts[3]


def test_agent_rejects_invalid_file_payload():
    with pytest.raises(ValueError):
        Agent._parse_files('{"files": []}')


def test_agent_rejects_invalid_state_transition(tmp_path):
    agent = Agent(SequenceModel([]), tmp_path)

    with pytest.raises(ValueError, match="RECEIVED -> DONE"):
        agent._transition(State.DONE)

    assert agent.state is State.RECEIVED


def test_agent_repairs_when_acceptance_review_rejects(tmp_path):
    first = json.dumps(
        {
            "files": [
                {"path": "test_answer.py", "content": "def test_answer():\n    assert 1 == 1\n"}
            ]
        }
    )
    repaired = json.dumps(
        {
            "files": [
                {"path": "test_answer.py", "content": "def test_answer():\n    assert 42 == 42\n"}
            ]
        }
    )
    model = SequenceModel(
        [
            "Critério: verificar 42",
            "1. Criar teste",
            first,
            '{"accepted": false, "reason": "O teste não verifica 42"}',
            repaired,
            '{"accepted": true, "reason": "O teste verifica 42"}',
        ]
    )
    agent = Agent(model, tmp_path)

    agent.run("Verifique 42")

    assert agent.state is State.DONE
    assert "O teste não verifica 42" in model.prompts[4]
    assert json.loads((agent.trace.path / "state.json").read_text())["attempts"] == 2


def test_agent_fails_when_acceptance_review_rejects_last_attempt(tmp_path):
    model = SequenceModel(
        [
            "Critério: verificar 42",
            "1. Criar teste",
            json.dumps(
                {
                    "files": [
                        {
                            "path": "test_answer.py",
                            "content": "def test_answer():\n    assert True\n",
                        }
                    ]
                }
            ),
            '{"accepted": false, "reason": "Critério não coberto"}',
        ]
    )
    agent = Agent(model, tmp_path, max_attempts=1)

    result = agent.run("Verifique 42")

    assert agent.state is State.FAILED
    assert "Critério não coberto" in result
