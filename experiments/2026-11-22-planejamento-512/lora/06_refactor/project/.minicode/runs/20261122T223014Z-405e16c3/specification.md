### Objetivo
O objetivo é refatorar a função `word_count` de modo que ela continue contando as palavras separadas por espaços em branco em um texto, mas utilizando uma implementação mais simples.

### Restrições explícitas
- A função deve receber um único parâmetro, que é uma string.
- O retorno deve ser um número inteiro representando a quantidade de palavras no texto.
- Palavras são definidas como sequências de caracteres separadas por espaços em branco.
- Espaços em branco consecutivos devem ser considerados como uma única separação.
- Textos vazios devem retornar zero.

### Critérios de aceitação verificáveis
1. A função retorna 0 para uma string vazia.
2. A função retorna 1 para uma única palavra.
3. A função retorna 3 para a string "um dois três".
4. A função retorna 2 para a string "uma frase".
