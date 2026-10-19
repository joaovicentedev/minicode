"""Registro persistente das execuções do agente."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class RunTrace:
    """Guarda eventos e estado de uma execução fora do contexto do modelo."""

    def __init__(self, project: Path, task: str):
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        self.path = project / ".minicode" / "runs" / run_id
        self.path.mkdir(parents=True)
        self.state = {
            "task": task,
            "status": "RECEIVED",
            "attempts": 0,
            "llm_calls": 0,
            "test_runs": 0,
            "changed_files": [],
            "result": None,
        }
        self._save_state()
        self.event("state", status="RECEIVED")

    def event(self, kind: str, **data: object) -> None:
        """Acrescenta uma ação e atualiza os contadores da execução."""
        if kind == "state":
            self.state["status"] = data["status"]
        elif kind == "attempt":
            self.state["attempts"] += 1
        elif kind == "llm":
            self.state["llm_calls"] += 1
        elif kind == "test":
            self.state["test_runs"] += 1
        elif kind == "write":
            path = data["path"]
            if path not in self.state["changed_files"]:
                self.state["changed_files"].append(path)
        record = {"time": datetime.now(UTC).isoformat(), "kind": kind, **data}
        with (self.path / "actions.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._save_state()

    def document(self, name: str, content: str) -> None:
        """Salva a especificação ou o plano produzido pelo modelo."""
        if name not in {"specification", "plan"}:
            raise ValueError("Documento de execução desconhecido")
        (self.path / f"{name}.md").write_text(content + "\n", encoding="utf-8")
        self.event("document", name=name)

    def finish(self, result: str) -> None:
        """Registra o resultado final mesmo quando a execução falha."""
        self.state["result"] = result
        self.event("result", status=self.state["status"], text=result)

    def _save_state(self) -> None:
        (self.path / "state.json").write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
