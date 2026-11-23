### Objetivo
O objetivo é modificar a função `list_items` no arquivo `catalog.py` para que ela retorne os itens de uma página específica, onde a primeira página corresponde a `page=1`. Além disso, a função deve rejeitar valores inválidos para `page` e `page_size`, que são menores que 1, lançando uma exceção `ValueError`.

### Restrições explícitas
- A função `list_items` deve receber três parâmetros: `items`, um iterável contendo os itens; `page`, um número inteiro indicando a página desejada (começando por 1); e `page_size`, um número inteiro indicando o tamanho da página.
- Valores de `page` ou `page_size` menores que 1 devem resultar em uma exceção `ValueError`.

### Critérios de aceitação verificáveis
1. Quando `list_items` é chamada com `page=1`, ela deve retornar os primeiros `page_size` elementos de `items`.
   - Exemplo: `list_items([1, 2, 3, 4, 5, 6], 1, 3)` retorna `[1, 2, 3]`.
2. Quando `list_items` é chamada com `page > 1`, ela deve retornar os elementos correspondentes à página especificada, considerando o tamanho da página.
   - Exemplo: `list_items([1, 2, 3, 4, 5, 6], 2, 3)` retorna `[4, 5, 6]`.
3. A função deve lançar uma exceção `ValueError` caso `page` ou `page_size` seja menor que 1.
   - Exemplo: `list_items([1, 2, 3, 4], 0, 2)` deve lançar `ValueError`.
   - Exemplo: `list_items([1, 2, 3, 4], 1, 0)` deve lançar `ValueError`.
