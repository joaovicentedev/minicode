# MiniCode

O MiniCode recebe uma tarefa em linguagem natural, usa um modelo de linguagem para propor alterações em um projeto e verifica o resultado com `pytest`. O programa controla o fluxo e limita as ações executadas no sistema de arquivos.

## Preparação e execução

Requisitos: Python 3.11 a 3.13, [`uv`](https://docs.astral.sh/uv/) e `pytest` com as dependências de teste do projeto-alvo.

```sh
make setup
```

Esse comando instala as dependências e cria `.env` a partir de `.env.example` se o arquivo ainda não existir. Configure `MINICODE_API_KEY`, `MINICODE_BASE_URL` e `MINICODE_MODEL` no `.env` ou no ambiente. Não versione nem compartilhe a chave.

Execute uma tarefa informando a raiz do projeto-alvo:

```sh
make run PROJECT=./projects/exemplo TASK="Adicione uma rota /health"
```

O equivalente sem `make` é:

```sh
uv run minicode --project ./projects/exemplo "Adicione uma rota /health"
```

O MiniCode pode criar a pasta do projeto e subpastas dentro dela. Se `--project` for omitido, usa o diretório atual. Se a tarefa for omitida, solicita o texto no terminal. O padrão é de duas tentativas no total; `--max-attempts 3` ajusta esse limite. Consulte [USO.md](USO.md) para mais exemplos e detalhes.

## Arquitetura

A organização segue a ideia de portas e adaptadores: `agent/` coordena a tarefa sem depender diretamente de uma API específica de modelo; a porta `LanguageModel`, em `llm/`, define a chamada ao modelo, e `OpenAIChatModel` adapta um endpoint compatível com OpenAI. `cli/` recebe argumentos e configura a execução. `tools/` implementa as operações locais controladas pelo programa. `tests/` verifica o comportamento do MiniCode. `spec/` está reservado para evolução da especificação; na versão atual, a spec é texto produzido pelo modelo.

O harness, formado pela orquestração do agente e pelas ferramentas locais, decide quando ler, gravar e testar. O modelo retorna texto e propostas de arquivos; ele não executa comandos diretamente. Veja também [docs/architecture.md](docs/architecture.md).

## Fluxo do agente e Spec-Driven Development

1. O agente recebe a tarefa e lê uma amostra limitada de arquivos do projeto.
2. Solicita ao modelo uma **especificação** com objetivo e critérios de aceitação verificáveis.
3. Usa a especificação para solicitar um **plano numerado**.
4. Envia tarefa, especificação, plano e contexto ao modelo para propor arquivos em JSON.
5. Valida a resposta e os caminhos, grava os arquivos e executa `pytest -q` na raiz do projeto-alvo.
6. Se os testes passarem, pede ao modelo uma revisão dos critérios de aceitação antes de concluir. Uma rejeição inicia reparo, se houver tentativas restantes.

Essa ordem aplica Spec-Driven Development: a implementação só é solicitada depois da spec e do plano. A spec atual é texto livre; o programa não valida automaticamente a qualidade dos critérios de aceitação. A revisão posterior é uma avaliação do modelo e não substitui testes de aceitação independentes.

Os estados registrados são `RECEIVED → SPECIFIED → PLANNED → IMPLEMENTING → VERIFYING → DONE`. As transições permitidas são validadas pelo programa. Uma falha nos testes ou na revisão dos critérios pode levar a `REPAIRING`; o limite de tentativas leva a `FAILED`. Quando `pytest` não encontra testes ou não está disponível, o resultado é `UNVERIFIED`.

## Ferramentas implementadas

| Ferramenta | Ação permitida |
| --- | --- |
| `list_files` | Lista arquivos do projeto, excluindo diretórios e nomes protegidos. |
| `read_file` | Lê um arquivo permitido dentro do projeto. |
| `write_file` | Grava o conteúdo integral de um arquivo e cria suas subpastas. |
| `run_tests` | Executa somente `pytest -q`, com limite de 120 segundos. |

O agente também usa `validate_write_path` para verificar todos os caminhos propostos antes de iniciar a gravação. As chamadas a essas ferramentas são feitas pelo programa; não há shell arbitrário disponível ao modelo.

## Agent Hardness, segurança e repair loop

Algumas regras são aplicadas pelo código, além das instruções enviadas ao modelo: a implementação ocorre após spec e plano; `DONE` só é atribuído quando `pytest` retorna código 0; as tentativas são limitadas; e caminhos inválidos são rejeitados antes da gravação. O JSON dos arquivos é validado com Pydantic. O adaptador solicita um JSON Schema ao endpoint quando compatível e, caso o endpoint rejeite esse formato, valida a resposta recebida localmente.

As leituras e escritas ficam restritas à raiz informada em `--project`. Caminhos que saem dela e arquivos sensíveis, como `.env`, chaves `.pem`/`.key` e itens em `.git`, `.aws` ou `.ssh`, são recusados. O modelo não pode escolher um comando de shell; a única execução de verificação é `pytest -q`. Essas restrições não constituem um sandbox de sistema operacional: os testes rodam no ambiente do processo e podem produzir efeitos colaterais. Revise o `git diff` do projeto-alvo após a execução, pois não há backup automático.

Se os testes falharem, o agente monta um novo pedido de reparo com a tarefa original, a saída de erro, os testes visíveis e o conteúdo atual dos arquivos propostos. A spec e o plano anteriores não são reutilizados nessa etapa, pois podem conter interpretações equivocadas. Os pedidos de implementação e reparo incluem lembretes gerais de Python, como a relação entre `bool` e `int`, para ajudar na revisão de tipos e condições quando aplicável. O padrão de duas tentativas permite uma proposta inicial e um reparo. Sem testes coletados ou sem `pytest`, o agente termina como `UNVERIFIED` e não inicia um reparo sem falha concreta. Estados diferentes de `DONE` produzem código de saída 1.

O comando individual registra no terminal os turnos do modelo, os arquivos gravados, os estados e o resultado dos testes. Cada execução também cria `.minicode/runs/<id>/` no projeto-alvo, com `specification.md`, `plan.md`, `actions.jsonl` e `state.json`. Esses arquivos guardam tarefa, spec, plano, ferramentas chamadas, arquivos alterados, testes, erros, tentativas, chamadas ao modelo e resultado. A pasta fica fora do contexto enviado ao modelo e é protegida contra alterações propostas por ele. O prompt completo e o conteúdo integral das respostas do modelo não são gravados nesse histórico.

## Avaliação da Parte 1

O diretório [evaluation/cases](evaluation/cases) contém seis tarefas isoladas: implementação de função, correção de bug, modificação de API, criação de testes, validação de dados e pequena refatoração. Os testes visíveis ficam em `project/tests/`: o agente os lê como contexto e executa `pytest -q` após cada proposta. Durante a avaliação, os testes visíveis já existentes são somente leitura; o agente pode criar testes novos quando a tarefa pedir. Os testes de aceitação ficam em `checks/`, fora do projeto entregue ao agente.

```sh
make evaluate
```

Esse comando usa o modelo configurado em `.env` e grava `evaluation/results/<data>/run.json`, além das cópias modificadas e seus históricos. Ao terminar, mostra o caminho da execução. Para medir as soluções depois, em um processo separado:

Os casos de `run` e `grade` são processados em paralelo (quatro por padrão); `--workers N` ajusta esse limite. Os resultados permanecem ordenados pelo nome do caso.

```sh
make grade RUN=evaluation/results/<data>
```

O comando `grade` executa somente os testes de `checks/` contra cada cópia, sem chamar o agente e sem alterar seus arquivos. Ele grava `report.json` no diretório da execução. Também é possível escolher um nome de saída com `uv run minicode-eval run --output evaluation/results/ensaio-2` e depois executar `uv run minicode-eval grade --run evaluation/results/ensaio-2`. `TaskSuccessRate` é a fração dos casos avaliados em que o agente termina em `DONE` e os testes de aceitação passam. `FirstAttemptSuccess` é a fração concluída na primeira tentativa. `AverageIterations` e `AverageLLMCalls` são as médias de tentativas de implementação e chamadas ao modelo por caso. Os resultados dependem da execução real do endpoint configurado; os testes automatizados do MiniCode não substituem essa avaliação.

Para repetir somente um caso, use `--case` no comando `run`. O comando `grade` detecta automaticamente quais casos estão na pasta da execução:

```sh
uv run minicode-eval run --case 05_validation --output evaluation/results/ensaio-validation
uv run minicode-eval grade --run evaluation/results/ensaio-validation
```

Também é possível usar `make evaluate CASE=05_validation` e depois `make grade RUN=<pasta-da-execução>`.

## Desenvolvimento

```sh
make check
```

Esse alvo executa `uv run pytest` e `uv run ruff check .`. Também é possível executá-los separadamente com `make test` e `make lint`.
