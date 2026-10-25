"""Ferramentas restritas ao diretório do projeto-alvo."""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    stdout: str
    stderr: str


class TestSandbox(Protocol):
    """Porta para executar testes sem expor o processo do agente ao projeto-alvo."""

    def run(self, project: Path, timeout: int, checks: Path | None = None) -> CommandResult: ...


class ProjectTools:
    """Acesso a arquivos e execução fixa de pytest dentro do projeto."""

    def __init__(
        self,
        root: Path,
        timeout: int = 120,
        read_only_paths: set[str] | None = None,
        sandbox: TestSandbox | None = None,
    ):
        self.root = root.resolve()
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise ValueError(
                f"Não foi possível criar ou acessar o projeto '{self.root}'. "
                "Escolha uma pasta existente ou um caminho onde seu usuário possa gravar."
            ) from error
        self.timeout = timeout
        self.read_only_paths = set(read_only_paths or ())
        self.sandbox = sandbox or DockerSandbox()

    def _resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if not candidate.is_relative_to(self.root):
            raise ValueError("Caminho fora do projeto não é permitido")
        relative = candidate.relative_to(self.root)
        if self._is_protected(relative) or ".minicode" in relative.parts:
            raise ValueError("Arquivos de configuração e credenciais são protegidos")
        return candidate

    @staticmethod
    def _is_protected(path: Path) -> bool:
        sensitive_name = any(
            token in path.name.lower() for token in ("secret", "credential", "token")
        )
        return (
            bool({".git", ".aws", ".ssh"}.intersection(path.parts))
            or path.name == ".env"
            or path.name.startswith(".env.")
            or path.name.endswith((".pem", ".key"))
            or sensitive_name
        )

    def list_files(self) -> list[str]:
        """Lista arquivos do projeto sem incluir diretórios ocultos ou venvs."""
        excluded = {".git", ".venv", ".minicode", "__pycache__", ".pytest_cache"}
        return sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
            and not excluded.intersection(path.relative_to(self.root).parts)
            and not self._is_protected(path.relative_to(self.root))
        )

    def read_file(self, relative_path: str) -> str:
        """Lê arquivo dentro do projeto."""
        return self._resolve(relative_path).read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> None:
        """Grava arquivo dentro do projeto e cria diretórios pais."""
        self.validate_write_path(relative_path)
        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def validate_write_path(self, relative_path: str) -> None:
        """Confirma que um caminho proposto é gravável pelo harness."""
        path = self._resolve(relative_path)
        if path.relative_to(self.root).as_posix() in self.read_only_paths:
            raise ValueError(f"Arquivo existente somente leitura: {relative_path}")

    def run_tests(self) -> CommandResult:
        """Executa pytest apenas por meio do sandbox configurado."""
        return self.sandbox.run(self.root, self.timeout)


class DockerSandbox:
    """Adaptador Docker para testes em uma cópia filtrada e somente leitura do projeto."""

    def __init__(self, docker: str = "docker", image: str = "minicode-pytest:py313"):
        self.docker = docker
        self.image = image

    def run(self, project: Path, timeout: int, checks: Path | None = None) -> CommandResult:
        """Executa pytest em container isolado, sem fallback para o host."""
        with TemporaryDirectory(prefix="minicode-sandbox-") as temporary:
            staged = Path(temporary)
            staged.chmod(0o755)
            tools = ProjectTools(project)
            for relative_path in tools.list_files():
                try:
                    source = tools._resolve(relative_path)
                except ValueError:
                    continue
                target = staged / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.parent.chmod(0o755)
                shutil.copyfile(source, target)
                target.chmod(0o644)

            name = f"minicode-test-{uuid4().hex[:12]}"
            command = [
                self.docker, "run", "--rm", "--pull=never", "--name", name,
                "--network=none", "--read-only", "--cap-drop=ALL",
                "--security-opt=no-new-privileges", "--pids-limit=128",
                "--memory=512m", "--cpus=1", "--user=65534:65534",
                "--tmpfs=/tmp:rw,nosuid,nodev,size=64m,mode=1777",
                "--mount", f"type=bind,src={staged},dst=/workspace,readonly",
                "--workdir=/workspace", "--env=HOME=/tmp",
                "--env=PYTHONDONTWRITEBYTECODE=1",
                "--env=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                "--env=PYTHONPATH=/workspace:/workspace/src",
            ]
            if checks is not None:
                command += [
                    "--mount", f"type=bind,src={checks.resolve()},dst=/checks,readonly"
                ]
            command += [self.image, "pytest", "-q", "-p", "no:cacheprovider"]
            if checks is not None:
                command.append("/checks")
            try:
                completed = subprocess.run(
                    command, capture_output=True, text=True, timeout=timeout + 10, check=False
                )
            except FileNotFoundError:
                return CommandResult(
                    None, "", "Docker não está instalado; instale e rode make sandbox"
                )
            except subprocess.TimeoutExpired as error:
                try:
                    subprocess.run(
                        [self.docker, "rm", "-f", name],
                        capture_output=True, text=True, timeout=10, check=False,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    pass
                stdout = (
                    error.stdout.decode()
                    if isinstance(error.stdout, bytes)
                    else (error.stdout or "")
                )
                stderr = (
                    error.stderr.decode()
                    if isinstance(error.stderr, bytes)
                    else (error.stderr or "")
                )
                return CommandResult(124, stdout, stderr + f"\npytest excedeu {timeout} segundos")
            if completed.returncode in {125, 126, 127}:
                detail = completed.stderr.strip() or "falha ao iniciar o container"
                return CommandResult(
                    None, completed.stdout,
                    f"Sandbox Docker indisponível: {detail}. Inicie Docker e rode make sandbox.",
                )
            return CommandResult(completed.returncode, completed.stdout, completed.stderr)
