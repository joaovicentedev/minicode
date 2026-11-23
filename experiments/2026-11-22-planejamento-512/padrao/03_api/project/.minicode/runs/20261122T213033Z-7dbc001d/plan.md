1. Localize o arquivo `catalog.py`.
2. Implemente as alterações necessárias na função `list_items` em `catalog.py` para atender aos requisitos especificados.
3. Verifique se há testes existentes em `test_catalog.py`. Se sim, edite-os conforme necessário.
4. Adicione novos casos de teste em `test_catalog.py` para cobrir os cenários onde `page` ou `page_size` são menores que 1.
5. Execute os testes com `pytest -q` para garantir que todos os casos de teste passem.
6. Confirme que a função lança `ValueError` quando `page` ou `page_size` são menores que 1.
