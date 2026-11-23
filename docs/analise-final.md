# Análise final do MiniCode

Neste experimento, o LoRA melhorou a estrutura dos planos, mas não
aumentou o sucesso do agente: o planejador base resolveu 6/6 tarefas e o adaptado resolveu
5/6. O resultado é exploratório, com uma execução por condição e seis casos.

## Configuração e evidências

O treinamento especializou somente o planejamento (`PLAN`) do Qwen3.5-0.8B.
Especificação, implementação, reparo e revisão continuaram no Qwen2.5-14B.
Como referência adicional, foi utilizado o Qwen2.5-14B também no planejamento.

Base e LoRA foram avaliados com o mesmo conjunto de seis casos, duas tentativas, um worker,
CPU float32 e geração determinística, sem thinking, de até 512 tokens por plano.
Foi selecionado o checkpoint da época 3, com menor loss de validação.
A referência foi executada separadamente com quatro workers e a configuração
de geração do endpoint remoto. A duração entre condições não foi comparada.

Os resultados foram obtidos dos [relatórios e históricos preservados](../experiments/2026-11-22-planejamento-512/).
`run.json` registra a execução; `report.json` mede o comportamento com testes
externos, que ficam fora do contexto do agente. Sucesso exige `DONE` e aprovação
nesses testes. O [manifesto](../experiments/2026-11-22-planejamento-512/manifest.json)
registra revisão dos pesos, dependências e hashes. Os pesos ficam fora do Git.

## Treinamento e avaliação especializada

Foram utilizadas 80 tarefas de treino, 10 de validação e 10 de teste. O treinamento
foi realizado por dez épocas com LoRA de rank 8, alpha 16 e dropout 0,05, aplicado a
`q_proj` e `v_proj`. O melhor checkpoint foi o da época 3, com loss de validação
1,6207. A queda posterior da loss de treino acompanhada de piora da validação
sugere sobreajuste e justifica selecionar o checkpoint pela validação.

O [arquivo de métricas](../notebooks/minicode-plan-lora/metrics.json) registra
os resultados do mesmo teste especializado antes e depois do ajuste:

| Medida | Base | LoRA |
| --- | --- | --- |
| Conformidade estrutural | 0% | 100% |
| Alinhamento à tarefa | 20% | 60% |
| Cobertura dos critérios selecionados | 20% | 40% |
| Consistência com o contexto | 90% | 100% |
| Aprovação conjunta | 0% | 30% |

São medidas estruturais e lexicais, conforme a [descrição das métricas](metricas-planejamento.md).
Elas não demonstram compreensão semântica completa. `predictions.json` e o
notebook executado não estavam no pacote transferido para este repositório;
a revisão manual dos dez exemplos especializados ainda não foi realizada.

## Resultados no agente completo

| Planejador | Sucesso externo + DONE | Primeira tentativa | Tentativas médias | Chamadas médias |
| --- | --- | --- | --- | --- |
| Qwen2.5-14B, referência | 5/6 (83,3%) | 3/6 (50%) | 1,50 | 4,33 |
| Qwen3.5-0.8B, base | 6/6 (100%) | 3/6 (50%) | 1,50 | 4,50 |
| Qwen3.5-0.8B + LoRA | 5/6 (83,3%) | 3/6 (50%) | 1,50 | 4,50 |

| Caso | Referência | Base | LoRA |
| --- | --- | --- | --- |
| Implementação de função | Passou | Passou | Passou |
| Correção de bug | Passou | Passou | Passou |
| Modificação de API | Passou | Passou | Passou |
| Criação de testes | Passou | Passou | Passou |
| Validação de dados | Falhou | Passou | Passou |
| Refatoração | Passou | Passou | Falhou |

Nos seis planos do agente, o base teve 0/6 aprovações na regra estrutural e o
LoRA teve 6/6. Apesar disso, o base teve uma solução correta a mais. A estrutura
favorecida pelo treino não foi suficiente para melhorar o resultado do sistema.

Na referência, a validação aceitou booleanos como idades, contrariando a tarefa;
os testes visíveis impediram `DONE`. No LoRA, a refatoração terminou em `DONE`,
mas reprovou nos testes externos: `word_count('  um\t dois\ntrês  ')` retornou 2,
quando deveria retornar 3. A implementação separava por espaço literal, sem
tratar todas as formas de espaço em branco. Esse caso evidencia a limitação dos
testes visíveis e da revisão feita pelo modelo.

As restrições também foram exercitadas: o harness rejeitou propostas que tentavam
modificar testes existentes. Base recuperou esse erro nos casos de bug e API;
LoRA recuperou nos casos de função e bug. Na condição base, três casos passaram
somente após uma segunda tentativa; no LoRA, dois dos cinco sucessos ocorreram
na segunda tentativa.

## Respostas ao item 37

1. **Quanto a LLM faz sozinha e quanto depende do harness?** O modelo propõe
   planos e código; o harness controla escrita, executa testes e fornece feedback.
   Foram observadas recuperações e bloqueios.
2. **Spec-Driven Development melhora a execução?** Todas as condições utilizaram
   especificação. Sem uma condição sem spec, esse ganho não foi isolado.
3. **Pedir uma regra difere de impô-la no código?** Sim. O modelo propôs alterar
   testes protegidos; a validação programática recusou as propostas antes da escrita.
4. **O feedback permite corrigir erros?** Sim, houve sucesso após segunda tentativa:
   três casos no base e dois no LoRA. O reparo não resolveu todos os problemas.
5. **O fine-tuning melhorou o modelo?** Houve melhora nas medidas especializadas de
   estrutura e conteúdo lexical; a correção semântica geral não foi comprovada.
6. **O ganho especializado melhorou o agente completo?** Esse ganho não foi observado nesta execução:
   base teve 6/6 sucessos e LoRA, 5/6, apesar da melhora estrutural dos planos.
7. **O modelo pequeno especializado compete com o maior na tarefa restrita?**
   No agente, o planejador LoRA igualou os 5/6 da referência maior. A amostra pequena
   e a ausência de comparação especializada direta com o maior impedem afirmar equivalência.
8. **Quais componentes tiveram maior impacto?** Foram observados efeitos das restrições, do feedback e dos
   testes externos, mas o impacto individual de cada componente não foi isolado.

## Estudo de ablação: oportunidade de reparo

**Pergunta:** permitir uma segunda tentativa contribuiu para o sucesso do agente?

Foi realizada uma ablação retrospectiva, comparando os mesmos históricos dos casos
aprovados na primeira tentativa com os aprovados ao final de até duas tentativas.
A condição sem reparo foi estimada interrompendo cada histórico após a primeira
tentativa e mantendo suas respostas iniciais. Não foram feitas novas chamadas
aos modelos nem uma execução independente com `--max-attempts 1`.

Os valores foram extraídos de `first_attempt_success` e `success` nos arquivos
[`report.json`](../experiments/2026-11-22-planejamento-512/) de cada condição.
O critério continua sendo aprovação do agente e dos testes externos.

| Planejador | Sem reparo, estimado | Com reparo, observado | Diferença |
| --- | --- | --- | --- |
| Qwen2.5-14B, referência | 3/6 (50%) | 5/6 (83,3%) | +33,3 pontos percentuais |
| Qwen3.5-0.8B, base | 3/6 (50%) | 6/6 (100%) | +50 pontos percentuais |
| Qwen3.5-0.8B + LoRA | 3/6 (50%) | 5/6 (83,3%) | +33,3 pontos percentuais |

No base, a segunda tentativa recuperou os casos de correção de bug, API e
validação. No LoRA, recuperou implementação de função e correção de bug.
O feedback inclui rejeições de escrita e resultados de verificação; portanto,
o efeito observado é da oportunidade de reparo com esse conjunto de sinais,
e não apenas do feedback dos testes.

**Conclusão:** a análise dos históricos indica que remover a oportunidade de reparo
reduziria o número de soluções aprovadas nas três condições. O reparo foi útil,
mas não suficiente: a refatoração do LoRA continuou reprovada nos testes externos.
Foram analisados seis casos por condição, mantendo as primeiras respostas fixas
nessa estimativa. A variabilidade de uma nova execução sem reparo não foi medida.
