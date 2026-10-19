"""Porta e adaptador OpenAI para o endpoint da disciplina."""

import logging
import os
from typing import Protocol

import httpx
from dotenv import load_dotenv
from openai import APIStatusError, OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LanguageModel(Protocol):
    """Porta para geração de texto."""

    def complete(
        self, prompt: str, *, response_model: type[BaseModel] | None = None
    ) -> str: ...


class OpenAIChatModel:
    """Adaptador de chat compatível com a API OpenAI."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        http_client: httpx.Client | None = None,
    ):
        self.client = OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)
        self.model = model
        self._supports_json_schema: bool | None = None

    def complete(self, prompt: str, *, response_model: type[BaseModel] | None = None) -> str:
        request = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if response_model is not None and self._supports_json_schema is not False:
            request["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "minicode_response",
                    "strict": True,
                    "schema": response_model.model_json_schema(),
                },
            }
        try:
            response = self.client.chat.completions.create(**request)
            if response_model is not None:
                self._supports_json_schema = "response_format" in request
        except APIStatusError as error:
            unsupported_format = error.status_code in {400, 422} and any(
                marker in str(error).lower()
                for marker in (
                    "response_format",
                    "json_schema",
                    "structured output",
                    "extra inputs",
                )
            )
            if "response_format" not in request or not unsupported_format:
                raise
            logger.warning(
                "Endpoint recusou response_format JSON Schema; repetindo sem schema: %s",
                error,
            )
            request.pop("response_format")
            self._supports_json_schema = False
            response = self.client.chat.completions.create(**request)
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("O modelo retornou uma resposta vazia")
        return content

    @classmethod
    def from_environment(cls) -> "OpenAIChatModel":
        """Carrega credenciais de ambiente ou do arquivo .env."""
        load_dotenv()
        base_url = os.getenv("MINICODE_BASE_URL", "https://llm.liaufms.org/v1/qwen2-5-14b-instruct-awq")
        api_key = os.getenv("MINICODE_API_KEY")
        model = os.getenv("MINICODE_MODEL", "Qwen/Qwen2.5-14B-Instruct-AWQ")
        if not api_key:
            raise ValueError("Defina MINICODE_API_KEY no ambiente ou em .env")
        return cls(base_url=base_url, api_key=api_key, model=model)
