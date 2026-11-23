### Objetivo
Refatorar a função `word_count` em `words.py` para uma implementação mais simples, mantendo seu comportamento original de contar palavras separadas por espaços em branco, inclusive no caso de texto vazio.

### Restrições explícitas
- A função deve receber um único argumento: `text`, que é uma string.
- A função deve retornar um número inteiro representando a contagem de palavras.
- Palavras são consideradas separadas por espaços em branco.
- Texto vazio deve ser considerado como contendo zero palavras.

### Critérios de aceitação verificáveis
- A função deve retornar `0` quando chamada com uma string vazia.
- A função deve retornar `3` quando chamada com `"um dois três"`.
- A função deve retornar `1` quando chamada com `"palavra"` ou `" palavra "`.
- A função deve retornar `2` quando chamada com `"uma frase aqui"`.
