### Objetivo
O objetivo é modificar a função `list_items` no módulo `catalog.py` para que ela retorne uma lista de itens correspondendo à página especificada, começando com `page=1`. Além disso, a função deve rejeitar valores de `page` ou `page_size` menores que 1, lançando um `ValueError`.

### Restrições explícitas
- A função `list_items` deve receber três parâmetros: `items`, `page`, e `page_size`.
- `page` e `page_size` devem ser números inteiros.
- Se `page` ou `page_size` forem menores que 1, a função deve lançar um `ValueError`.

### Critérios de aceitação verificáveis
1. A função retorna os itens corretamente para a página especificada.
   - Exemplo: `list_items([1, 2, 3, 4, 5, 6, 7, 8], 2, 4)` deve retornar `[5, 6, 7, 8]`.
2. A função lança `ValueError` quando `page` ou `page_size` são menores que 1.
   - Exemplo: `list_items([1, 2, 3, 4, 5, 6, 7, 8], 0, 4)` deve lançar `ValueError`.
   - Exemplo: `list_items([1, 2, 3, 4, 5, 6, 7, 8], 2, 0)` deve lançar `ValueError`.
