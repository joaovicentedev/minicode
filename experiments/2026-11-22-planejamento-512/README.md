# Experimento final de planejamento

A [análise final](../../docs/analise-final.md) compara três condições:
Qwen2.5-14B em todos os turnos (`padrao`), Qwen3.5-0.8B no planejamento (`base`)
e o mesmo modelo com LoRA no planejamento (`lora`). Nas duas condições locais,
os demais turnos continuam no endpoint principal e o limite do plano é 512 tokens.

`base/`, `lora/` e `padrao/` contêm os projetos, históricos, `run.json` e
`report.json`. A referência `padrao` foi medida em uma execução independente,
com quatro workers e os limites próprios do servidor remoto. Base e LoRA usam
um worker. O manifesto registra configuração, revisões e hashes dos artefatos.

Para reproduzir as condições locais, copie `run_local.py` para uma pasta nova
e execute da raiz do projeto com Docker ativo e a imagem do sandbox preparada:

```sh
HF_HOME="$PWD/.cache/huggingface" .venv-inference/bin/python experiments/nova-execucao/run_local.py base
HF_HOME="$PWD/.cache/huggingface" .venv-inference/bin/python experiments/nova-execucao/run_local.py lora
```

Instale antes `notebooks/requirements-mac.txt` no ambiente de inferência e
configure o endpoint principal em `.env`. Os pesos precisam estar no cache local
e o adaptador em `notebooks/minicode-plan-lora/`. Os comandos também executam
os testes externos. Os diretórios de saída não podem existir antes da execução.

`finalize.py` recompõe `summary.json` a partir dos três relatórios disponíveis,
sem reexecutar modelos nem sobrescrever a análise final. Runs e históricos de
texto podem ser versionados. Pesos e pacotes que os contêm ficam fora do Git.
