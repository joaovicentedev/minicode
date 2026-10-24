# MiniCode

O MiniCode recebe uma tarefa em linguagem natural, usa um modelo de linguagem para propor alterações em um projeto e verifica o resultado com `pytest`. O programa controla o fluxo e limita as ações executadas no sistema de arquivos.

## Preparação e execução

Requisitos: Python 3.11 a 3.13, [`uv`](https://docs.astral.sh/uv/) e `pytest` com as dependências de teste do projeto-alvo.

```sh
make setup
```

Esse comando instala as dependências e cria `.env` a partir de `.env.example` se o arquivo ainda não existir. A configuração usa `MINICODE_API_KEY`, `MINICODE_BASE_URL` e `MINICODE_MODEL` no `.env` ou no ambiente. A chave deve permanecer fora do controle de versão.

Uma tarefa pode ser executada com a raiz do projeto-alvo informada explicitamente:

```sh
make run PROJECT=./projects/exemplo TASK="Adicione uma rota /health"
```

O equivalente sem `make` é:

```sh
uv run minicode --project ./projects/exemplo "Adicione uma rota /health"
```

O MiniCode pode criar a pasta do projeto e subpastas dentro dela. Se `--project` for omitido, usa o diretório atual. Se a tarefa for omitida, solicita o texto no terminal. O padrão é de duas tentativas no total; `--max-attempts 3` ajusta esse limite. [USO.md](USO.md) contém mais exemplos e detalhes.

## Arquitetura

O fluxo separa a orquestração do modelo e das operações locais. `LanguageModel` é a porta de geração de texto; `OpenAIChatModel` é o adaptador para endpoints de chat compatíveis com a API OpenAI. O modelo retorna texto e propostas de arquivos. O programa decide quando ler, gravar e testar.

| Componente | Responsabilidade |
| --- | --- |
| `src/minicode/cli/` | Recebe argumentos, configura o modelo e inicia a execução. |
| `src/minicode/agent/` | Controla estados, prompts, tentativas, propostas e reparos. |
| `src/minicode/llm/` | Define a porta `LanguageModel` e o adaptador `OpenAIChatModel`. |
| `src/minicode/tools/` | Restringe o acesso a arquivos e executa `pytest -q` no projeto-alvo. |
| `src/minicode/trace.py` | Persiste documentos, eventos, contadores e o resultado de cada execução. |
| `src/minicode/evaluation.py` | Executa casos isolados e mede soluções com testes de aceitação externos. |
| `src/minicode/spec/` | Reserva espaço para uma representação estruturada da especificação; atualmente ela é texto produzido pelo modelo. |
| `tests/` | Verifica o comportamento do MiniCode. |

O agente depende da porta `LanguageModel`; a entrada da aplicação seleciona o adaptador. As ferramentas locais são chamadas pelo agente e concentram as operações sobre o projeto-alvo. O modelo não recebe acesso direto a elas nem a um shell arbitrário.

## Fluxo do agente

1. O agente recebe a tarefa e lê até 20 arquivos de texto compatíveis, com limite aproximado de 24 mil caracteres e prioridade para os testes existentes.
2. Solicita ao modelo uma **especificação** com objetivo e critérios de aceitação verificáveis.
3. Usa a especificação para solicitar um **plano numerado**.
4. Envia tarefa, especificação, plano e contexto ao modelo para propor arquivos em JSON.
5. Valida a resposta e os caminhos, grava os arquivos e executa `pytest -q` na raiz do projeto-alvo.
6. Se os testes passarem, pede ao modelo uma revisão dos critérios de aceitação antes de concluir. Uma rejeição inicia reparo, se houver tentativas restantes.
7. Se os testes falharem, a saída de erro, a tarefa original, os testes visíveis e os arquivos propostos retornam ao modelo para uma nova tentativa. A especificação e o plano anteriores não são reutilizados nesse pedido.

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

## Restrições, segurança e reparo

Algumas regras são aplicadas pelo código, além das instruções enviadas ao modelo: a implementação ocorre após especificação e plano; `DONE` só é atribuído quando `pytest` retorna código 0 e a revisão de aceitação aprova; as tentativas são limitadas; e caminhos inválidos são rejeitados antes da gravação. O JSON dos arquivos é validado com Pydantic. O adaptador solicita um JSON Schema ao endpoint quando compatível e, caso o endpoint rejeite esse formato, valida a resposta recebida localmente.

As leituras e escritas ficam restritas à raiz informada em `--project`. Caminhos que saem dela e arquivos sensíveis, como `.env`, chaves `.pem`/`.key` e itens em `.git`, `.aws` ou `.ssh`, são recusados. O modelo não pode escolher um comando de shell; a única execução de verificação é `pytest -q`. Essas restrições não constituem um sandbox de sistema operacional: os testes rodam no ambiente do processo e podem produzir efeitos colaterais. Como não há backup automático, o `git diff` do projeto-alvo deve ser revisado após a execução.

Se os testes falharem, o agente monta um novo pedido de reparo com a tarefa original, a saída de erro, os testes visíveis e o conteúdo atual dos arquivos propostos. A spec e o plano anteriores não são reutilizados nessa etapa, pois podem conter interpretações equivocadas. Os pedidos de implementação e reparo incluem lembretes gerais de Python, como a relação entre `bool` e `int`, para ajudar na revisão de tipos e condições quando aplicável. O padrão de duas tentativas permite uma proposta inicial e um reparo. Sem testes coletados ou sem `pytest`, o agente termina como `UNVERIFIED` e não inicia um reparo sem falha concreta. Estados diferentes de `DONE` produzem código de saída 1.

O MiniCode pode criar ou editar arquivos de outras linguagens, mas o contexto automático inclui apenas `.py`, `.md`, `.toml`, `.yaml`, `.yml`, `.json` e `.txt`, e a verificação automática usa somente `pytest`. Cada proposta substitui o conteúdo integral dos arquivos indicados.

## Terminal e histórico

O comando individual mostra os turnos do modelo com etapa, duração e tamanho da resposta; estados; tentativas; nomes dos arquivos gravados; código de saída do pytest; resultado final dos testes; e estado final. **O conteúdo da especificação e do plano não é exibido no terminal.** Quando ocorre reparo, a primeira saída de erro também não é impressa integralmente; ela fica no histórico. A saída final dos testes é exibida ao encerrar a execução.

| Etapa | Visibilidade no terminal |
| --- | --- |
| Tarefa | Aparece no comando digitado ou na entrada interativa; não é repetida pelo agente. |
| Especificação e plano | Aparecem como etapas concluídas, sem o texto integral. |
| Alteração de código | Aparecem os caminhos dos arquivos gravados, sem o conteúdo. |
| Execução e testes | Aparecem o início do pytest e seu código de saída; a saída final é impressa ao término. |
| Erro e correção | Aparecem o estado `REPAIRING`, a nova tentativa e os novos arquivos; o erro intermediário completo fica no histórico. |
| Resultado | Aparecem a mensagem final e o estado `DONE`, `FAILED` ou `UNVERIFIED`. |

Cada execução cria `<projeto-alvo>/.minicode/runs/<id>/`:

| Arquivo | Conteúdo |
| --- | --- |
| `specification.md` | Especificação completa. |
| `plan.md` | Plano completo. |
| `actions.jsonl` | Estados, ferramentas, arquivos alterados, testes, saídas de erro e revisão de aceitação. |
| `state.json` | Tarefa, resultado, estado final e contadores de tentativas, chamadas ao modelo e testes. |

O histórico fica fora do contexto enviado ao modelo e é protegido contra alterações propostas por ele. O prompt completo e o conteúdo integral das respostas do modelo não são gravados. A saída dos testes pode conter dados exibidos pelo projeto-alvo.

## Avaliação

O diretório [evaluation/cases](evaluation/cases) contém seis tarefas isoladas: implementação de função, correção de bug, modificação de API, criação de testes, validação de dados e pequena refatoração. Os testes visíveis ficam em `project/tests/`: o agente os lê como contexto e executa `pytest -q` após cada proposta. Durante a avaliação, os testes visíveis já existentes são somente leitura; o agente pode criar testes novos quando a tarefa pedir. Os testes de aceitação ficam em `checks/`, fora do projeto entregue ao agente.

```sh
make evaluate
```

Esse comando usa o modelo configurado em `.env` e grava `evaluation/results/<data>/run.json`, além das cópias modificadas e seus históricos. Ao terminar, mostra o caminho da execução. A medição das soluções ocorre em um processo separado:

```sh
make grade RUN=evaluation/results/<data>
```

Os casos de `run` e `grade` são processados em paralelo (quatro por padrão); `--workers N` ajusta esse limite na CLI `minicode-eval`. Os resultados permanecem ordenados pelo nome do caso. A avaliação reduz a saída do terminal a avisos, erros, métricas e caminhos dos relatórios; cada caso conserva seu histórico.

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
