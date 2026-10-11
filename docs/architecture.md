# Arquitetura inicial

O harness controla o agente; o modelo só recebe prompts e retorna propostas.

- `agent/`: máquina de estados, orquestração, limites e ciclo de reparo.
- `llm/`: porta `LanguageModel` e adaptador compatível com a API OpenAI do modelo da disciplina.
- `tools/`: operações limitadas sobre arquivos e execução fixa de pytest no projeto-alvo.
- `spec/`: espaço para evolução da especificação estruturada e critérios de aceitação.
- `cli/`: entrada do usuário e configuração do projeto-alvo.
- `tests/`: testes automatizados do próprio MiniCode.

Fluxo previsto: `RECEIVED → SPECIFIED → PLANNED → IMPLEMENTING → VERIFYING → DONE`, com `REPAIRING` após falhas de verificação e `FAILED` quando esgotado o limite de tentativas. O programa validará as transições; o prompt sozinho não será a barreira.

As credenciais e o endpoint são lidos de `.env`/ambiente. O `.env` não deve ser versionado. A primeira versão permite somente `pytest -q` como comando; o subprocesso tem timeout e os caminhos de escrita são limitados ao projeto. Isso é uma barreira básica, não um sandbox de sistema operacional.
