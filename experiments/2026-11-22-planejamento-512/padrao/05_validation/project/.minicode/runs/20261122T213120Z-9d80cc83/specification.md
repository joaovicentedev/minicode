### Objetivo
O objetivo é criar uma função `valid_age` que valide idades fornecidas como parâmetro. A função deve retornar a idade válida se ela estiver dentro do intervalo de 0 a 120 (inclusive). Caso contrário, a função deve lançar um `ValueError`.

### Restrições explícitas
- A função deve aceitar apenas valores inteiros.
- Valores fora do intervalo de 0 a 120 devem gerar um `ValueError`.
- Valores booleanos (`True`, `False`) também devem gerar um `ValueError`.

### Critérios de aceitação verificáveis
1. A função retorna o valor inteiro fornecido se este estiver no intervalo de 0 a 120.
   - Exemplo: `valid_age(42)` deve retornar `42`.
2. A função lança um `ValueError` para valores inteiros fora do intervalo de 0 a 120.
   - Exemplo: `valid_age(-1)` deve lançar `ValueError`.
3. A função lança um `ValueError` para valores booleanos.
   - Exemplo: `valid_age(True)` deve lançar `ValueError`.
