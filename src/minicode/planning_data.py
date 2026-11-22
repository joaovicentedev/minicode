"""Dados e métricas locais para o experimento de planejamento."""

import json
import re
import unicodedata
from pathlib import Path

from minicode.agent import build_plan_prompt


def load_examples(path: Path) -> list[dict[str, str]]:
    """Lê e valida exemplos JSONL com tarefa, especificação, contexto e plano."""
    examples = []
    required = {"task", "spec", "context", "plan"}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        valid_values = all(
            isinstance(item[key], str) and item[key].strip() for key in required & item.keys()
        )
        if set(item) != required or not valid_values:
            raise ValueError(f"Exemplo inválido na linha {number}")
        examples.append(item)
    if not examples:
        raise ValueError("Dataset vazio")
    return examples


def format_example(example: dict[str, str]) -> dict[str, str]:
    """Converte o exemplo no prompt realmente usado pelo agente."""
    return {
        "prompt": build_plan_prompt(example["task"], example["spec"], example["context"]),
        "completion": example["plan"],
    }


def plan_score(
    plan: str, rubric: dict[str, list[list[str]]] | None = None,
) -> dict[str, bool]:
    """Mede estrutura e, opcionalmente, evidências lexicais de uma rubrica por tarefa.

    Cada dimensão exige todos os grupos; basta uma alternativa por grupo.
    As evidências são aproximações auditáveis, não uma validação semântica.
    """
    lines = [line.strip() for line in plan.splitlines() if line.strip()]
    numbered = bool(lines) and all(re.match(r"^\d+[.)] \S", line) for line in lines)
    order = [int(re.match(r"^(\d+)", line).group(1)) for line in lines] if numbered else []
    text = plan.lower()
    scores = {
        "numbered": numbered and order == list(range(1, len(lines) + 1)),
        "mentions_tests": "test" in text,
        "mentions_pytest": "pytest -q" in text,
        "no_code_block": "```" not in plan,
        "no_completed_claim": not bool(
            re.search(r"\b(já (executei|criei|implementei)|testes passaram)\b", text)
        ),
    }
    scores["structural_pass"] = all(scores.values())
    if rubric is not None:
        if set(rubric) != {"task_alignment", "spec_coverage", "context_consistency"}:
            raise ValueError("Rubrica deve conter as três dimensões de qualidade")
        normalized = unicodedata.normalize("NFKD", text)
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        for dimension, groups in rubric.items():
            if not isinstance(groups, list) or not groups:
                raise ValueError("Dimensão da rubrica deve conter grupos não vazios")
            matched = []
            for alternatives in groups:
                if (
                    not isinstance(alternatives, list) or not alternatives
                    or any(not isinstance(term, str) or not term.strip() for term in alternatives)
                ):
                    raise ValueError("Grupo da rubrica deve conter termos não vazios")
                patterns = [
                    "".join(
                        char for char in unicodedata.normalize("NFKD", term.lower())
                        if not unicodedata.combining(char)
                    )
                    for term in alternatives
                ]
                matched.append(any(
                    re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", normalized)
                    for term in patterns
                ))
            scores[dimension] = all(matched)
        scores["quality_pass"] = all(scores[dimension] for dimension in rubric)
        scores["overall_pass"] = scores["structural_pass"] and scores["quality_pass"]
    return scores


def summarize_plans(
    answers: list[str], examples: list[dict[str, str]],
    rubrics: dict[str, dict[str, list[list[str]]]],
) -> dict[str, float]:
    """Calcula taxas por critério em pares completos de respostas e tarefas."""
    if not answers or len(answers) != len(examples):
        raise ValueError("Forneça uma resposta por exemplo e pelo menos um exemplo")
    if any(example["task"] not in rubrics for example in examples):
        raise ValueError("Rubrica ausente para uma tarefa avaliada")
    scores = [
        plan_score(answer, rubrics[example["task"]])
        for answer, example in zip(answers, examples, strict=True)
    ]
    return {key: sum(score[key] for score in scores) / len(scores) for key in scores[0]}
