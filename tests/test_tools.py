import pytest

from minicode.tools import ProjectTools


def test_project_tools_reads_writes_and_lists_files(tmp_path):
    tools = ProjectTools(tmp_path)
    tools.write_file("src/example.py", "answer = 42\n")

    assert tools.read_file("src/example.py") == "answer = 42\n"
    assert "src/example.py" in tools.list_files()


def test_project_tools_rejects_paths_outside_project(tmp_path):
    tools = ProjectTools(tmp_path / "project")

    with pytest.raises(ValueError):
        tools.write_file("../outside.txt", "unsafe")


def test_project_tools_reports_when_project_cannot_be_created(tmp_path):
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("file", encoding="utf-8")

    with pytest.raises(ValueError, match="Escolha uma pasta existente"):
        ProjectTools(parent_file / "snake")


def test_project_tools_protects_environment_files(tmp_path):
    tools = ProjectTools(tmp_path)
    (tmp_path / ".env").write_text("API_KEY=secret", encoding="utf-8")

    assert ".env" not in tools.list_files()
    with pytest.raises(ValueError, match="protegidos"):
        tools.read_file(".env")


def test_project_tools_runs_pytest(tmp_path):
    tools = ProjectTools(tmp_path)
    tools.write_file("test_example.py", "def test_answer():\n    assert 6 * 7 == 42\n")

    result = tools.run_tests()

    assert result.returncode == 0

