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


def test_project_tools_validates_all_write_paths_before_writing(tmp_path):
    tools = ProjectTools(tmp_path)

    with pytest.raises(ValueError):
        tools.validate_write_path("../outside.txt")


def test_project_tools_keeps_existing_tests_read_only(tmp_path):
    test_file = tmp_path / "tests" / "test_feature.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_feature():\n    assert True\n", encoding="utf-8")
    tools = ProjectTools(tmp_path, read_only_paths={"tests/test_feature.py"})

    assert "assert True" in tools.read_file("tests/test_feature.py")
    with pytest.raises(ValueError, match="somente leitura"):
        tools.validate_write_path("tests/../tests/test_feature.py")
    with pytest.raises(ValueError, match="somente leitura"):
        tools.write_file("tests/test_feature.py", "assert False")
    assert "assert True" in test_file.read_text(encoding="utf-8")
    tools.write_file("tests/test_new.py", "def test_new():\n    assert True\n")
    assert (tmp_path / "tests" / "test_new.py").exists()


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


def test_project_tools_reports_empty_test_collection(tmp_path):
    tools = ProjectTools(tmp_path)
    result = tools.run_tests()

    assert result.returncode == 5

