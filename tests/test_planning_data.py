import json

import pytest

from minicode.planning_data import format_example, load_examples, plan_score, summarize_plans


def test_load_examples_and_splits_are_disjoint():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "notebooks/data"
    splits = [load_examples(root / f"{name}.jsonl") for name in ("train", "validation", "test")]
    assert [len(split) for split in splits] == [80, 10, 10]
    tasks = [item["task"] for split in splits for item in split]
    assert len(tasks) == len(set(tasks))
    for split in splits:
        for item in split:
            assert all(plan_score(item["plan"]).values())
    contexts = [item["context"] for split in splits for item in split]
    assert len(contexts) == len(set(contexts))


def test_load_examples_rejects_invalid_rows(tmp_path):
    path = tmp_path / "invalid.jsonl"
    path.write_text(json.dumps({"task": "x"}), encoding="utf-8")
    with pytest.raises(ValueError, match="linha 1"):
        load_examples(path)


def test_format_example_uses_agent_prompt():
    item = {"task": "Tarefa X", "spec": "Spec Y", "context": "Arquivo Z", "plan": "1. Ação"}
    formatted = format_example(item)
    assert "Você está na etapa PLAN" in formatted["prompt"]
    assert "Tarefa X" in formatted["prompt"]
    assert "Spec Y" in formatted["prompt"]
    assert "Arquivo Z" in formatted["prompt"]
    assert formatted["completion"] == "1. Ação"


def test_plan_score_checks_required_structure():
    good = "1. Ler arquivo.\n2. Criar testes.\n3. Executar pytest -q."
    assert all(plan_score(good).values())
    bad = "Já implementei.\n```python\npass\n```"
    assert not plan_score(bad)["numbered"]
    assert not plan_score(bad)["no_code_block"]
    assert not plan_score(bad)["no_completed_claim"]


RUBRIC = {
    "task_alignment": [["ordenação", "ordenar"], ["data"]],
    "spec_coverage": [["fora de ordem"], ["vazia", "vazio"]],
    "context_consistency": [["events.py"]],
}
GOOD_PLAN = (
    "1. Ler events.py.\n2. Ordenar pela data.\n"
    "3. Testar eventos fora de ordem e lista vazia.\n4. Executar pytest -q."
)


def test_rubric_rejects_generic_plan_despite_valid_structure():
    scores = plan_score("1. Ler arquivo.\n2. Criar testes.\n3. Executar pytest -q.", RUBRIC)
    assert scores["structural_pass"]
    assert not scores["task_alignment"]
    assert not scores["spec_coverage"]
    assert not scores["context_consistency"]
    assert not scores["quality_pass"]
    assert not scores["overall_pass"]


def test_rubric_accepts_alternatives_ignoring_accents_and_case():
    assert all(plan_score(GOOD_PLAN.replace("Ordenar", "ORDENACAO"), RUBRIC).values())


def test_rubric_separates_missing_criterion_and_wrong_file():
    scores = plan_score(GOOD_PLAN.replace("vazia", "com itens"), RUBRIC)
    assert scores["task_alignment"]
    assert scores["context_consistency"]
    assert not scores["spec_coverage"]
    assert not scores["overall_pass"]
    scores = plan_score(GOOD_PLAN.replace("events.py", "other.py"), RUBRIC)
    assert scores["spec_coverage"]
    assert not scores["context_consistency"]


def test_rubric_term_does_not_match_inside_another_word():
    scores = plan_score(GOOD_PLAN.replace("data", "database"), RUBRIC)
    assert not scores["task_alignment"]


@pytest.mark.parametrize("rubric", [
    {}, {**RUBRIC, "unexpected": [["x"]]},
    {**RUBRIC, "task_alignment": []},
    {**RUBRIC, "task_alignment": [[]]},
    {**RUBRIC, "task_alignment": [[""]]},
    {**RUBRIC, "task_alignment": [[1]]},
    {**RUBRIC, "task_alignment": ["data"]},
])
def test_plan_score_rejects_invalid_rubric(rubric):
    with pytest.raises(ValueError):
        plan_score(GOOD_PLAN, rubric)


def test_summary_aggregates_per_criterion_and_joint_success():
    examples = [{"task": "sort"}, {"task": "sort"}]
    metrics = summarize_plans([GOOD_PLAN, "1. Executar pytest -q."], examples, {"sort": RUBRIC})
    assert metrics["structural_pass"] == 1.0
    assert metrics["task_alignment"] == 0.5
    assert metrics["quality_pass"] == 0.5
    assert metrics["overall_pass"] == 0.5


@pytest.mark.parametrize("answers,examples,rubrics", [
    ([], [], {}),
    ([GOOD_PLAN], [], {}),
    ([], [{"task": "sort"}], {"sort": RUBRIC}),
    ([GOOD_PLAN], [{"task": "sort"}], {}),
])
def test_summary_rejects_missing_answers_or_rubrics(answers, examples, rubrics):
    with pytest.raises(ValueError):
        summarize_plans(answers, examples, rubrics)


def test_evaluation_rubrics_cover_only_validation_and_test():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "notebooks/data"
    rubrics = json.loads((root / "rubrics.json").read_text())
    examples = load_examples(root / "validation.jsonl") + load_examples(root / "test.jsonl")
    assert set(rubrics) == {example["task"] for example in examples}
    for example in examples:
        scores = plan_score(example["plan"], rubrics[example["task"]])
        assert scores["structural_pass"]
        assert scores["task_alignment"]
        assert scores["context_consistency"]
        # A referência antiga não explicita a exceção exigida na especificação.
        if "arithmetic.py" in example["task"]:
            assert not scores["spec_coverage"]
        else:
            assert scores["overall_pass"]


def test_overall_pass_requires_structure_even_with_all_quality_evidence():
    scores = plan_score(GOOD_PLAN.replace("1. ", ""), RUBRIC)
    assert scores["quality_pass"]
    assert not scores["structural_pass"]
    assert not scores["overall_pass"]
