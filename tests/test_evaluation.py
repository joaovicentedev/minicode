import json
import shutil
import subprocess
from pathlib import Path

import pytest

from minicode.evaluation import grade_cases, run_cases, select_cases
from minicode.tools import ProjectTools


class SequenceModel:
    def __init__(self, responses):
        self.responses = iter(responses)

    def complete(self, prompt, *, response_model=None):
        return next(self.responses)


class ReferenceModel:
    def complete(self, prompt, *, response_model=None):
        if response_model is None:
            return "Objetivo e critérios" if "Não implemente ainda" in prompt else "1. Implementar"
        solutions = {
            "sum_even": (
                "calculator.py",
                "def sum_even(numbers):\n    return sum(n for n in numbers if n % 2 == 0)\n",
            ),
            "normalize_name": (
                "names.py",
                "def normalize_name(name):\n    return ' '.join(name.split())\n",
            ),
            "list_items": (
                "catalog.py",
                "def list_items(items, page, page_size):\n"
                "    if page < 1 or page_size < 1:\n        raise ValueError\n"
                "    start = (page - 1) * page_size\n"
                "    return items[start:start + page_size]\n",
            ),
            "clamp(value": (
                "tests/test_clamp.py",
                "from clamp import clamp\n\n"
                "def test_below():\n    assert clamp(-1, 0, 10) == 0\n\n"
                "def test_inside():\n    assert clamp(5, 0, 10) == 5\n\n"
                "def test_above():\n    assert clamp(11, 0, 10) == 10\n",
            ),
            "valid_age": (
                "validation.py",
                "def valid_age(age):\n"
                "    if isinstance(age, bool) or not isinstance(age, int) "
                "or not 0 <= age <= 120:\n        raise ValueError\n"
                "    return age\n",
            ),
            "word_count": ("words.py", "def word_count(text):\n    return len(text.split())\n"),
        }
        for marker, (path, content) in solutions.items():
            if marker in prompt:
                return json.dumps({"files": [{"path": path, "content": content}]})
        raise ValueError("Tarefa desconhecida")


def test_run_and_grade_keep_acceptance_tests_outside_agent_project(tmp_path):
    cases = tmp_path / "cases"
    case = cases / "one"
    (case / "project").mkdir(parents=True)
    (case / "checks").mkdir()
    (case / "task.json").write_text(
        json.dumps({"category": "função", "task": "Corrija answer"}), encoding="utf-8"
    )
    (case / "project" / "tests").mkdir()
    (case / "project" / "pytest.ini").write_text("[pytest]\npythonpath = .\n")
    (case / "project" / "tests" / "test_visible.py").write_text(
        "def test_visible():\n    assert True\n", encoding="utf-8"
    )
    (case / "checks" / "test_acceptance.py").write_text(
        "from answer import answer\n\ndef test_answer():\n    assert answer() == 42\n",
        encoding="utf-8",
    )
    model = SequenceModel(
        [
            "spec",
            "plan",
            json.dumps(
                {"files": [{"path": "answer.py", "content": "def answer():\n    return 0\n"}]}
            ),
        ]
    )

    run = run_cases(model, cases, tmp_path / "output")

    project = tmp_path / "output" / "one" / "project"
    assert run["cases"][0]["agent_state"] == "DONE"
    assert run["cases"][0]["llm_calls"] == 3
    assert not list(project.rglob("*acceptance*.py"))
    assert json.loads((tmp_path / "output" / "run.json").read_text()) == run

    report = grade_cases(cases, tmp_path / "output")

    assert report["task_success_rate"] == 0
    assert report["first_attempt_success"] == 0
    assert report["average_iterations"] == 1
    assert report["average_llm_calls"] == 3
    assert report["cases"][0]["agent_state"] == "DONE"
    assert report["cases"][0]["acceptance_returncode"] != 0
    assert not list(project.rglob("*acceptance*.py"))
    assert json.loads((tmp_path / "output" / "report.json").read_text()) == report
    with pytest.raises(ValueError):
        run_cases(model, cases, tmp_path / "output")


def test_all_evaluation_cases_have_required_categories_and_checks():
    cases = Path(__file__).resolve().parents[1] / "evaluation" / "cases"
    categories = set()
    for case in cases.iterdir():
        metadata = json.loads((case / "task.json").read_text(encoding="utf-8"))
        categories.add(metadata["category"])
        assert metadata["task"]
        assert list((case / "project" / "tests").glob("test_*.py"))
        assert list((case / "checks").glob("test_*.py"))
    assert len(categories) == 6


def test_reference_model_passes_all_six_acceptance_suites(tmp_path):
    cases = Path(__file__).resolve().parents[1] / "evaluation" / "cases"

    run_cases(ReferenceModel(), cases, tmp_path / "results")
    report = grade_cases(cases, tmp_path / "results")

    assert report["task_success_rate"] == 1
    assert report["first_attempt_success"] == 1
    assert report["average_iterations"] == 1
    assert report["average_llm_calls"] == 3
    assert len(report["cases"]) == 6


def test_select_and_run_only_validation_case(tmp_path):
    cases = Path(__file__).resolve().parents[1] / "evaluation" / "cases"
    assert [case.name for case in select_cases(cases, ["05_validation"])] == ["05_validation"]
    with pytest.raises(ValueError, match="desconhecido"):
        select_cases(cases, ["missing"])

    run = run_cases(ReferenceModel(), cases, tmp_path / "single", case_names=["05_validation"])
    report = grade_cases(cases, tmp_path / "single")

    assert [case["case"] for case in run["cases"]] == ["05_validation"]
    assert [case["case"] for case in report["cases"]] == ["05_validation"]
    assert report["task_success_rate"] == 1
    assert not (tmp_path / "single" / "01_function").exists()


def test_visible_validation_failure_identifies_boolean_input(tmp_path):
    source = Path(__file__).resolve().parents[1] / "evaluation/cases/05_validation/project"
    project = tmp_path / "project"
    shutil.copytree(source, project)

    result = ProjectTools(project).run_tests()

    assert result.returncode == 1
    assert "test_valid_age_rejects_booleans[True]" in result.stdout
    assert "test_valid_age_rejects_booleans[False]" in result.stdout


def test_validation_case_can_be_repaired_from_visible_failure(tmp_path):
    cases = Path(__file__).resolve().parents[1] / "evaluation" / "cases"
    wrong = json.dumps(
        {
            "files": [
                {
                    "path": "validation.py",
                    "content": "def valid_age(age):\n"
                    "    if not isinstance(age, int) or not 0 <= age <= 120:\n"
                    "        raise ValueError\n"
                    "    return age\n",
                }
            ]
        }
    )
    fixed = json.dumps(
        {
            "files": [
                {
                    "path": "validation.py",
                    "content": "def valid_age(age):\n"
                    "    if type(age) is not int or not 0 <= age <= 120:\n"
                    "        raise ValueError\n"
                    "    return age\n",
                }
            ]
        }
    )

    run_cases(
        SequenceModel(["spec", "plan", wrong, fixed]),
        cases,
        tmp_path / "repaired",
        case_names=["05_validation"],
    )
    report = grade_cases(cases, tmp_path / "repaired")

    assert report["task_success_rate"] == 1
    assert report["first_attempt_success"] == 0
    assert report["average_iterations"] == 2
    assert report["average_llm_calls"] == 4


def test_evaluation_rejects_changes_to_existing_visible_tests(tmp_path):
    cases = Path(__file__).resolve().parents[1] / "evaluation" / "cases"
    changed_test = json.dumps(
        {
            "files": [
                {
                    "path": "tests/test_validation.py",
                    "content": "def test_fake():\n    assert True\n",
                }
            ]
        }
    )
    fixed_code = json.dumps(
        {
            "files": [
                {
                    "path": "validation.py",
                    "content": "def valid_age(age):\n"
                    "    if type(age) is not int or not 0 <= age <= 120:\n"
                    "        raise ValueError\n"
                    "    return age\n",
                }
            ]
        }
    )
    source_test = cases / "05_validation/project/tests/test_validation.py"

    run_cases(
        SequenceModel(["spec", "plan", changed_test, fixed_code]),
        cases,
        tmp_path / "protected",
        case_names=["05_validation"],
    )
    generated_test = tmp_path / "protected/05_validation/project/tests/test_validation.py"
    report = grade_cases(cases, tmp_path / "protected")

    assert generated_test.read_text(encoding="utf-8") == source_test.read_text(encoding="utf-8")
    assert report["task_success_rate"] == 1
    assert report["average_iterations"] == 2


def test_evaluation_cli_help():
    result = subprocess.run(
        ["uv", "run", "minicode-eval", "run", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--cases" in result.stdout
    assert "--output" in result.stdout
    assert "--case" in result.stdout
    grade = subprocess.run(
        ["uv", "run", "minicode-eval", "grade", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert grade.returncode == 0
    assert "--run" in grade.stdout
    assert "--case" in grade.stdout
