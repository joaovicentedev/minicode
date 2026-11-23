1.  **Localizar e analisar testes existentes**:
    *   Verificar `tests/test_validation.py` para entender a estrutura de validação atual e os casos de erro já testados.
    *   Identificar que a função `valid_age` retorna apenas o valor, sem validar o tipo (int/bool) ou o intervalo.

2.  **Implementar a função**:
    *   Criar `valid_age` que recebe o argumento `age`.
    *   Verificar se `age` é um número inteiro.
    *   Verificar se `age` está entre 0 e 120 (inclusive).
    *   Se for válido, retornar `age`.
    *   Se for inválido (não inteiro, menor que 0 ou maior que 120, ou booleano), lançar `ValueError`.

3.  **Verificar com pytest**:
    *   Executar `pytest -v` para confirmar que a função retorna o valor esperado e que erros de tipo ou intervalo são detectados corretamente.

