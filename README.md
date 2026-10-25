# MiniCode

Apresentação da Parte 1: [slides HTML](show/apresentacao.html) e [roteiro de demonstração](show/ROTEIRO.md).

O MiniCode recebe uma tarefa em linguagem natural, usa um modelo de linguagem para propor alterações em um projeto e verifica o resultado com `pytest`. O programa controla o fluxo e limita as ações executadas no sistema de arquivos.

## Preparação e execução

Requisitos: Python 3.11 a 3.13, [`uv`](https://docs.astral.sh/uv/) e Docker ativo. O container leve usa Python 3.13 e `pytest`.

```sh
make setup
```

Esse comando instala as dependências, cria `.env` a partir de `.env.example` se necessário e constrói a imagem `minicode-pytest:py313`. Para reconstruir só a imagem, use `make sandbox`. A configuração usa `MINICODE_API_KEY`, `MINICODE_BASE_URL` e `MINICODE_MODEL` no `.env` ou no ambiente. A chave deve permanecer fora do controle de versão.

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
| `src/minicode/tools/` | Restringe o acesso a arquivos e executa `pytest -q` em container Docker. |
| `src/minicode/trace.py` | Persiste documentos, eventos, contadores e o resultado de cada execução. |
| `src/minicode/evaluation.py` | Executa casos isolados e mede soluções com testes de aceitação externos. |
| `src/minicode/spec/` | Reserva espaço para uma representação estruturada da especificação; atualmente ela é texto produzido pelo modelo. |
| `tests/` | Verifica o comportamento do MiniCode. |

O agente depende da porta `LanguageModel`; a entrada da aplicação seleciona o adaptador. As ferramentas locais são chamadas pelo agente e concentram as operações sobre o projeto-alvo. O modelo não recebe acesso direto a elas nem a um shell arbitrário.

## Fluxo do agente

1. O agente recebe a tarefa e lê até 20 arquivos de texto compatíveis, com limite aproximado de 24 mil caracteres e prioridade para os testes existentes.
2. Solicita ao modelo uma **especificação** do comportamento observável, com restrições explícitas e critérios de aceitação verificáveis, sem código nem decisões de estrutura.
3. Usa a especificação e o contexto do projeto para solicitar um **plano numerado** de ações futuras, sem repetir os critérios da spec.
4. Envia tarefa, especificação, plano e contexto ao modelo para propor arquivos em JSON.
5. Valida a resposta e os caminhos, grava os arquivos e executa `pytest -q` em uma cópia filtrada do projeto dentro do container.
6. Se os testes passarem, pede ao modelo uma revisão dos critérios de aceitação antes de concluir. Uma rejeição inicia reparo, se houver tentativas restantes.
7. Se os testes falharem, a saída de erro, a tarefa original, os testes visíveis e os arquivos propostos retornam ao modelo para uma nova tentativa. Em erros de importação, o feedback inclui orientação sobre o caminho dos módulos para `pytest -q`. A especificação e o plano anteriores não são reutilizados nesse pedido.

Essa ordem aplica Spec-Driven Development: a implementação só é solicitada depois da spec e do plano. A spec atual é texto livre; o programa não valida automaticamente a qualidade dos critérios de aceitação. A revisão posterior é uma avaliação do modelo e não substitui testes de aceitação independentes.

Os estados registrados são `RECEIVED → SPECIFIED → PLANNED → IMPLEMENTING → VERIFYING → DONE`. As transições permitidas são validadas pelo programa. Uma falha nos testes ou na revisão dos critérios pode levar a `REPAIRING`; o limite de tentativas leva a `FAILED`. Quando `pytest` não encontra testes ou não está disponível, o resultado é `UNVERIFIED`.

## Ferramentas implementadas

| Ferramenta | Ação permitida |
| --- | --- |
| `list_files` | Lista arquivos do projeto, excluindo diretórios e nomes protegidos. |
| `read_file` | Lê um arquivo permitido dentro do projeto. |
| `write_file` | Grava o conteúdo integral de um arquivo e cria suas subpastas. |
| `run_tests` | Executa somente `pytest -q` no container, com limite de 120 segundos; inclui a raiz do projeto e `src/` no caminho de importação. |

O agente também usa `validate_write_path` para verificar todos os caminhos propostos antes de iniciar a gravação. As chamadas a essas ferramentas são feitas pelo programa; não há shell arbitrário disponível ao modelo.

## Restrições, segurança e reparo

Algumas regras são aplicadas pelo código, além das instruções enviadas ao modelo: a implementação ocorre após especificação e plano; `DONE` só é atribuído quando `pytest` retorna código 0 e a revisão de aceitação aprova; as tentativas são limitadas; e caminhos inválidos são rejeitados antes da gravação. O JSON dos arquivos é validado com Pydantic. O adaptador solicita um JSON Schema ao endpoint quando compatível e, caso o endpoint rejeite esse formato, valida a resposta recebida localmente.

As leituras e escritas ficam restritas à raiz informada em `--project`. Caminhos que saem dela e arquivos sensíveis, como `.env`, chaves `.pem`/`.key` e itens em `.git`, `.aws` ou `.ssh`, são recusados. O modelo não pode escolher um comando de shell; a única execução de verificação é `pytest -q`. Para cada teste, o harness copia apenas os arquivos permitidos para uma pasta temporária e a monta como somente leitura no container. O container fica sem rede, sem capacidades Linux adicionais, com sistema de arquivos somente leitura, usuário sem privilégios e limites de CPU, memória, processos e tempo. Testes de aceitação externos usam o mesmo sandbox. Se Docker ou a imagem não estiverem disponíveis, a execução fica `UNVERIFIED`; não há fallback para executar código do projeto no host. O container reduz o acesso do código de teste ao host, mas depende da segurança do Docker. Como não há backup automático dos arquivos propostos, o `git diff` do projeto-alvo deve ser revisado após a execução.

Se os testes falharem, o agente monta um novo pedido de reparo com a tarefa original, a saída de erro, os testes visíveis e o conteúdo atual dos arquivos propostos. A spec e o plano anteriores não são reutilizados nessa etapa, pois podem conter interpretações equivocadas. O container inclui a raiz do projeto e `src/` no `PYTHONPATH` usado por `pytest -q`; os prompts orientam a conferir os nomes dos imports, recalcular valores esperados a partir da tarefa e corrigir testes criados pelo próprio agente quando necessário. Na revisão de aceitação, o modelo deve apontar uma divergência concreta para rejeitar, com entrada e valores quando aplicável, e manter a justificativa coerente com `accepted`. Essa revisão ainda não substitui testes de aceitação externos. O padrão de duas tentativas permite uma proposta inicial e um reparo. Sem testes coletados ou sem Docker disponível, o agente termina como `UNVERIFIED` e não inicia um reparo sem falha concreta. Estados diferentes de `DONE` produzem código de saída 1.

O MiniCode pode criar ou editar arquivos de outras linguagens, mas o contexto automático inclui apenas `.py`, `.md`, `.toml`, `.yaml`, `.yml`, `.json` e `.txt`, e a verificação automática usa somente `pytest` no Python 3.13 da imagem. Dependências adicionais do projeto-alvo não são instaladas automaticamente no container. Cada proposta substitui o conteúdo integral dos arquivos indicados.

## Terminal e histórico

O comando individual mostra os turnos do modelo com etapa, duração, tamanho e conteúdo integral da resposta; estados; tentativas; conteúdo dos arquivos gravados; código de saída e saída completa do pytest em cada tentativa; e estado final. Os prompts enviados ao modelo continuam fora do log. A proposta de arquivos aparece como JSON retornado pelo modelo, inclusive em reparos.

| Etapa | Visibilidade no terminal |
| --- | --- |
| Tarefa | Aparece no comando digitado ou na entrada interativa; não é repetida pelo agente. |
| Especificação e plano | O texto integral das respostas aparece no terminal e fica salvo em arquivos separados no histórico. |
| Alteração de código | Aparecem o JSON proposto pelo modelo e o conteúdo de cada arquivo gravado. |
| Execução e testes | Aparecem o código de saída e a saída completa do pytest em cada tentativa. |
| Erro e correção | Aparecem o erro do teste, o estado `REPAIRING` e a nova proposta do modelo. |
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

O comando `grade` executa somente os testes de `checks/` contra cada cópia no sandbox Docker, sem chamar o agente e sem alterar seus arquivos. Ele grava `report.json` no diretório da execução; se Docker estiver indisponível, encerra com erro sem publicar métricas. Também é possível escolher um nome de saída com `uv run minicode-eval run --output evaluation/results/ensaio-2` e depois executar `uv run minicode-eval grade --run evaluation/results/ensaio-2`. `TaskSuccessRate` é a fração dos casos avaliados em que o agente termina em `DONE` e os testes de aceitação passam. `FirstAttemptSuccess` é a fração concluída na primeira tentativa. `AverageIterations` e `AverageLLMCalls` são as médias de tentativas de implementação e chamadas ao modelo por caso. Os resultados dependem da execução real do endpoint configurado; os testes automatizados do MiniCode não substituem essa avaliação.

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
