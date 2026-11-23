### Objetivo
Criar testes pytest no arquivo `tests/test_clamp.py` para a função `clamp(value, minimum, maximum)` localizada em `clamp.py`. Os testes devem abranger casos onde o valor está abaixo, dentro e acima do intervalo definido por `minimum` e `maximum`.

### Restrições explícitas
- O teste deve utilizar a função `clamp` importada do módulo `clamp.py`.
- Não é necessário modificar o conteúdo de `clamp.py`.

### Critérios de aceitação verificáveis
- **Teste de valor abaixo do intervalo**: Verificar se a função retorna o valor mínimo quando o parâmetro `value` é menor que o valor de `minimum`.
- **Teste de valor dentro do intervalo**: Verificar se a função retorna o próprio valor quando este está entre `minimum` e `maximum`.
- **Teste de valor acima do intervalo**: Verificar se a função retorna o valor máximo quando o parâmetro `value` é maior que o valor de `maximum`.

Cada critério deve ser verificado através de chamadas à função `clamp` com diferentes valores de entrada e comparação dos resultados esperados.
