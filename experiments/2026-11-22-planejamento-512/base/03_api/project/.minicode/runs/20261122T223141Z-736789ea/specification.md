### Objetivo
O objetivo é modificar a função `list_items` para que ela retorne uma página específica de itens, começando com `page=1`. Além disso, a função deve rejeitar valores de `page` ou `page_size` menores que 1, lançando um `ValueError`.

### Restrições explícitas
- A função `list_items` deve receber três parâmetros: `items`, `page`, e `page_size`.
- Os parâmetros `page` e `page_size` devem ser números inteiros.
- Valores de `page` ou `page_size` menores que 1 devem gerar um `ValueError`.

### Critérios de aceitação verificáveis
- A função deve retornar a página correta de itens quando `page` e `page_size` são válidos.
- A função deve lançar um `ValueError` quando `page` ou `page_size` forem menores que 1.
- Exemplos de validação:
  - `list_items([1, 2, 3, 4], 2, 2)` deve retornar `[3, 4]`.
  - `list_items([1, 2, 3, 4], 1, 2)` deve retornar `[1, 2]`.
  - Tentar `list_items([1, 2, 3, 4], 0, 2)` deve lançar um `ValueError`.
  - Tentar `list_items([1, 2, 3, 4], 2, 0)` deve lançar um `ValueError`.
