1.  **Identificar e localizar** os arquivos relevantes:
    *   `calculator.py` (contém a função atual `sum_even` com erro `NotImplementedError`).
    *   `tests/test_calculator.py` (contém os testes existentes para validar a assinatura e a lógica).

2.  **Implementar** a função `sum_even` na `calculator.py`:
    *   Criar uma variável `total = 0`.
    *   Iterar sobre cada elemento `num` da lista `numbers`.
    *   Verificar se `num` é par (divisível por 2).
    *   Se for par, adicionar `num` à variável `total`.
    *   Atualizar a função `sum_even` para retornar `total`.

3.  **Criar** ou ajustar testes:
    *   Adicionar um teste específico para a função `sum_even` dentro de `tests/test_calculator.py`.
    *   Testar a função com os casos de entrada fornecidos na especificação (lista `[1, 2, 3, 4]`, `[0, 1, 2, 3, 4, 5]`, `[10, 21, 32, 43, 54]`).

4.  **Verificar** com pytest:
    *   Executar o teste `test_sum_even` usando o comando `pytest -q`.
    *   Confirmar que o resultado da execução é `pass` (ou `ok` dependendo do pytest version, mas o objetivo é a verificação de sucesso).

5.  **Descrever** os passos futuros:
    *   Executar o teste `test_sum_even` para confirmar que a função retorna a soma correta dos casos especificados.

