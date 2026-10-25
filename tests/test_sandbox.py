import json

from minicode.evaluation import run_acceptance
from minicode.tools import DockerSandbox


def test_docker_sandbox_stages_only_allowed_files_and_restricts_container(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("answer = 42\n", encoding="utf-8")
    (project / ".env").write_text("API_KEY=secret\n", encoding="utf-8")
    (project / ".minicode").mkdir()
    (project / ".minicode" / "state.json").write_text("{}", encoding="utf-8")
    (project / "outside.py").symlink_to(tmp_path / "outside.py")
    (tmp_path / "outside.py").write_text("secret = True\n", encoding="utf-8")
    checks = tmp_path / "checks"
    checks.mkdir()
    (checks / "test_acceptance.py").write_text("def test_ok(): assert True\n")
    docker = tmp_path / "fake-docker"
    docker.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        "args = sys.argv[1:]\n"
        "mount = args[args.index('--mount') + 1]\n"
        "root = pathlib.Path(mount.split('src=', 1)[1].split(',dst=', 1)[0])\n"
        "files = sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file())\n"
        "print(json.dumps({'args': args, 'files': files}))\n",
        encoding="utf-8",
    )
    docker.chmod(0o755)

    result = run_acceptance(project, checks, DockerSandbox(docker=str(docker)))

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["files"] == ["app.py"]
    args = data["args"]
    assert "--network=none" in args
    assert "--read-only" in args
    assert "--cap-drop=ALL" in args
    assert "--security-opt=no-new-privileges" in args
    assert "--user=65534:65534" in args
    assert "--pull=never" in args
    assert any("dst=/workspace,readonly" in part for part in args)
    assert any("dst=/checks,readonly" in part for part in args)
    assert args[-5:] == ["pytest", "-q", "-p", "no:cacheprovider", "/checks"]


def test_docker_sandbox_fails_closed_when_docker_is_missing(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "test_example.py").write_text("def test_ok(): assert True\n")

    result = DockerSandbox(docker=str(tmp_path / "missing-docker")).run(project, 2)

    assert result.returncode is None
    assert "Docker não está instalado" in result.stderr


def test_docker_sandbox_reports_daemon_failure(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    docker = tmp_path / "fake-docker"
    docker.write_text("#!/bin/sh\necho 'daemon unavailable' >&2\nexit 125\n")
    docker.chmod(0o755)

    result = DockerSandbox(docker=str(docker)).run(project, 2)

    assert result.returncode is None
    assert "daemon unavailable" in result.stderr
    assert "make sandbox" in result.stderr
