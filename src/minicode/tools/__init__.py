"""Ferramentas restritas ao diretório do projeto-alvo."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    stdout: str
    stderr: str


class ProjectTools:
    """Acesso a arquivos e execução fixa de pytest dentro do projeto."""

    def __init__(
        self, root: Path, timeout: int = 120, read_only_paths: set[str] | None = None
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
        """Executa apenas pytest, com tempo máximo configurado."""
        try:
            completed = subprocess.run(
                ["pytest", "-q"],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
            return CommandResult(completed.returncode, completed.stdout, completed.stderr)
        except subprocess.TimeoutExpired as error:
            stdout = (
                error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
            )
            stderr = (
                error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
            )
            return CommandResult(124, stdout, stderr + f"\npytest excedeu {self.timeout} segundos")
        except FileNotFoundError:
            return CommandResult(None, "", "pytest não está disponível no ambiente")
