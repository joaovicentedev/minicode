# Como usar o MiniCode

O MiniCode recebe uma tarefa em linguagem natural, consulta o modelo configurado, propõe alterações para um projeto e executa os testes desse projeto. Esta documentação descreve o fluxo implementado atualmente.

## Requisitos

- Python 3.11, 3.12 ou 3.13
- [`uv`](https://docs.astral.sh/uv/)
- A chave, o endpoint e o identificador de modelo fornecidos pela disciplina
- `pytest` e as dependências necessárias para testar o projeto-alvo

## Preparar o MiniCode

Na pasta deste repositório, instale as dependências e crie o arquivo de configuração local:

```sh
uv sync
cp .env.example .env
```

Edite `.env` e preencha.

## Executar uma tarefa

Passe o caminho do projeto-alvo e descreva a tarefa entre aspas:

```sh
uv run minicode --project /caminho/para/meu-projeto "Adicione uma rota /health que retorne status ok"
```

O MiniCode cria a pasta-alvo e seus diretórios pais quando seu usuário tem permissão de escrita. No macOS, use um caminho dentro da sua pasta de usuário, por exemplo:

```sh
uv run minicode --project "$HOME/Projects/snake" "Crie o jogo da cobrinha"
```

O caminho passado em `--project` é a raiz de trabalho do projeto. O agente pode criar arquivos diretamente nela e organizar o código em subpastas, como `src/`, `tests/` ou `assets/`, conforme a tarefa. Todas as alterações ficam dentro desse diretório. Por exemplo, `--project ./projects/snake` permite criar `./projects/snake/src/...`.

O caminho `/projects/snake` começa na raiz do disco (`/`), e normalmente não é gravável pelo usuário no macOS. Se não for possível criar/acessar o caminho informado, o MiniCode mostra uma mensagem com essa explicação.

Se `--project` for omitido, o diretório atual será usado como projeto-alvo:

```sh
cd /caminho/para/meu-projeto
uv run --project /caminho/para/minicode minicode "Corrija a validação de email"
```

Também é possível iniciar sem passar a tarefa; o programa solicitará o texto no terminal:

```sh
uv run minicode --project /caminho/para/meu-projeto
```

Para ajustar o limite de tentativas, use `--max-attempts`. O padrão é duas tentativas no total, contando a tentativa inicial:

```sh
uv run minicode --project /caminho/para/meu-projeto --max-attempts 3 "Corrija os testes de UserService"
```

## O que acontece durante a execução

1. O MiniCode coleta até 20 arquivos de texto compatíveis, priorizando os testes existentes, com limite total aproximado de 24 mil caracteres para contextualizar a solicitação. Arquivos `.env`, chaves comuns e diretórios `.git`, `.aws` e `.ssh` são excluídos das ferramentas de leitura.
2. O modelo gera uma especificação com critérios de aceitação.
3. O modelo gera um plano numerado.
4. O modelo propõe o conteúdo integral dos arquivos em JSON.
5. O MiniCode valida todos os caminhos antes de gravar os arquivos e executa `pytest -q` no projeto-alvo.
6. Se os testes passarem, o modelo revisa a implementação diante da tarefa e dos critérios de aceitação. Uma rejeição impede `DONE` e inicia reparo quando ainda há tentativas.
7. Se os testes falharem e houver tentativas restantes, o reparo recebe a tarefa original, o erro, os testes visíveis e o conteúdo atual dos arquivos propostos. A spec e o plano anteriores ficam de fora desse pedido para evitar repetir uma interpretação equivocada.
8. Se pytest não encontrar testes (código 5) ou não estiver instalado, o resultado será `UNVERIFIED`; o agente não pedirá um reparo sem uma falha concreta.
9. O terminal mostra a saída da verificação e o estado final (`DONE`, `FAILED` ou `UNVERIFIED`). Os estados diferentes de `DONE` fazem o comando sair com código 1.

O comando individual registra no terminal os turnos do modelo (etapa, duração e tamanho da resposta), os arquivos gravados, as transições de estado e o resultado do pytest. A especificação e o plano ficam no histórico da execução. O prompt completo, que inclui trechos do projeto, não é registrado.

Cada execução salva um histórico em `<projeto-alvo>/.minicode/runs/<id>/`: `specification.md`, `plan.md`, `actions.jsonl` e `state.json`. O diretório é excluído do contexto enviado ao modelo e das ferramentas de escrita. `state.json` contém a tarefa, o estado, o resultado e os contadores de tentativas, chamadas ao modelo e testes; `actions.jsonl` registra as ferramentas, arquivos e erros. A saída dos testes também é registrada ali e pode conter dados exibidos pelos testes.

Na etapa de implementação, o MiniCode envia um JSON Schema gerado a partir do modelo Pydantic `FileChanges` usando o parâmetro OpenAI-compatible `response_format`. A compatibilidade depende da implementação do servidor por trás do endpoint. Se o servidor rejeitar especificamente o formato estruturado, o adaptador registra um aviso, repete sem o schema e valida o JSON recebido localmente com Pydantic; se a resposta ainda estiver malformada, o agente pede uma correção antes de encerrar.

## Ferramentas e limites atuais

- As operações de leitura e escrita ficam restritas ao diretório do projeto-alvo.
- O modelo não recebe um shell arbitrário: o único comando disponível para verificação é `pytest -q`.
- O MiniCode pode editar arquivos de diferentes linguagens, mas a verificação automática atual é somente `pytest`. Projetos sem testes Python terminam como `UNVERIFIED`; isso não significa que a implementação esteja correta nem que esteja incorreta.
- Os caminhos propostos são relativos à raiz informada por `--project`. O agente pode criar subpastas adequadas dentro dela, mas não pode gravar fora dela.
- A execução dos testes tem limite de 120 segundos.
- Arquivos `.env`, chaves `.pem`/`.key`, nomes contendo `secret`, `credential` ou `token`, e pastas `.git`, `.aws` e `.ssh` são protegidos contra leitura e escrita pelas ferramentas.
- O MiniCode não cria um backup automático das alterações. Revise o `git diff` do projeto-alvo antes de aceitar o resultado.
- A revisão de critérios é feita por modelo e pode errar. Testes de aceitação independentes continuam necessários para medir a correção da solução.
- A proteção de caminhos e comandos é uma barreira básica, não um sandbox de sistema operacional. Testes executam código no mesmo ambiente do processo e podem ter efeitos colaterais.
- Os testes do projeto-alvo precisam estar instalados no ambiente usado para iniciar o MiniCode e suas dependências devem estar disponíveis.

## Desenvolvimento do MiniCode

Na raiz deste repositório:

```sh
uv run pytest
uv run ruff check .
```

O `Makefile` oferece atalhos para os mesmos comandos:

```sh
make setup
make run PROJECT=./projects/snake TASK="Crie o jogo da cobrinha"
make test
make lint
make check
make evaluate
```

`make setup` instala as dependências e cria `.env` a partir de `.env.example` somente se o arquivo ainda não existir; depois, preencha a configuração. Em `make run`, `PROJECT` usa o diretório atual por padrão e, sem `TASK`, o programa solicita a tarefa no terminal. `make check` executa testes e lint.

`make evaluate` roda seis tarefas em cópias isoladas e salva `evaluation/results/<data>/run.json`. Os testes visíveis estão em `tests/` de cada projeto e os arquivos já existentes nessa pasta são somente leitura para o agente durante a avaliação. Após a execução, use `make grade RUN=evaluation/results/<data>` para rodar os testes externos de `checks/`, sem chamar o agente. O relatório `report.json` inclui `TaskSuccessRate`, `FirstAttemptSuccess`, `AverageIterations` e `AverageLLMCalls`. Veja o [README.md](README.md) para as definições dessas métricas.

As etapas `run` e `grade` executam até quatro casos em paralelo por padrão, mantendo os resultados na ordem dos casos. Use `--workers 1` para execução sequencial ou outro número positivo para ajustar a concorrência. O modelo usado por `run` precisa aceitar chamadas simultâneas. O terminal mostra apenas avisos, erros e os caminhos dos relatórios; spec, plano e eventos detalhados continuam no histórico de cada caso.

Para rodar apenas um caso, use `make evaluate CASE=05_validation`. O comando `grade` detecta automaticamente os casos presentes na pasta da execução. Também é possível usar `uv run minicode-eval run --case 05_validation --output evaluation/results/ensaio-validation` seguido de `uv run minicode-eval grade --run evaluation/results/ensaio-validation`.

Veja [`README.md`](README.md) para a arquitetura, o fluxo completo, os limites e a avaliação.
