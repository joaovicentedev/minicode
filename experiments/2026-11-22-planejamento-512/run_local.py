"""Executar da raiz com .venv-inference/bin/python; modos base ou lora."""

import json
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForMultimodalLM, AutoProcessor

from minicode.evaluation import grade_cases, run_cases
from minicode.llm import OpenAIChatModel
from minicode.llm.local_planner import LocalPlanner

mode = sys.argv[1]
assert mode in {"base", "lora"}
torch.set_grad_enabled(False)
torch.set_num_threads(4)
root = Path(__file__).resolve().parent
model_id = "Qwen/Qwen3.5-0.8B"
revision = "2fc06364715b967f1860aea9cf38778875588b17"
processor = AutoProcessor.from_pretrained(model_id, revision=revision, local_files_only=True)
model = AutoModelForMultimodalLM.from_pretrained(
    model_id, dtype=torch.float32, revision=revision, local_files_only=True
)
if mode == "lora":
    model = PeftModel.from_pretrained(model, "notebooks/minicode-plan-lora")
model.eval()
(root / f"{mode}-config.json").write_text(
    json.dumps(
        {
            "model": model_id,
            "revision": revision,
            "adapter": "notebooks/minicode-plan-lora" if mode == "lora" else None,
            "device": "cpu",
            "dtype": "float32",
            "max_new_tokens": 512,
            "do_sample": False,
            "workers": 1,
            "max_attempts": 2,
        },
        indent=2,
    )
)
run_cases(
    OpenAIChatModel.from_environment(),
    Path("evaluation/cases"),
    root / mode,
    workers=1,
    planning_model=LocalPlanner(model, processor.tokenizer, max_new_tokens=512),
)
print(json.dumps(grade_cases(Path("evaluation/cases"), root / mode), indent=2))
