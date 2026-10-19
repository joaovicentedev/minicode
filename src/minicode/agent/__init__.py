"""Orquestração do fluxo spec, plano, implementação e verificação."""

import json
import logging
from enum import StrEnum
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from minicode.llm import LanguageModel
from minicode.tools import ProjectTools
from minicode.trace import RunTrace

logger = logging.getLogger(__name__)

PYTHON_REMINDERS = (
    "Se implementar em Python, confira estas peculiaridades quando forem relevantes:\n"
    "- bool é subtipo de int; isinstance(True, int) é verdadeiro.\n"
    "- Use is para None; == compara valores, is compara identidade.\n"
    "- Listas e dicionários vazios são falsos em condições, mas não são None.\n"
    "- Argumentos padrão mutáveis podem compartilhar estado entre chamadas.\n"
    "- Confira os limites dos intervalos e o tipo da exceção exigida.\n"
)


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
    UNVERIFIED = "UNVERIFIED"


class Agent:
    """Executa uma tarefa em projeto com número limitado de reparos."""

    def __init__(
        self,
        model: LanguageModel,
        project: Path,
        max_attempts: int = 2,
        read_only_paths: set[str] | None = None,
    ):
        if max_attempts < 1:
            raise ValueError("max_attempts deve ser pelo menos 1")
        self.model = model
        self.tools = ProjectTools(project, read_only_paths=read_only_paths)
        self.max_attempts = max_attempts
        self.state = State.RECEIVED
        self._turn = 0
        self.trace: RunTrace | None = None

    def run(self, task: str) -> str:
        """Executa tarefa e retorna o resultado da verificação."""
        if not task.strip():
            raise ValueError("A tarefa não pode ser vazia")
        self._turn = 0
        self.state = State.RECEIVED
        self.trace = RunTrace(self.tools.root, task)
        try:
            result = self._run(task)
        except Exception as error:
            self._transition(State.FAILED)
            self.trace.event("error", type=type(error).__name__, message=str(error))
            self.trace.finish(str(error))
            raise
        self.trace.finish(result)
        return result

    def _transition(self, state: State) -> None:
        """Atualiza o estado em memória e no histórico."""
        self.state = state
        self.trace.event("state", status=state.value)

    def _run(self, task: str) -> str:
        """Executa as etapas obrigatórias da tarefa."""
        context = self._project_context()
        logger.info("Tarefa recebida; lendo contexto do projeto %s", self.tools.root)
        spec = self._complete_turn(
            "especificação",
            "Produza uma especificação concisa, sem adicionar funcionalidades não pedidas, "
            "com objetivo e critérios de aceitação verificáveis. Liste separadamente todas as "
            "restrições explícitas do pedido, inclusive tipos, exceções e limites. "
            "Não inclua código nem uma solução pronta. "
            f"Não implemente ainda. Tarefa: {task}\n\nContexto do projeto:\n{context}"
        )
        self.trace.document("specification", spec)
        self._transition(State.SPECIFIED)
        logger.info("Estado: %s", self.state.value)
        logger.info("Especificação produzida:\n%s", spec)
        plan = self._complete_turn(
            "plano",
            f"Tarefa original:\n{task}\n\nEspecificação:\n{spec}\n\n"
            "Crie um plano numerado e enxuto. Preserve todos os requisitos explícitos "
            "da tarefa e considere os testes existentes antes de propor novos arquivos. "
            "Descreva apenas os passos; não inclua código pronto.",
        )
        self.trace.document("plan", plan)
        self._transition(State.PLANNED)
        logger.info("Estado: %s", self.state.value)
        logger.info("Plano produzido:\n%s", plan)
        self._transition(State.IMPLEMENTING)
        logger.info("Estado: %s", self.state.value)
        prompt = self._implementation_prompt(task, spec, plan, context)
        if self.tools.read_only_paths:
            prompt += "\nArquivos existentes somente leitura: " + ", ".join(
                sorted(self.tools.read_only_paths)
            )
        feedback = ""
        for attempt in range(self.max_attempts):
            self.trace.event("attempt", number=attempt + 1)
            logger.info("Tentativa de implementação %d/%d", attempt + 1, self.max_attempts)
            answer = self._complete_turn("implementação/reparo", feedback or prompt, FileChanges)
            try:
                changes = self._parse_files(answer)
                for change in changes.files:
                    self.tools.validate_write_path(change.path)
                    self.trace.event("tool", name="validate_write_path", path=change.path)
            except ValueError as error:
                self.trace.event("error", type="validation", message=str(error))
                logger.warning("Turno de implementação não passou na validação: %s", error)
                if attempt + 1 == self.max_attempts:
                    self._transition(State.FAILED)
                    logger.info("Estado final: %s", self.state.value)
                    return str(error)
                self._transition(State.REPAIRING)
                logger.info("Estado: %s", self.state.value)
                feedback = prompt + (
                    f"\n\nA proposta anterior foi rejeitada: {error}. "
                    "Corrija os caminhos e retorne somente um JSON válido com a propriedade "
                    "files e objetos path/content. Os caminhos são relativos à raiz do projeto "
                    "informada em --project; não repita o nome da pasta do projeto. Sem markdown."
                )
                continue
            for change in changes.files:
                self.tools.write_file(change.path, change.content)
                self.trace.event("write", path=change.path)
            logger.info("Arquivos gravados: %s", ", ".join(change.path for change in changes.files))
            self._transition(State.VERIFYING)
            logger.info("Estado: %s; executando pytest -q", self.state.value)
            result = self.tools.run_tests()
            self.trace.event(
                "test",
                command="pytest -q",
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
            logger.info("pytest terminou com código %s", result.returncode)
            if result.returncode == 5:
                self._transition(State.UNVERIFIED)
                logger.warning(
                    "pytest não coletou testes; a implementação não pode ser declarada válida"
                )
                logger.info("Estado final: %s", self.state.value)
                return (
                    "Implementação gravada, mas não validada: "
                    "pytest não encontrou testes no projeto. "
                    "O MiniCode não fez reparo automático porque não recebeu um teste que falhou."
                )
            if result.returncode is None:
                self._transition(State.UNVERIFIED)
                logger.warning("pytest não está disponível no ambiente")
                logger.info("Estado final: %s", self.state.value)
                return (
                    "Implementação gravada, mas não validada: "
                    "pytest não está disponível no ambiente."
                )
            if result.returncode == 0:
                self._transition(State.DONE)
                logger.info("Estado final: %s", self.state.value)
                return result.stdout or "Testes concluídos com sucesso."
            if attempt + 1 < self.max_attempts:
                self._transition(State.REPAIRING)
                logger.info("Estado: %s", self.state.value)
                feedback = self._repair_feedback(
                    task,
                    result.stdout + "\n" + result.stderr,
                    [change.path for change in changes.files],
                )
        self._transition(State.FAILED)
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
        self.trace.event("llm", number=self._turn, stage=stage)
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

    def _repair_feedback(self, task: str, failure: str, paths: list[str]) -> str:
        """Inclui falha e arquivos atuais no contexto da próxima tentativa."""
        excerpts = []
        remaining = 12_000
        for relative_path in paths:
            try:
                content = self.tools.read_file(relative_path)
                if self.trace is not None:
                    self.trace.event("tool", name="read_file", path=relative_path)
            except (OSError, UnicodeDecodeError, ValueError):
                continue
            excerpt = content[:remaining]
            excerpts.append(f"--- {relative_path} ---\n{excerpt}")
            remaining -= len(excerpt)
            if remaining <= 0:
                break
        current_files = "\n\n".join(excerpts) or "(sem arquivos para reler)"
        visible_tests = []
        test_budget = 8_000
        paths = self.tools.list_files()
        if self.trace is not None:
            self.trace.event("tool", name="list_files", count=len(paths))
        for relative_path in paths:
            path = Path(relative_path)
            if not path.name.startswith("test_") or path.suffix != ".py":
                continue
            try:
                content = self.tools.read_file(relative_path)
                if self.trace is not None:
                    self.trace.event("tool", name="read_file", path=relative_path)
            except (OSError, UnicodeDecodeError, ValueError):
                continue
            excerpt = content[:test_budget]
            visible_tests.append(f"--- {relative_path} ---\n{excerpt}")
            test_budget -= len(excerpt)
            if test_budget <= 0:
                break
        tests = "\n\n".join(visible_tests) or "(sem testes visíveis)"
        read_only = ", ".join(sorted(self.tools.read_only_paths)) or "(nenhum)"
        return (
            "A verificação encontrou falhas. Antes de responder, compare a entrada que falhou, "
            "o resultado esperado e o comportamento do código atual. Corrija a causa da falha; "
            "não repita uma solução com o mesmo comportamento e preserve os testes existentes, "
            "salvo quando a tarefa pedir sua alteração. Mantenha os caminhos existentes quando "
            "possível e nunca escreva fora da raiz. Responda somente com JSON no formato "
            '{"files": [{"path": "caminho/relativo", "content": "conteúdo integral"}]}.\n'
            f"{PYTHON_REMINDERS}\n"
            f"Tarefa original e suas restrições:\n{task}\n\n"
            f"Arquivos somente leitura:\n{read_only}\n\n"
            f"Saída dos testes:\n{failure}\n\nTestes visíveis:\n{tests}\n\n"
            f"Arquivos atuais:\n{current_files}"
        )

    @staticmethod
    def _implementation_prompt(task: str, spec: str, plan: str, context: str = "") -> str:
        return (
            "Implemente somente o que a tarefa pede. O diretório informado em --project é a raiz "
            "de trabalho do projeto. Crie nessa pasta os arquivos e subpastas necessários, "
            "usando uma estrutura apropriada à linguagem e à tarefa (por exemplo src/, tests/ "
            "ou assets/ quando fizer sentido). Todos os caminhos são relativos a essa raiz e "
            "nunca podem sair dela. Não envolva todo o projeto em outra pasta sem necessidade. "
            "Crie apenas os arquivos necessários, sem versões duplicadas ou alternativas. "
            "Leia os testes existentes no contexto e use-os como referência. "
            "A tarefa original prevalece quando a especificação ou o plano omitirem uma restrição. "
            "Ao adicionar testes, use a pasta tests/ e nomes que não dupliquem outros testes. "
            "Retorne somente um objeto JSON no formato "
            '{"files": [{"path": "caminho/relativo", "content": "conteúdo integral"}]}. '
            "Inclua arquivos de teste quando adequado.\n"
            f"{PYTHON_REMINDERS}"
            f"Tarefa: {task}\nEspecificação:\n{spec}\nPlano:\n{plan}\n"
            f"Contexto do projeto:\n{context}\n"
        )

    def _project_context(self) -> str:
        """Lê uma amostra limitada de arquivos-fonte para contextualizar o modelo."""
        supported = {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".txt"}
        chunks = []
        budget = 24_000
        paths = self.tools.list_files()
        paths.sort(key=lambda path: (not Path(path).name.startswith("test_"), path))
        if self.trace is not None:
            self.trace.event("tool", name="list_files", count=len(paths))
        for relative_path in paths:
            path = Path(relative_path)
            if path.suffix not in supported:
                continue
            try:
                content = self.tools.read_file(relative_path)
                if self.trace is not None:
                    self.trace.event("tool", name="read_file", path=relative_path)
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
