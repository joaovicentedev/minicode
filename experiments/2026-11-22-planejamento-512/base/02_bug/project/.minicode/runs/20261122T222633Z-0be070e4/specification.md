### Objetivo
O objetivo é corrigir a função `normalize_name` no módulo `names.py` para que ela remova espaços em branco nas extremidades da string e compacte qualquer sequência de espaços em branco internos em apenas um espaço, mantendo as letras inalteradas.

### Restrições Explícitas
- A função deve receber uma única string como parâmetro.
- A saída da função deve ser uma string.

### Critérios de Aceitação Verificáveis
- Dado a entrada `"  Ana   Maria  "`, a função deve retornar `"Ana Maria"`.
- Dado a entrada `"João da Silva  "`, a função deve retornar `"João da Silva"`.
- Dado a entrada `"Maria  da Silva"`, a função deve retornar `"Maria da Silva"`.
- Dado a entrada `" José Carlos "`, a função deve retornar `"José Carlos"`.
