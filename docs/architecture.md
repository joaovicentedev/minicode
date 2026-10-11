# Arquitetura inicial

A implementação será construída em torno de um harness que controla o agente, em vez de delegar as ações diretamente ao modelo.

- `agent/`: máquina de estados, orquestração, limites e ciclo de reparo.
- `llm/`: cliente compatível com a API do modelo fornecido na disciplina.
- `tools/`: operações limitadas sobre arquivos e execução de testes no projeto-alvo.
- `spec/`: especificação estruturada e critérios de aceitação.
- `cli/`: entrada do usuário e configuração do projeto-alvo.
- `tests/`: testes automatizados do próprio MiniCode.

Fluxo previsto: `RECEIVED → SPECIFIED → PLANNED → IMPLEMENTING → VERIFYING → DONE`, com `REPAIRING` após falhas de verificação e `FAILED` quando esgotado o limite de tentativas. O programa validará as transições; o prompt sozinho não será a barreira.

As credenciais e o endpoint serão lidos da configuração local (`.env`/ambiente). O `.env` não deve ser versionado.
