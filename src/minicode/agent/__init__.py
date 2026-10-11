"""Orquestração do fluxo spec, plano, implementação e verificação."""

import json
import logging
from enum import StrEnum
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from minicode.llm import LanguageModel
from minicode.tools import ProjectTools

logger = logging.getLogger(__name__)


class FileChange(BaseModel):
    """Alteração de um arquivo proposta pelo modelo."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(description="Caminho relativo ao diretório do projeto")
    content: str = Field(description="Conteúdo integral do arquivo")


class FileChanges(BaseModel):
    """Resposta estruturada com os arquivos a criar ou substituir."""

    model_config = ConfigDict(extra="forbid")

    files: list[FileChange] = Field(min_length=1)


class State(StrEnum):
    RECEIVED = "RECEIVED"
    SPECIFIED = "SPECIFIED"
    PLANNED = "PLANNED"
    IMPLEMENTING = "IMPLEMENTING"
    VERIFYING = "VERIFYING"
    REPAIRING = "REPAIRING"
    DONE = "DONE"
    FAILED = "FAILED"


class Agent:
    """Executa uma tarefa em projeto com número limitado de reparos."""

    def __init__(self, model: LanguageModel, project: Path, max_attempts: int = 2):
        if max_attempts < 1:
            raise ValueError("max_attempts deve ser pelo menos 1")
        self.model = model
        self.tools = ProjectTools(project)
        self.max_attempts = max_attempts
        self.state = State.RECEIVED
        self._turn = 0

    def run(self, task: str) -> str:
        """Executa tarefa e retorna o resultado da verificação."""
        if not task.strip():
            raise ValueError("A tarefa não pode ser vazia")
        context = self._project_context()
        logger.info("Tarefa recebida; lendo contexto do projeto %s", self.tools.root)
        spec = self._complete_turn(
            "especificação",
            "Produza uma especificação concisa, com objetivo e critérios de aceitação. "
            f"Não implemente ainda. Tarefa: {task}\n\nContexto do projeto:\n{context}"
        )
        self.state = State.SPECIFIED
        logger.info("Estado: %s", self.state.value)
        logger.info("Especificação produzida:\n%s", spec)
        plan = self._complete_turn("plano", f"Especificação:\n{spec}\n\nCrie um plano numerado.")
        self.state = State.PLANNED
        logger.info("Estado: %s", self.state.value)
        logger.info("Plano produzido:\n%s", plan)
        self.state = State.IMPLEMENTING
        logger.info("Estado: %s", self.state.value)
        prompt = self._implementation_prompt(task, spec, plan, context)
        feedback = ""
        for attempt in range(self.max_attempts):
            logger.info("Tentativa de implementação %d/%d", attempt + 1, self.max_attempts)
            answer = self._complete_turn("implementação/reparo", prompt + feedback, FileChanges)
            try:
                changes = self._parse_files(answer)
            except ValueError as error:
                logger.warning("Turno de implementação não passou na validação: %s", error)
                if attempt + 1 == self.max_attempts:
                    self.state = State.FAILED
                    logger.info("Estado final: %s", self.state.value)
                    return str(error)
                self.state = State.REPAIRING
                logger.info("Estado: %s", self.state.value)
                feedback = (
                    "\n\nSua resposta anterior não correspondeu ao schema. "
                    "Retorne somente um JSON válido com a propriedade files, contendo "
                    "objetos path e content. Sem markdown ou explicações."
                )
                continue
            for change in changes.files:
                self.tools.write_file(change.path, change.content)
            logger.info("Arquivos gravados: %s", ", ".join(change.path for change in changes.files))
            self.state = State.VERIFYING
            logger.info("Estado: %s; executando pytest -q", self.state.value)
            result = self.tools.run_tests()
            logger.info("pytest terminou com código %d", result.returncode)
            if result.returncode == 0:
                self.state = State.DONE
                logger.info("Estado final: %s", self.state.value)
                return result.stdout or "Testes concluídos com sucesso."
            if attempt + 1 < self.max_attempts:
                self.state = State.REPAIRING
                logger.info("Estado: %s", self.state.value)
                feedback = f"\n\nOs testes falharam. Corrija a implementação.\n{result.stdout}\n{result.stderr}"
        self.state = State.FAILED
        logger.info("Estado final: %s", self.state.value)
        return f"Falha após {self.max_attempts} tentativa(s).\n{result.stdout}\n{result.stderr}"

    def _complete_turn(
        self,
        stage: str,
        prompt: str,
        response_model: type[BaseModel] | None = None,
    ) -> str:
        """Registra metadados da chamada ao modelo sem despejar o prompt no log."""
        self._turn += 1
        started = perf_counter()
        logger.info("Turno LLM %d (%s): enviando %d caracteres", self._turn, stage, len(prompt))
        try:
            response = self.model.complete(prompt, response_model=response_model)
        except Exception:
            logger.exception("Turno LLM %d (%s) falhou", self._turn, stage)
            raise
        elapsed = perf_counter() - started
        logger.info(
            "Turno LLM %d (%s): resposta com %d caracteres em %.2fs",
            self._turn,
            stage,
            len(response),
            elapsed,
        )
        return response

    @staticmethod
    def _implementation_prompt(task: str, spec: str, plan: str, context: str = "") -> str:
        return (
            "Implemente a tarefa no projeto. Retorne somente um objeto JSON no formato "
            '{"files": [{"path": "caminho/relativo", "content": "conteúdo integral"}]}. '
            "Inclua arquivos de teste quando adequado.\n"
            f"Tarefa: {task}\nEspecificação:\n{spec}\nPlano:\n{plan}\n"
            f"Contexto do projeto:\n{context}\n"
        )

    def _project_context(self) -> str:
        """Lê uma amostra limitada de arquivos-fonte para contextualizar o modelo."""
        supported = {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".txt"}
        chunks = []
        budget = 24_000
        for relative_path in self.tools.list_files():
            path = Path(relative_path)
            if path.suffix not in supported:
                continue
            try:
                content = self.tools.read_file(relative_path)
            except (OSError, UnicodeDecodeError, ValueError):
                continue
            excerpt = content[: min(len(content), 4_000, budget)]
            if not excerpt:
                continue
            chunks.append(f"--- {relative_path} ---\n{excerpt}")
            budget -= len(excerpt)
            if budget <= 0 or len(chunks) >= 20:
                break
        return "\n\n".join(chunks) if chunks else "(Nenhum arquivo de texto compatível encontrado.)"

    @staticmethod
    def _parse_files(answer: str) -> FileChanges:
        """Valida os arquivos propostos com o schema Pydantic."""
        try:
            try:
                return FileChanges.model_validate_json(answer)
            except ValidationError:
                start = answer.find("{")
                end = answer.rfind("}")
                if start < 0 or end <= start:
                    raise
                return FileChanges.model_validate_json(answer[start : end + 1])
        except (ValidationError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(
                "Resposta inválida: esperado JSON conforme o schema de arquivos. "
                "Confira se o endpoint aceita response_format JSON Schema."
            ) from error
