### Objetivo
Criar testes pytest em `tests/test_clamp.py` para a função `clamp(value, minimum, maximum)` presente no módulo `clamp.py`. Os testes devem abranger os casos onde o valor está abaixo, dentro e acima do intervalo definido por `minimum` e `maximum`.

### Restrições explícitas
- A função `clamp` retorna o valor se este estiver dentro do intervalo definido por `minimum` e `maximum`.
- Se o valor for menor que `minimum`, a função retorna `minimum`.
- Se o valor for maior que `maximum`, a função retorna `maximum`.

### Critérios de aceitação verificáveis
- **Teste para valor dentro do intervalo:** Verificar se a função retorna o valor quando este está dentro do intervalo.
  - Exemplo: `assert clamp(5, 0, 10) == 5`
- **Teste para valor abaixo do intervalo:** Verificar se a função retorna `minimum` quando o valor é menor que `minimum`.
  - Exemplo: `assert clamp(-3, 0, 10) == 0`
- **Teste para valor acima do intervalo:** Verificar se a função retorna `maximum` quando o valor é maior que `maximum`.
  - Exemplo: `assert clamp(15, 0, 10) == 10`

Esses critérios permitem validar que a função `clamp` funciona corretamente em todos os casos possíveis.
