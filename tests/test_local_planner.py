from types import SimpleNamespace
from unittest.mock import MagicMock as Mock

import pytest

from minicode.llm.local_planner import LocalPlanner


def test_local_planner_generates_only_completion():
    inputs = Mock()
    inputs.to.return_value = {"input_ids": SimpleNamespace(shape=(1, 3))}
    tokenizer = Mock(eos_token_id=7)
    tokenizer.return_value = inputs
    tokenizer.decode.return_value = "1. Ler os testes."
    model = Mock(device="cpu")
    planner = LocalPlanner(model, tokenizer)
    assert planner.model is model
    assert planner.max_new_tokens == 160
    assert planner.complete("tarefa") == "1. Ler os testes."
    tokenizer.apply_chat_template.assert_called_once_with(
        [{"role": "user", "content": "tarefa"}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False,
    )
    inputs.to.assert_called_once_with("cpu")
    assert model.generate.call_args.kwargs["do_sample"] is False
    assert model.generate.call_args.kwargs["max_new_tokens"] == 160
    model.generate.return_value.__getitem__.assert_called_once_with((0, slice(3, None)))


def test_local_planner_rejects_schema():
    planner = LocalPlanner(Mock(), Mock(), max_new_tokens=20)
    assert planner.max_new_tokens == 20
    with pytest.raises(ValueError, match="somente texto"):
        planner.complete("tarefa", response_model=object)


def test_local_planner_rejects_empty_answer():
    inputs = Mock()
    inputs.to.return_value = {"input_ids": SimpleNamespace(shape=(1, 3))}
    tokenizer = Mock()
    tokenizer.return_value = inputs
    tokenizer.decode.return_value = " "
    with pytest.raises(RuntimeError, match="vazia"):
        LocalPlanner(Mock(), tokenizer).complete("tarefa")
