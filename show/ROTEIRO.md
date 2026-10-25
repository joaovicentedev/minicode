# Roteiro de apresentação do MiniCode

## Slides HTML da Parte 1

Abra [`apresentacao.html`](apresentacao.html) no navegador. Use as setas esquerda/direita (ou cima/baixo), Page Up/Page Down e Espaço para navegar. `Home` e `End` vão ao primeiro e ao último slide. O cronômetro no canto inferior direito começa ao abrir a página; `R` o reinicia. Os botões no rodapé também mudam os slides.

O slide de resultados usa os valores medidos em `evaluation/results/ensaio-8/report.json` (seis casos). Na apresentação, identifique essa execução e abra o relatório se for citar os números. Para uma demonstração nova, rode os comandos do slide com uma pasta de saída ainda inexistente e apresente os resultados dessa nova execução separadamente.

Para verificar a interação dos slides: `node --test show/slides.test.js`.

## Escopo e duração

O enunciado prevê duas entregas: **Parte 1 em 15 dias** e **Parte 2 em 30 dias**. Ele exige vídeo nas duas entregas, mas **não determina duração em minutos**. Este roteiro sugere **7 minutos para a Parte 1**. Ajuste o ritmo à duração solicitada fora do enunciado, se houver.

O vídeo da Parte 1 precisa mostrar uma execução completa: solicitação → especificação → plano → alteração de código → execução → erro, se ocorrer → correção → testes → resultado. Mostre apenas o que aconteceu de fato; um reparo só pode ser demonstrado se a execução produziu falha e nova tentativa.

O comando individual `uv run minicode` agora imprime cada resposta do modelo e a saída do pytest de cada tentativa. Para mostrar spec, plano, proposta de arquivos e revisão, acompanhe os blocos `Resposta LLM` no terminal. O comando `minicode-eval run` mantém a saída reduzida; nesse fluxo, abra `specification.md`, `plan.md` e `actions.jsonl` no histórico do caso.

## Antes de gravar

1. Abra o terminal na raiz do repositório. Confirme que Docker está ativo e execute `make sandbox`. Confirme que `.env` está configurado, sem exibir seu conteúdo nem a chave na gravação.
2. Execute `make check` e mantenha o resultado disponível para mostrar rapidamente.
3. Escolha o caso `05_validation`: ele começa com uma implementação incompleta e testes visíveis para inteiros, limites e valores booleanos.
4. Faça uma execução de ensaio com um caminho de saída novo. Guarde o caminho exibido pelo comando para abrir os arquivos do histórico durante a gravação.
5. Confira `run.json` e `report.json` antes de citar métricas. Não use números de exemplo como se fossem resultados medidos.

Comandos para o ensaio ou a gravação, a partir da raiz do repositório:

```sh
uv run minicode-eval run --case 05_validation --output evaluation/results/show-validation
uv run minicode-eval grade --run evaluation/results/show-validation
```

Se a pasta `evaluation/results/show-validation` já existir, escolha outro nome de saída. O comando `run` não sobrescreve resultados anteriores. Para uma demonstração com os seis casos, use `make evaluate` e depois `make grade RUN=<caminho-exibido>`; eles rodam até quatro casos em paralelo por padrão.

## Parte 1 — sequência sugerida (7 minutos)

| Tempo | Tela | Fala sugerida |
| --- | --- | --- |
| 0:00–0:40 | `README.md` e árvore do projeto | “O MiniCode recebe uma tarefa em linguagem natural, altera um projeto e verifica o resultado. A primeira entrega cobre o agente e o sistema que controla suas ações.” |
| 0:40–1:30 | `src/minicode/agent/`, `llm/`, `tools/` | “A orquestração está separada da porta do modelo e das ferramentas locais. O modelo propõe conteúdo; o programa decide quando ler, gravar e testar.” |
| 1:30–2:20 | `src/minicode/agent/__init__.py` | “A tarefa vira especificação com critérios de aceitação, depois plano e implementação. As transições de estado são validadas. O resultado só chega a `DONE` após pytest passar e a revisão de aceitação aprovar.” |
| 2:20–3:00 | `src/minicode/tools/__init__.py` | “As capacidades mínimas são listar, ler, gravar e testar. Os caminhos ficam dentro do projeto e os testes executam em uma cópia filtrada no Docker, sem rede e com limites de recursos.” |
| 3:00–4:40 | Terminal: `run` do caso escolhido e arquivos do histórico | Mostre a tarefa, `specification.md`, `plan.md`, arquivo alterado e eventos de teste em `actions.jsonl`. Aponte o estado final em `state.json`. |
| 4:40–5:25 | Histórico da mesma execução | Se houve falha inicial, mostre a saída do teste, o evento `REPAIRING`, a nova alteração e o teste seguinte. Se passou na primeira tentativa, diga isso claramente e explique o fluxo de reparo pelo código ou por um histórico real anterior. |
| 5:25–6:10 | Terminal: `grade` e `report.json` | “Os testes de aceitação ficam fora do projeto entregue ao agente. `grade` executa esses testes depois e calcula taxa de sucesso, sucesso na primeira tentativa, média de iterações e média de chamadas ao modelo.” Leia apenas os valores efetivamente obtidos. |
| 6:10–7:00 | `README.md`, `USO.md`, testes e `AI_USAGE.md` | “A documentação explica execução, arquitetura, limites e reprodução. Os testes do próprio MiniCode cobrem estados, ferramentas, histórico e avaliação.” Encerre com a limitação real: a imagem padrão usa Python 3.13 e `pytest`, sem dependências adicionais do projeto-alvo. |

### Onde encontrar as evidências da execução

Após `run`, a pasta do caso fica em `evaluation/results/show-validation/05_validation/project/`. Dentro dela, abra `.minicode/runs/<id>/`:

- `specification.md`: especificação produzida;
- `plan.md`: plano;
- `actions.jsonl`: chamadas de ferramenta, alterações, testes, erros e estados;
- `state.json`: tarefa, estado final, tentativas e contadores.

O arquivo alterado estará na própria cópia do projeto. O `report.json` da pasta da avaliação contém as métricas e o resultado dos testes externos. Não mostre `.env` nem credenciais.

## Parte 2 — itens para o vídeo final

A segunda entrega exige trabalho adicional. Use esta sequência **quando houver artefatos e resultados reais**:

1. Declare a hipótese e a função específica escolhida para especialização.
2. Mostre origem, filtragem e divisão do dataset em treino, validação e teste.
3. Abra o notebook executável no Colab: dependências, tokenização, modelo, LoRA ou QLoRA, treinamento, perdas, inferência e avaliação.
4. Compare quantitativamente o mesmo modelo antes e depois do ajuste. Inclua uma referência adicional quando fizer sentido.
5. Mostre a integração do modelo ajustado ao agente e o efeito na taxa de sucesso de tarefas completas.
6. Apresente uma ablação simples e discuta o que os números permitem concluir.
7. Mostre como reproduzir o experimento e a execução final.

Não apresente esta parte como concluída sem notebook, dataset, integração, ablação e resultados medidos.
