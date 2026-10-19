"""Interface de linha de comando do MiniCode."""

import argparse
import logging
from pathlib import Path

from minicode.agent import Agent, State
from minicode.llm import OpenAIChatModel


def main() -> None:
    """Lê a tarefa e executa o MiniCode no projeto escolhido."""
    parser = argparse.ArgumentParser(description="Agente de programação MiniCode")
    parser.add_argument("task", nargs="?", help="Tarefa em linguagem natural")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Projeto alvo")
    parser.add_argument("--max-attempts", type=int, default=2, help="Tentativas incluindo reparos")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    task = args.task or input("Tarefa> ").strip()
    try:
        agent = Agent(OpenAIChatModel.from_environment(), args.project, args.max_attempts)
        print(agent.run(task))
        print(f"Estado final: {agent.state.value}")
        if agent.state is not State.DONE:
            parser.exit(1)
    except (ValueError, RuntimeError) as error:
        parser.exit(1, f"minicode: {error}\n")
