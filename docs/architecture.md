# Arquitetura inicial

O harness controla o agente; o modelo só recebe prompts e retorna propostas.

- `agent/`: máquina de estados, orquestração, limites e ciclo de reparo.
- `llm/`: porta `LanguageModel` e adaptador compatível com a API OpenAI do modelo da disciplina.
- `tools/`: operações limitadas sobre arquivos e execução fixa de pytest no projeto-alvo.
- `spec/`: espaço para evolução da especificação estruturada e critérios de aceitação.
- `cli/`: entrada do usuário e configuração do projeto-alvo.
- `tests/`: testes automatizados do próprio MiniCode.

Fluxo: `RECEIVED → SPECIFIED → PLANNED → IMPLEMENTING → VERIFYING → DONE`, com `REPAIRING` após falhas verificáveis, `FAILED` quando esgotado o limite de tentativas e `UNVERIFIED` quando pytest não encontra testes ou não está disponível. Um resultado sem testes não é tratado como falha de implementação e não dispara um reparo automático. O caminho informado em `--project` é a raiz de trabalho; o modelo pode criar subpastas dentro dela, e as ferramentas recusam caminhos externos.

As credenciais e o endpoint são lidos de `.env`/ambiente. O `.env` não deve ser versionado. A primeira versão permite somente `pytest -q` como comando; o subprocesso tem timeout e os caminhos de escrita são limitados ao projeto. Isso é uma barreira básica, não um sandbox de sistema operacional.

`trace.py` persiste cada execução em `<projeto>/.minicode/runs/<id>/`. O agente registra estados e chamadas de ferramentas no arquivo de eventos; spec, plano e estado resumido ficam em arquivos próprios. `ProjectTools` exclui `.minicode` da leitura e da escrita propostas pelo modelo. Em `evaluation.py`, `run_cases` executa o agente em cópias com testes visíveis em `tests/`; `grade_cases` é uma etapa separada que roda os testes externos de `checks/` e produz `report.json` sem alterar as cópias.
