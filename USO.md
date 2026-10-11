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

1. O MiniCode coleta até 20 arquivos de texto compatíveis, com limite total aproximado de 24 mil caracteres, para contextualizar a solicitação. Arquivos `.env`, chaves comuns e diretórios `.git`, `.aws` e `.ssh` são excluídos das ferramentas de leitura.
2. O modelo gera uma especificação com critérios de aceitação.
3. O modelo gera um plano numerado.
4. O modelo propõe o conteúdo integral dos arquivos em JSON.
5. O MiniCode valida os caminhos, grava os arquivos e executa `pytest -q` no projeto-alvo.
6. Se os testes falharem e houver tentativas restantes, o erro é enviado ao modelo para uma nova proposta.
7. O terminal mostra a saída dos testes e o estado final (`DONE` ou `FAILED`).

O comando registra no terminal os turnos do modelo (etapa, duração e tamanho da resposta), a especificação e o plano gerados, os arquivos gravados, as transições de estado e o resultado do pytest. O prompt completo, que inclui trechos do projeto, não é registrado.

Na etapa de implementação, o MiniCode envia um JSON Schema gerado a partir do modelo Pydantic `FileChanges` usando o parâmetro OpenAI-compatible `response_format`. A compatibilidade depende da implementação do servidor por trás do endpoint. Se o servidor rejeitar especificamente o formato estruturado, o adaptador registra um aviso, repete sem o schema e valida o JSON recebido localmente com Pydantic; se a resposta ainda estiver malformada, o agente pede uma correção antes de encerrar.

## Ferramentas e limites atuais

- As operações de leitura e escrita ficam restritas ao diretório do projeto-alvo.
- O modelo não recebe um shell arbitrário: o único comando disponível para verificação é `pytest -q`.
- A execução dos testes tem limite de 120 segundos.
- Arquivos `.env`, chaves `.pem`/`.key`, nomes contendo `secret`, `credential` ou `token`, e pastas `.git`, `.aws` e `.ssh` são protegidos contra leitura e escrita pelas ferramentas.
- O MiniCode não cria um backup automático das alterações. Revise o `git diff` do projeto-alvo antes de aceitar o resultado.
- A proteção de caminhos e comandos é uma barreira básica, não um sandbox de sistema operacional. Testes executam código no mesmo ambiente do processo e podem ter efeitos colaterais.
- Os testes do projeto-alvo precisam estar instalados no ambiente usado para iniciar o MiniCode e suas dependências devem estar disponíveis.

## Desenvolvimento do MiniCode

Na raiz deste repositório:

```sh
uv run pytest
uv run ruff check .
```

Veja [`README.md`](README.md) para o resumo do projeto e [`docs/architecture.md`](docs/architecture.md) para a separação entre agente, porta do modelo e ferramentas.
