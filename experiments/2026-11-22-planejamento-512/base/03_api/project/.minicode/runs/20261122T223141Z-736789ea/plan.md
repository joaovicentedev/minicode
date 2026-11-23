1.  **Validar entrada de parâmetros**: Verificar se `page` e `page_size` são números inteiros válidos antes de executar a lógica.
2.  **Validar limites**: Verificar se `page` ou `page_size` são maiores que 1. Se forem menores, lançar `ValueError`.
3.  **Executar lógica**: Aplicar a lógica de filtragem de itens baseada no valor de `page` e `page_size`.
4.  **Verificar resultados**: Confirmar que a função retorna a lista correta quando os parâmetros são válidos.
5.  **Executar testes**: Executar os testes existentes e novos para garantir que a validação de limites e a lógica de filtragem funcionem corretamente.

