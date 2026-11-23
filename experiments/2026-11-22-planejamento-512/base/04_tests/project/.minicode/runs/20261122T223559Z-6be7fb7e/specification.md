### Objetivo
Criar testes pytest no arquivo `tests/test_clamp.py` para a função `clamp(value, minimum, maximum)` que é definida em `clamp.py`. Os testes devem abranger os casos onde o valor está abaixo, dentro e acima do intervalo definido por `minimum` e `maximum`.

### Restrições explícitas
- A função `clamp(value, minimum, maximum)` retorna o valor limitado pelo intervalo `[minimum, maximum]`.
- O valor de retorno deve ser igual ao `value` se estiver dentro do intervalo.
- Se o `value` for menor que `minimum`, a função deve retornar `minimum`.
- Se o `value` for maior que `maximum`, a função deve retornar `maximum`.

### Critérios de aceitação verificáveis
1. Quando o valor está abaixo do intervalo, a função deve retornar o `minimum`.
   - Exemplo: `assert clamp(-1, 0, 10) == 0`
2. Quando o valor está dentro do intervalo, a função deve retornar o próprio `value`.
   - Exemplo: `assert clamp(5, 0, 10) == 5`
3. Quando o valor está acima do intervalo, a função deve retornar o `maximum`.
   - Exemplo: `assert clamp(15, 0, 10) == 10`
