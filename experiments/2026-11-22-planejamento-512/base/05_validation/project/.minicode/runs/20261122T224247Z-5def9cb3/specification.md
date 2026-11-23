### Objetivo
Criar uma função `valid_age(age)` que valide idades fornecidas como parâmetro. A função deve retornar a idade válida ou lançar um `ValueError` caso a idade seja inválida.

### Restrições explícitas
- A função deve aceitar números inteiros.
- A função deve validar idades entre 0 e 120, inclusive.
- Qualquer valor fora desse intervalo deve gerar um `ValueError`.
- Booleanos (`True`, `False`) devem gerar um `ValueError`.

### Critérios de aceitação verificáveis
- A função deve retornar o número inteiro fornecido se estiver dentro do intervalo de 0 a 120.
- A função deve lançar um `ValueError` se o número fornecido for menor que 0 ou maior que 120.
- A função deve lançar um `ValueError` se o valor fornecido for um booleano.

Exemplos de verificação:
- `valid_age(42)` deve retornar `42`.
- `valid_age(-1)` deve lançar um `ValueError`.
- `valid_age(True)` deve lançar um `ValueError`.
