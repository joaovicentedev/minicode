"""Adaptador local usado apenas pelos testes do próprio MiniCode."""

import os
import subprocess
import sys
from pathlib import Path

from minicode.agent import Agent
from minicode.tools import CommandResult, ProjectTools


class LocalSandbox:
    """Executa fixtures de teste sem depender do daemon Docker no CI."""

    def run(self, project: Path, timeout: int, checks: Path | None = None) -> CommandResult:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(project.resolve()), str(project.resolve() / "src"))
        )
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
        if checks is not None:
            command.append(str(checks.resolve()))
        completed = subprocess.run(
            command, cwd=project, env=environment,
            capture_output=True, text=True, timeout=timeout, check=False,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class LocalAgent(Agent):
    """Agente de teste com executor de fixtures injetado."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sandbox=LocalSandbox(), **kwargs)


class LocalProjectTools(ProjectTools):
    """Ferramentas de teste com executor de fixtures injetado."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, sandbox=LocalSandbox(), **kwargs)
