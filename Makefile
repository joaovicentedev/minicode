.PHONY: help setup sandbox run test lint check evaluate grade train

PROJECT ?= .
TASK ?=
UV ?= uv

help:
	@echo "Alvos: setup, sandbox, run, test, lint, check, evaluate, grade, train"
	@echo 'Exemplo: make run PROJECT=./projects/snake TASK="Crie o jogo da cobrinha"'

setup:
	$(UV) sync
	@test -f .env || cp .env.example .env
	$(MAKE) sandbox

sandbox:
	docker build -f Dockerfile.sandbox -t minicode-pytest:py313 .

run:
	$(UV) run minicode --project "$(PROJECT)" $(if $(TASK),"$(TASK)")

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .

check: test lint

evaluate:
	$(UV) run minicode-eval run $(if $(CASE),--case "$(CASE)")

grade:
	@test -n "$(RUN)"
	$(UV) run minicode-eval grade --run "$(RUN)" $(if $(CASE),--case "$(CASE)")

# Usa o ambiente preparado sem uv sync remover as dependências do notebook.
train:
	mkdir -p notebooks/outputs .cache/tmp .cache/pip .cache/jupyter
	PATH="$(CURDIR)/.venv/bin:$$PATH" TMPDIR="$(CURDIR)/.cache/tmp" PIP_CACHE_DIR="$(CURDIR)/.cache/pip" MPLCONFIGDIR="$(CURDIR)/.cache/matplotlib" HF_HOME="$(CURDIR)/.cache/huggingface" JUPYTER_RUNTIME_DIR="$(CURDIR)/.cache/jupyter" .venv/bin/jupyter nbconvert --to notebook --execute notebooks/train.ipynb --output train.executed.ipynb --output-dir notebooks/outputs --ExecutePreprocessor.timeout=-1 --ExecutePreprocessor.kernel_name=python3
