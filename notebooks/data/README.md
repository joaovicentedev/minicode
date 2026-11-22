# Dados e avaliação de planejamento

A função especializada é produzir um plano a partir de tarefa, especificação e contexto do repositório. A hipótese principal é que o ajuste melhora a proporção de planos estruturalmente conformes. A qualidade do conteúdo é uma avaliação complementar, necessária para interpretar esse ganho.

## Origem e formato

O conjunto contém 100 exemplos: 80 de treino, 10 de validação e 10 de teste. Foram preservados os 12 exemplos iniciais de treino e todos os exemplos de validação e teste. Os 68 exemplos adicionais de treino e os 14 exemplos adicionais de validação e teste são sintéticos, elaborados com apoio de IA nesta ampliação, sem consultas a um endpoint de geração e sem execução de soluções de referência.

Cada linha JSONL contém exatamente quatro campos de texto: `task`, `spec`, `context` e `plan`. `format_example` monta o mesmo prompt de planejamento usado pelo agente; somente `plan` é a resposta de treinamento. Os contextos adicionais de treino são pequenos módulos Python com uma função ainda não implementada. Os novos casos de validação e teste incluem implementação, correção de bugs, criação de testes e refatoração, com módulos e contratos distintos dos exemplos de treino. As especificações incluem restrições e casos de aceitação; os planos indicam inspeção, alteração, testes específicos e execução de `pytest -q`.

Os temas incluem cálculos, sequências, dicionários, processamento de texto, validação, serialização e utilidades HTTP. Os novos planos têm estrutura semelhante e predominam tarefas de implementação: variedade de domínio não equivale a variedade de projetos reais. O conjunto continua exploratório.

## Separação e verificação

A separação é fixa por tarefa, sem redistribuição aleatória nesta ampliação. Os testes automatizados verificam contagens, tarefas e contextos distintos entre os splits e conformidade estrutural dos planos. Essa verificação não identifica toda similaridade semântica entre tarefas e não comprova a correção dos planos.

A verificação de qualidade nesta etapa consiste em critérios explícitos nos exemplos e rubricas auditáveis; ainda é necessária revisão humana para detectar ambiguidades e erros semânticos. Não houve filtragem baseada em respostas do modelo nem seleção de exemplos por desempenho. Os dados iniciais de treino incluem temas próximos aos casos existentes de avaliação do agente; use tarefas novas para conclusões sobre generalização end-to-end.

Validação e teste têm dez exemplos cada e ainda são pequenos. Uma mudança de uma resposta altera uma taxa em 10 pontos percentuais. Use validação para decisões de configuração; mantenha o teste fora do treinamento e da seleção de hiperparâmetros. As rubricas de avaliação não são inseridas nos prompts nem usadas como respostas de treinamento.

## Métricas automáticas

`plan_score` mede cada critério separadamente e `summarize_plans` calcula sua taxa no conjunto avaliado:

| Medida | Interpretação |
| --- | --- |
| `numbered` | Linhas numeradas consecutivamente a partir de 1 |
| `mentions_tests` | Menção textual a testes |
| `mentions_pytest` | Presença de `pytest -q` |
| `no_code_block` | Ausência de bloco Markdown de código |
| `no_completed_claim` | Ausência de algumas afirmações de conclusão em português |
| `structural_pass` | Todos os cinco critérios estruturais satisfeitos |
| `task_alignment` | Evidências lexicais da ação e do assunto específico da tarefa |
| `spec_coverage` | Evidências lexicais de critérios e casos de aceitação por tarefa |
| `context_consistency` | Referência ao arquivo esperado no contexto |
| `quality_pass` | As três dimensões de evidências satisfeitas |
| `overall_pass` | Conformidade estrutural e todas as evidências satisfeitas |

`rubrics.json` associa cada tarefa de validação e teste a três dimensões. Cada dimensão contém grupos de alternativas; todos os grupos devem ser atendidos, com pelo menos um termo de cada grupo. A comparação ignora caixa e acentos e exige limites de palavra. Use a mesma rubrica para base e adaptado, definida antes de observar as respostas geradas.

Essas dimensões são **proxies lexicais, não notas de correção semântica**. Sinônimos ausentes da rubrica podem gerar falsos negativos; contradições contendo os termos esperados podem gerar falsos positivos. Referenciar o arquivo correto não garante coerência com sua API. A referência inicial de validação para `arithmetic.py`, por exemplo, fala em contrato, mas não explicita a exceção exigida; a nova métrica de cobertura a rejeita. O exemplo foi preservado.

## Rubrica de revisão manual

Revise as respostas base e ajustada, preferencialmente ocultando qual modelo as produziu. Para cada dimensão, atribua 0, 1 ou 2 e justifique com trechos do plano:

| Dimensão | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Adequação à tarefa | Propõe comportamento errado ou não aborda a tarefa | Direção correta, mas genérica ou parcialmente divergente | Ações concretas compatíveis com o objetivo e sem contradições |
| Cobertura da especificação | Omite requisitos essenciais ou os contradiz | Cobre parte dos requisitos, faltando limites ou testes relevantes | Contempla requisitos explícitos e testes dos casos de aceitação |
| Coerência com o contexto | Inventa uma estrutura incompatível ou altera API indevidamente | Localização correta, mas sem detalhes suficientes para aferir compatibilidade | Referencia arquivos e símbolos corretos e preserva contratos existentes |

Registre em `manual_review` de `predictions.json`, para cada modelo, por exemplo:

```json
{
  "task_alignment": 2,
  "spec_coverage": 1,
  "context_consistency": 2,
  "justification": "A ação e o arquivo estão corretos, mas falta testar entrada vazia."
}
```

Reporte médias por dimensão e a proporção de planos com nota 2 nas três dimensões. Não misture essas notas com as taxas automáticas. Se houver ambiguidade na especificação, registre-a em vez de acrescentar exigências retrospectivamente. Qualidade local de plano também não substitui `TaskSuccessRate` nos testes externos do agente.

## Uso no Colab

O notebook carrega os splits e as rubricas, compara o mesmo teste antes e depois do ajuste e grava `metrics.json` com taxas e perdas. Também exporta `predictions.json` com tarefa, contexto, especificação, referência, respostas, critérios e campos para revisão manual. Baixe esses arquivos e o adaptador antes de encerrar o runtime.

Publique os arquivos desta alteração na branch configurada no notebook antes de executar no Colab. O notebook busca o código do repositório remoto; mudanças apenas locais não estarão disponíveis lá. O treinamento e a compatibilidade com a GPU ainda precisam ser verificados no Colab.
