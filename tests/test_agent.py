import json
import logging

import pytest

from minicode.agent import Agent, State


class SequenceModel:
    def __init__(self, responses):
        self.responses = iter(responses)

    def complete(self, prompt, *, response_model=None):
        return next(self.responses)


def test_agent_completes_spec_plan_implementation_and_verification(tmp_path, caplog):
    model = SequenceModel(
        [
            "Spec: calcule a resposta",
            "1. Criar o teste",
            json.dumps({"files": [{"path": "test_answer.py", "content": "def test_answer():\n    assert 42 == 42\n"}]}),
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


def test_agent_parses_file_payload():
    files = Agent._parse_files('{"files": [{"path": "x.py", "content": "x = 1"}]}')

    assert files.files[0].path == "x.py"
    assert files.files[0].content == "x = 1"


def test_agent_parses_json_wrapped_in_markdown():
    files = Agent._parse_files('Resposta:\n```json\n{"files": [{"path": "x.py", "content": "ok"}]}\n```')

    assert files.files[0].content == "ok"


def test_agent_project_context_includes_source_and_excludes_environment_files(tmp_path):
    agent = Agent(SequenceModel([]), tmp_path)
    agent.tools.write_file("src/app.py", "print('hello')")
    (tmp_path / ".env").write_text("API_KEY=secret", encoding="utf-8")

    context = agent._project_context()

    assert "src/app.py" in context
    assert "API_KEY" not in context


def test_agent_rejects_invalid_file_payload():
    with pytest.raises(ValueError):
        Agent._parse_files('{"files": []}')
