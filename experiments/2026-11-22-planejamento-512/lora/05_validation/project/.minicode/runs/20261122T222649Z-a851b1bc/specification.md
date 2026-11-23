### Objetivo
Criar uma função `valid_age(age)` que valide idades fornecidas como entrada. A função deve retornar a idade válida ou lançar um `ValueError` para entradas inválidas.

### Restrições explícitas
- A função deve aceitar e retornar valores inteiros entre 0 e 120, inclusive.
- Entradas booleanas (`True`, `False`) devem gerar um `ValueError`.
- Outras entradas que não sejam inteiros também devem gerar um `ValueError`.

### Critérios de aceitação verificáveis
- A função deve retornar `42` quando chamada com `42`.
- A função deve lançar `ValueError` quando chamada com `-1`.
- A função deve lançar `ValueError` quando chamada com `True`.
- A função deve lançar `ValueError` quando chamada com `False`.
