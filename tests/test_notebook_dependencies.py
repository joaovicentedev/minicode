"""Verifica a preparação de kernels sem instalar pacotes no ambiente de testes."""

import ast
import json
import os
import subprocess
import tempfile
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.mark.parametrize("triton_available", [True, False])
def test_kernel_installation_preserves_runtime_and_checks_imports(triton_available):
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "notebooks/train.ipynb").read_text()
    )
    source = "".join(notebook["cells"][1]["source"])
    tree = ast.parse(source)
    tree.body = [node for node in tree.body if not isinstance(node, ast.Import | ast.ImportFrom)]
    runner = Mock()
    versions = Mock(side_effect=[
        "2.9.0+cu128", "3.5.0" if triton_available else PackageNotFoundError("triton"),
    ])
    # TemporaryDirectory grava as restrições em disco; o executor externo é injetado.
    temporary = Mock(wraps=tempfile.TemporaryDirectory)
    namespace = {
        "torch": SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True)),
        "os": os, "subprocess": SimpleNamespace(run=runner),
        "sys": SimpleNamespace(modules={}, executable="python-runtime"),
        "tempfile": SimpleNamespace(TemporaryDirectory=temporary),
        "Path": Path, "version": versions, "PackageNotFoundError": PackageNotFoundError,
    }
    exec(compile(tree, "dependency_cell", "exec"), namespace)
    assert namespace["constraints"] == (
        ["torch==2.9.0+cu128", "triton==3.5.0"] if triton_available else ["torch==2.9.0+cu128"]
    )
    assert runner.call_count == 4
    calls = runner.call_args_list
    assert "flash-linear-attention[cuda]" in calls[1].args[0]
    assert "--no-build-isolation" in calls[2].args[0]
    assert "causal-conv1d" in calls[2].args[0]
    for call in calls[:3]:
        command = call.args[0]
        assert command[:4] == ["python-runtime", "-m", "pip", "install"]
        assert "--constraint" in command
        assert call.kwargs["check"] is True
        assert call.kwargs["env"]["MAX_JOBS"] == "2"
    verification = calls[-1].args[0]
    assert verification[:2] == ["python-runtime", "-c"]
    assert "causal_conv1d_fn, causal_conv1d_update" in verification[2]
    assert "chunk_gated_delta_rule, fused_recurrent_gated_delta_rule" in verification[2]
    ast.parse(verification[2])
    assert not namespace["constraint_path"].exists()


def test_kernel_setup_rejects_already_imported_transformers():
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "notebooks/train.ipynb").read_text()
    )
    tree = ast.parse("".join(notebook["cells"][1]["source"]))
    tree.body = [node for node in tree.body if not isinstance(node, ast.Import | ast.ImportFrom)]
    runner = Mock()
    namespace = {
        "torch": SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True)),
        "sys": SimpleNamespace(modules={"transformers": object()}),
        "subprocess": SimpleNamespace(run=runner),
    }
    with pytest.raises(RuntimeError, match="sessão reiniciada"):
        exec(compile(tree, "dependency_cell", "exec"), namespace)
    runner.assert_not_called()


def test_kernel_installation_failure_stops_before_model_setup():
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "notebooks/train.ipynb").read_text()
    )
    tree = ast.parse("".join(notebook["cells"][1]["source"]))
    tree.body = [node for node in tree.body if not isinstance(node, ast.Import | ast.ImportFrom)]
    runner = Mock(side_effect=[None, subprocess.CalledProcessError(1, "pip")])
    namespace = {
        "torch": SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True)),
        "os": os, "subprocess": SimpleNamespace(run=runner),
        "sys": SimpleNamespace(modules={}, executable="python-runtime"),
        "tempfile": tempfile, "Path": Path, "version": Mock(return_value="1.0"),
        "PackageNotFoundError": PackageNotFoundError,
    }
    with pytest.raises(subprocess.CalledProcessError):
        exec(compile(tree, "dependency_cell", "exec"), namespace)
    assert runner.call_count == 2


def test_kernel_setup_rejects_missing_cuda_before_installation():
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "notebooks/train.ipynb").read_text()
    )
    tree = ast.parse("".join(notebook["cells"][1]["source"]))
    tree.body = [node for node in tree.body if not isinstance(node, ast.Import | ast.ImportFrom)]
    runner = Mock()
    namespace = {
        "torch": SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False)),
        "subprocess": SimpleNamespace(run=runner),
    }
    with pytest.raises(RuntimeError, match="GPU com CUDA indisponível"):
        exec(compile(tree, "dependency_cell", "exec"), namespace)
    runner.assert_not_called()


@pytest.mark.parametrize("directory", [".", "notebooks"])
def test_repository_setup_uses_existing_local_checkout(tmp_path, directory):
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    (tmp_path / "notebooks").mkdir()
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "notebooks/train.ipynb").read_text()
    )
    tree = ast.parse("".join(notebook["cells"][2]["source"]))
    start = next(
        i for i, node in enumerate(tree.body)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "REPO" for target in node.targets)
    )
    tree.body = tree.body[start:start + 3]
    path = Mock(side_effect=Path)
    path.cwd.return_value = tmp_path / directory
    runner = Mock()
    namespace = {"Path": path, "subprocess": SimpleNamespace(run=runner)}
    exec(compile(tree, "repository_cell", "exec"), namespace)
    assert namespace["REPO"] == tmp_path
    runner.assert_not_called()
