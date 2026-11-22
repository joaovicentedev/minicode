# Métricas de avaliação dos planos

Uso três medidas para distinguir o formato do plano, a presença de critérios específicos e a aprovação conjunta. Cada medida vale `True` ou `False` por resposta. Na avaliação dos dez exemplos de teste, o notebook calcula a proporção de respostas aprovadas em cada medida.

As regras estão em [planning_data.py](../src/minicode/planning_data.py), e os termos específicos de cada tarefa estão em [rubrics.json](../notebooks/data/rubrics.json). Essas métricas avaliam o texto do plano; não executam a implementação e não participam da loss de treinamento.

## Exemplo do conjunto de teste

O primeiro exemplo de [test.jsonl](../notebooks/data/test.jsonl) contém:

**Tarefa:** Corrija ordenação de eventos em events.py.

**Especificação:** Ordenar eventos pela data crescente.

**Contexto:**

```python
def sort_events(events): return events
```

O plano de referência é:

```text
1. Ler events.py e os testes.
2. Corrigir a ordenação pela data.
3. Testar eventos fora de ordem e entrada vazia.
4. Verificar com pytest -q.
```

Esse plano é a referência do dataset, não uma resposta observada em uma execução do modelo. Os demais planos abaixo são variações ilustrativas.

## structural_pass: formato do plano

`structural_pass` vale `True` quando os cinco critérios abaixo passam ao mesmo tempo:

| Critério | O que a implementação verifica |
| --- | --- |
| `numbered` | Todas as linhas não vazias começam com número, ponto ou parêntese e espaço; a sequência começa em 1 e não tem saltos |
| `mentions_tests` | O texto em minúsculas contém a sequência `test` |
| `mentions_pytest` | O texto em minúsculas contém `pytest -q` |
| `no_code_block` | O texto não contém três crases consecutivas |
| `no_completed_claim` | O texto não contém as expressões detectadas: “já executei”, “já criei”, “já implementei” ou “testes passaram” |

O plano de referência atende aos cinco critérios, então `structural_pass = True`.

Um plano pode passar nessa medida mesmo sem detalhar a solução:

```text
1. Ler os arquivos e os testes.
2. Ajustar a implementação.
3. Executar pytest -q.
```

Esse plano tem o formato esperado, mas não diz que precisa ordenar eventos pela data. Por isso, aprovação estrutural não significa adequação à tarefa.

A regra `mentions_tests` é particularmente simples: até a palavra `pytest` satisfaz a busca por `test`. Da mesma forma, `no_completed_claim` detecta apenas as expressões listadas, não toda possível afirmação de conclusão.

## spec_coverage: evidências dos critérios selecionados

`spec_coverage` procura termos definidos na rubrica da tarefa. Para o exemplo de eventos, a regra é:

```json
"spec_coverage": [
  ["fora de ordem", "desordenados", "desordenadas"],
  ["vazia", "vazio"]
]
```

Cada lista interna é um grupo de alternativas. Para passar, o plano precisa conter **pelo menos uma alternativa de cada grupo**. A comparação ignora maiúsculas e acentos e usa limites de palavra.

No plano de referência, o terceiro passo contém:

```text
3. Testar eventos fora de ordem e entrada vazia.
```

“Fora de ordem” satisfaz o primeiro grupo e “vazia” satisfaz o segundo. Portanto, `spec_coverage = True`.

Se esse passo fosse apenas:

```text
3. Testar eventos fora de ordem.
```

faltaria uma alternativa do grupo `vazia`/`vazio`. Nesse caso, `spec_coverage = False`, mesmo que os demais passos continuassem iguais.

O nome da métrica não significa que toda a especificação foi compreendida ou verificada. Neste caso, a rubrica seleciona dois cenários de teste; a menção à ordenação pela data é avaliada em outra dimensão. A direção crescente não tem uma verificação lexical específica. Os grupos da rubrica são critérios de avaliação selecionados, não uma reprodução exaustiva da especificação.

## overall_pass: aprovação conjunta

`overall_pass` combina estrutura e as três dimensões de conteúdo:

```text
overall_pass = structural_pass
               AND task_alignment
               AND spec_coverage
               AND context_consistency
```

Para o exemplo de eventos:

| Dimensão | Evidência exigida |
| --- | --- |
| `task_alignment` | “ordenação” ou “ordenar”, além de “data” |
| `spec_coverage` | Uma expressão de eventos fora de ordem, além de “vazia” ou “vazio” |
| `context_consistency` | Referência a `events.py` |

O plano de referência satisfaz as três dimensões e o formato, então `overall_pass = True`.

Se o plano trocar `events.py` por `other.py`, pode continuar passando em `structural_pass` e `spec_coverage`, mas falha em `context_consistency`. Consequentemente, `overall_pass = False`.

| Plano | structural_pass | spec_coverage | overall_pass |
| --- | --- | --- | --- |
| Referência original | True | True | True |
| Genérico: ler arquivos, ajustar implementação e executar pytest | True | False | False |
| Referência sem mencionar entrada vazia | True | False | False |
| Referência com `other.py` em vez de `events.py` | True | True | False |
| Referência com a primeira linha sem numeração | False | True | False |

`overall_pass` não é a média das outras medidas: todas precisam passar. A rubrica é necessária para calcular as dimensões de conteúdo; uma chamada a `plan_score` sem rubrica retorna somente os critérios estruturais.

## Interpretação das taxas do notebook

Se oito dos dez planos passarem em `structural_pass`, a taxa será `0.8`, ou 80%. Se seis passarem em `spec_coverage`, a taxa será `0.6`. Se quatro atenderem simultaneamente ao formato e às três dimensões de conteúdo, `overall_pass` será `0.4`.

Esses números são apenas um exemplo de cálculo. Não representam resultados medidos do modelo. Os planos que passam em cada critério podem ser diferentes; a taxa de `overall_pass` é calculada resposta por resposta, e não pela multiplicação ou média das taxas individuais.

## Limite da avaliação automática

As métricas procuram evidências textuais, não verificam o significado completo do plano. Um texto pode mencionar os termos esperados e ainda propor uma solução errada. Por exemplo, trocar “corrigir a ordenação pela data” por “ordenar pela data decrescente” mantém todos os termos exigidos e pode continuar passando, embora contradiga a especificação de ordem crescente.

Também pode ocorrer o contrário: um plano correto que use “coleção sem elementos” pode reprovar no grupo `vazia`/`vazio`. A revisão manual complementa essas medidas, e os testes externos do agente verificam o comportamento do código produzido.
