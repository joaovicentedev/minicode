.PHONY: help setup run test lint check evaluate grade

PROJECT ?= .
TASK ?=
UV ?= uv

help:
	@echo "Alvos: setup, run, test, lint, check, evaluate, grade"
	@echo 'Exemplo: make run PROJECT=./projects/snake TASK="Crie o jogo da cobrinha"'

setup:
	$(UV) sync
	@test -f .env || cp .env.example .env

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
