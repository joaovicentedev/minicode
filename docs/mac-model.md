# Levar o modelo para o Mac

O ZIP de transferência contém uma cópia do código, o modelo base em `models/Qwen3.5-0.8B/`, o adaptador em `notebooks/outputs/minicode-plan-lora/` e o notebook executado em `notebooks/outputs/train.executed.ipynb`. Os links do cache do Hugging Face são convertidos em arquivos reais no ZIP. O ambiente `.venv` do Linux, caches, credenciais e `.git` não fazem parte do pacote.

O adaptador corresponde à época 3, selecionada pela menor perda de validação (1,6207). O treinamento concluiu 10 épocas. No teste de 10 exemplos, a conformidade estrutural passou de 0% para 100%, e a aprovação conjunta dos critérios passou de 0% para 30%. Consulte `metrics.json`, `predictions.json` e `training_history.json` na pasta do adaptador. As métricas de conteúdo são aproximações lexicais e não comprovam correção semântica.

## Preparação

Extraia o ZIP e entre na pasta `minicode`. Recrie o ambiente para macOS; os binários do Linux não são portáveis. Com `uv` instalado:

```bash
uv venv --python 3.12
uv pip install --python .venv/bin/python -e . -r notebooks/requirements-mac.txt
```

A instalação das bibliotecas requer internet. Os pesos do modelo já estão no ZIP. As dependências propostas para macOS não foram executadas neste ambiente Linux; a disponibilidade dos wheels depende da arquitetura e da versão do macOS. O notebook de treinamento usa CUDA e deve continuar sendo executado na máquina NVIDIA.

## Carregar o adaptador para inferência

Execute este exemplo a partir da raiz da cópia extraída. Ele usa CPU e pesos sem quantização CUDA, como ponto de partida para verificar o carregamento no Mac:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForMultimodalLM, AutoProcessor

from minicode.planning_data import format_example, load_examples

base_path = Path('models/Qwen3.5-0.8B')
adapter_path = Path('notebooks/outputs/minicode-plan-lora')
processor = AutoProcessor.from_pretrained(base_path, local_files_only=True)
model = AutoModelForMultimodalLM.from_pretrained(
    base_path, dtype=torch.float32, local_files_only=True,
)
model = PeftModel.from_pretrained(model, adapter_path, local_files_only=True)
model.eval()
example = load_examples(Path('notebooks/data/test.jsonl'))[0]
prompt = format_example(example)['prompt']
text = processor.tokenizer.apply_chat_template(
    [{'role': 'user', 'content': prompt}],
    tokenize=False, add_generation_prompt=True, enable_thinking=False,
)
inputs = processor.tokenizer(text, return_tensors='pt')
with torch.no_grad():
    output = model.generate(
        **inputs, max_new_tokens=160, do_sample=False,
        pad_token_id=processor.tokenizer.eos_token_id,
    )
print(processor.tokenizer.decode(
    output[0, inputs['input_ids'].shape[1]:], skip_special_tokens=True,
))
PY
```

Sem os kernels CUDA, Transformers pode informar que está usando implementações alternativas. Esse caminho em CPU pode ser mais lento. Carregar o adaptador não cria um endpoint compatível com OpenAI; a integração com o agente exige um servidor de inferência separado.
