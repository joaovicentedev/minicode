# MiniCode

Agente de programação com LLM e harness verificável, desenvolvido para o Trabalho Prático de Redes Neurais.

## Preparação

Requisitos: Python 3.11–3.13 e [`uv`](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env
```

Preencha `.env` com endpoint, nome do modelo e credencial fornecidos pelo professor. Não versione `.env` nem compartilhe a chave. Também é possível fornecer essas variáveis diretamente no ambiente.

## Uso

Veja o guia detalhado em [`USO.md`](USO.md).

Com as variáveis do modelo configuradas em `.env`, rode no projeto que deseja modificar:

```sh
uv run minicode --project /caminho/do/projeto "Adicione uma rota /health"
```

O projeto precisa ter `pytest` disponível. O MiniCode solicita especificação e plano, propõe os arquivos em JSON, grava-os dentro do projeto e roda `pytest -q`. Em caso de falha, envia o erro para uma tentativa de reparo (duas tentativas por padrão). O estado final é exibido no terminal.

O harness oferece leitura/escrita de arquivos e execução fixa de pytest, sem shell arbitrário. Escritas que escapem do diretório do projeto são recusadas; pytest tem timeout de 120 segundos. Essa proteção limita o escopo das operações, mas não é isolamento forte contra código malicioso executado pelos próprios testes.

## Estrutura

O código principal fica em `src/minicode/`, separado em `agent`, `llm`, `tools`, `spec` e `cli`. A arquitetura está em [`docs/architecture.md`](docs/architecture.md). O cliente OpenAI é um adaptador atrás da porta `LanguageModel`; o harness controla as ações no projeto-alvo.

## Desenvolvimento

```sh
uv run pytest
uv run ruff check .
```
