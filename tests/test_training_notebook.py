"""Exercita o controle do treino sem carregar modelos ou depender de GPU."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest


@pytest.mark.parametrize("validation_values, expected_epoch, expected_saves", [
    ([3.0, 2.0, 2.0, 1.0, 1.5, 1.8, 1.9, 2.0, 2.1, 2.2], 4, 3),
    ([1.0] * 10, 1, 1),
    ([float("nan")] * 10, None, 0),
])
def test_training_saves_only_improvements_and_restores_best(
    tmp_path, validation_values, expected_epoch, expected_saves,
):
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "notebooks/train.ipynb").read_text()
    )
    source = next(
        "".join(cell["source"]) for cell in notebook["cells"]
        if "EPOCHS = 10" in "".join(cell["source"])
        and cell["cell_type"] == "code"
    )
    model = Mock(peft_config=None)
    model.parameters.return_value = [SimpleNamespace(requires_grad=True)]
    losses = []
    for value in validation_values:
        losses.extend([
            SimpleNamespace(loss=Mock(item=Mock(return_value=0.2))),
            SimpleNamespace(loss=Mock(item=Mock(return_value=value))),
        ])
    model.side_effect = losses
    optimizer = Mock()
    torch = SimpleNamespace(
        optim=SimpleNamespace(AdamW=Mock(return_value=optimizer)),
        no_grad=MagicMock(), cuda=SimpleNamespace(empty_cache=Mock()),
    )
    saved_weights = {"adapter": "best saved weights"}
    loader = Mock(return_value=saved_weights)
    restore = Mock()
    namespace = {
        "model": model, "torch": torch, "Path": Mock(return_value=tmp_path),
        "LoraConfig": Mock(), "get_peft_model": Mock(return_value=model),
        "processor": Mock(), "encoded_train": ["train"],
        "encoded_validation": ["validation"], "batch": Mock(return_value={}),
        "json": json, "load_peft_weights": loader,
        "set_peft_model_state_dict": restore,
    }
    if expected_epoch is None:
        with pytest.raises(RuntimeError, match="Loss não finita"):
            exec(compile(source, "training_cell", "exec"), namespace)
        assert model.save_pretrained.call_count == 0
        loader.assert_not_called()
        return
    exec(compile(source, "training_cell", "exec"), namespace)
    assert len(namespace["train_loss"]) == len(namespace["validation_loss"]) == 10
    assert namespace["best_epoch"] == expected_epoch
    assert model.save_pretrained.call_count == expected_saves
    for call in model.save_pretrained.call_args_list:
        assert call.args == (tmp_path,)
        assert call.kwargs == {"safe_serialization": True}
    history = json.loads((tmp_path / "training_history.json").read_text())
    assert history["best_epoch"] == expected_epoch
    assert history["epochs_completed"] == 10
    loader.assert_called_once_with(str(tmp_path), device="cpu")
    restore.assert_called_once_with(model, saved_weights)
    assert "optimizer" not in namespace
    assert "loss" not in namespace
    assert "best_adapter" not in namespace
    torch.cuda.empty_cache.assert_called_once()


def test_training_rejects_reexecution_with_existing_adapter():
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "notebooks/train.ipynb").read_text()
    )
    source = next(
        "".join(cell["source"]) for cell in notebook["cells"]
        if cell["cell_type"] == "code" and "EPOCHS = 10" in "".join(cell["source"])
    )
    namespace = {"model": SimpleNamespace(peft_config={"default": "existing"})}
    with pytest.raises(RuntimeError, match="já contém LoRA"):
        exec(compile(source, "training_cell", "exec"), namespace)
