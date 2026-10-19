import json

import pytest

from minicode.agent import Agent, State
from minicode.tools import ProjectTools
from minicode.trace import RunTrace


class SequenceModel:
    def __init__(self, responses):
        self.responses = iter(responses)

    def complete(self, prompt, *, response_model=None):
        return next(self.responses)


def test_run_trace_persists_documents_events_and_counters(tmp_path):
    trace = RunTrace(tmp_path, "Crie uma função")
    trace.document("specification", "Objetivo e critérios")
    trace.document("plan", "1. Implementar")
    trace.event("llm", number=1, stage="spec")
    trace.event("attempt", number=1)
    trace.event("write", path="main.py")
    trace.event("write", path="main.py")
    trace.event("test", command="pytest -q", returncode=0)
    trace.event("state", status="DONE")
    trace.finish("OK")

    state = json.loads((trace.path / "state.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (trace.path / "actions.jsonl").read_text().splitlines()]
    assert state == {
        "task": "Crie uma função",
        "status": "DONE",
        "attempts": 1,
        "llm_calls": 1,
        "test_runs": 1,
        "changed_files": ["main.py"],
        "result": "OK",
    }
    assert (trace.path / "specification.md").read_text() == "Objetivo e critérios\n"
    assert (trace.path / "plan.md").read_text() == "1. Implementar\n"
    assert events[-1]["kind"] == "result"
    with pytest.raises(ValueError):
        trace.document("other", "x")


def test_agent_persists_complete_execution_and_hides_trace_from_tools(tmp_path):
    model = SequenceModel(
        [
            "Spec com critérios",
            "1. Criar teste",
            json.dumps(
                {"files": [{"path": "test_answer.py", "content": "def test_ok():\n    assert 1\n"}]}
            ),
        ]
    )
    agent = Agent(model, tmp_path)

    agent.run("Crie teste")

    assert agent.state is State.DONE
    assert ".minicode" not in " ".join(ProjectTools(tmp_path).list_files())
    state = json.loads((agent.trace.path / "state.json").read_text(encoding="utf-8"))
    actions = (agent.trace.path / "actions.jsonl").read_text(encoding="utf-8")
    assert state["task"] == "Crie teste"
    assert state["llm_calls"] == 3
    assert state["attempts"] == 1
    assert state["test_runs"] == 1
    assert state["changed_files"] == ["test_answer.py"]
    assert '"name": "list_files"' in actions
    assert '"command": "pytest -q"' in actions
    with pytest.raises(ValueError):
        ProjectTools(tmp_path).write_file(".minicode/forbidden.txt", "x")


def test_agent_records_failed_model_call(tmp_path):
    agent = Agent(SequenceModel([]), tmp_path)

    with pytest.raises(StopIteration):
        agent.run("Crie algo")

    state = json.loads((agent.trace.path / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "FAILED"
    assert state["llm_calls"] == 1


def test_agent_trace_counts_repair_attempts_and_test_failures(tmp_path):
    first = json.dumps(
        {"files": [{"path": "answer.py", "content": "def answer():\n    return 0\n"}]}
    )
    repaired = json.dumps(
        {"files": [{"path": "answer.py", "content": "def answer():\n    return 42\n"}]}
    )
    (tmp_path / "test_answer.py").write_text(
        "from answer import answer\n\ndef test_answer():\n    assert answer() == 42\n",
        encoding="utf-8",
    )
    agent = Agent(SequenceModel(["spec", "plan", first, repaired]), tmp_path)

    agent.run("Corrija answer")

    state = json.loads((agent.trace.path / "state.json").read_text(encoding="utf-8"))
    action_lines = (agent.trace.path / "actions.jsonl").read_text().splitlines()
    events = [json.loads(line) for line in action_lines]
    assert agent.state is State.DONE
    assert state["attempts"] == 2
    assert state["llm_calls"] == 4
    assert state["test_runs"] == 2
    assert [event["returncode"] for event in events if event["kind"] == "test"] == [1, 0]
    assert any(event.get("status") == "REPAIRING" for event in events)
