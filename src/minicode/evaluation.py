"""Execução de casos e avaliação externa das soluções produzidas."""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from minicode.agent import Agent
from minicode.llm import LanguageModel, OpenAIChatModel
from minicode.tools import CommandResult


def select_cases(cases_dir: Path, names: list[str] | None = None) -> list[Path]:
    """Seleciona casos válidos sem aceitar nomes desconhecidos."""
    available = {
        path.name: path for path in cases_dir.iterdir() if (path / "task.json").is_file()
    }
    selected = sorted(available) if names is None else sorted(set(names))
    if not selected:
        raise ValueError("Nenhum caso de avaliação encontrado")
    unknown = set(selected) - available.keys()
    if unknown:
        raise ValueError(f"Caso de avaliação desconhecido: {', '.join(sorted(unknown))}")
    return [available[name] for name in selected]


def run_cases(
    model: LanguageModel,
    cases_dir: Path,
    output_dir: Path,
    max_attempts: int = 2,
    case_names: list[str] | None = None,
    workers: int = 4,
) -> dict:
    """Executa os casos em projetos isolados e guarda os resultados iniciais."""
    cases = select_cases(cases_dir, case_names)
    if workers < 1:
        raise ValueError("workers deve ser pelo menos 1")
    if output_dir.exists():
        raise ValueError(f"Diretório de saída já existe: {output_dir}")
    output_dir.mkdir(parents=True)
    def run_case(case: Path) -> dict:
        metadata = json.loads((case / "task.json").read_text(encoding="utf-8"))
        project = output_dir / case.name / "project"
        shutil.copytree(case / "project", project)
        existing_tests = {
            path.relative_to(project).as_posix()
            for path in (project / "tests").rglob("test_*.py")
        }
        agent = Agent(
            model, project, max_attempts=max_attempts, read_only_paths=existing_tests
        )
        error = None
        try:
            agent.run(metadata["task"])
        except Exception as caught:
            error = f"{type(caught).__name__}: {caught}"
        state = json.loads((agent.trace.path / "state.json").read_text(encoding="utf-8"))
        return {
            "case": case.name,
            "category": metadata["category"],
            "agent_state": state["status"],
            "iterations": state["attempts"],
            "llm_calls": state["llm_calls"],
            "error": error,
            "trace": str(agent.trace.path),
        }
    with ThreadPoolExecutor(max_workers=min(workers, len(cases))) as executor:
        results = list(executor.map(run_case, cases))
    run = {"cases": results}
    (output_dir / "run.json").write_text(
        json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return run


def run_acceptance(project: Path, checks: Path) -> CommandResult:
    """Roda somente os testes externos contra o projeto produzido."""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(project.resolve()), environment.get("PYTHONPATH", "")) if part
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                str(checks.resolve()),
            ],
            cwd=project,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        return CommandResult(124, stdout, stderr + "\nTestes de aceitação excederam 120 segundos")


def grade_cases(
    cases_dir: Path, output_dir: Path, case_names: list[str] | None = None, workers: int = 4
) -> dict:
    """Calcula as métricas sem chamar o agente nem alterar as soluções."""
    if workers < 1:
        raise ValueError("workers deve ser pelo menos 1")
    if case_names is None:
        case_names = [path.name for path in output_dir.iterdir() if (path / "project").is_dir()]
    cases = select_cases(cases_dir, case_names)
    def grade_case(case: Path) -> dict:
        project = output_dir / case.name / "project"
        traces = sorted((project / ".minicode" / "runs").glob("*/state.json"))
        if not traces:
            raise ValueError(f"Execução não encontrada para {case.name}")
        state = json.loads(traces[-1].read_text(encoding="utf-8"))
        metadata = json.loads((case / "task.json").read_text(encoding="utf-8"))
        acceptance = run_acceptance(project, case / "checks")
        success = state["status"] == "DONE" and acceptance.returncode == 0
        return {
            "case": case.name,
            "category": metadata["category"],
            "success": success,
            "first_attempt_success": success and state["attempts"] == 1,
            "iterations": state["attempts"],
            "llm_calls": state["llm_calls"],
            "agent_state": state["status"],
            "acceptance_returncode": acceptance.returncode,
            "acceptance_stdout": acceptance.stdout,
            "acceptance_stderr": acceptance.stderr,
            "trace": str(traces[-1].parent),
        }
    with ThreadPoolExecutor(max_workers=min(workers, len(cases))) as executor:
        results = list(executor.map(grade_case, cases))
    total = len(results)
    report = {
        "task_success_rate": sum(item["success"] for item in results) / total,
        "first_attempt_success": sum(item["first_attempt_success"] for item in results) / total,
        "average_iterations": sum(item["iterations"] for item in results) / total,
        "average_llm_calls": sum(item["llm_calls"] for item in results) / total,
        "cases": results,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    """Expõe comandos separados para executar o agente e avaliar as soluções."""
    parser = argparse.ArgumentParser(description="Avalia o MiniCode em tarefas de programação")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Executa o agente nos casos")
    run.add_argument("--cases", type=Path, default=Path("evaluation/cases"))
    run.add_argument("--output", type=Path)
    run.add_argument("--max-attempts", type=int, default=2)
    run.add_argument("--workers", type=int, default=4, help="Casos em paralelo (padrão: 4)")
    run.add_argument("--case", action="append", help="Caso a executar; pode ser repetido")
    grade = commands.add_parser("grade", help="Testa as soluções sem chamar o agente")
    grade.add_argument("--cases", type=Path, default=Path("evaluation/cases"))
    grade.add_argument("--run", type=Path, required=True)
    grade.add_argument("--workers", type=int, default=4, help="Casos em paralelo (padrão: 4)")
    grade.add_argument("--case", action="append", help="Caso a avaliar; padrão: casos da execução")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    try:
        if args.command == "run":
            output = args.output or Path("evaluation/results") / datetime.now(UTC).strftime(
                "%Y%m%dT%H%M%SZ"
            )
            run_cases(
                OpenAIChatModel.from_environment(),
                args.cases,
                output,
                args.max_attempts,
                args.case,
                args.workers,
            )
            print(f"Execução: {output / 'run.json'}")
            print(f"Avalie com: uv run minicode-eval grade --run {output}")
        else:
            report = grade_cases(args.cases, args.run, args.case, args.workers)
            metrics = {key: value for key, value in report.items() if key != "cases"}
            print(json.dumps(metrics, indent=2))
            print(f"Relatório: {args.run / 'report.json'}")
    except (OSError, ValueError) as error:
        parser.exit(1, f"minicode-eval: {error}\n")
