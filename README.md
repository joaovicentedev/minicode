# MiniCode

Agente de programação com LLM e harness verificável, desenvolvido para o Trabalho Prático de Redes Neurais.

## Preparação

Requisitos: Python 3.11–3.13 e [`uv`](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env
```

Preencha `.env` com endpoint, nome do modelo e credencial fornecidos pelo professor. Não versione `.env` nem compartilhe a chave. Também é possível fornecer essas variáveis diretamente no ambiente.

## Estrutura

O código principal fica em `src/minicode/`, separado em `agent`, `llm`, `tools`, `spec` e `cli`. A arquitetura planejada está em [`docs/architecture.md`](docs/architecture.md). O primeiro foco de implementação é o agente e o harness; os diretórios de experimentos e treinamento estão preparados para a segunda etapa.

## Desenvolvimento

```sh
uv run pytest
uv run ruff check .
```
