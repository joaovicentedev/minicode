### Objetivo
Refatorar a função `word_count` no arquivo `words.py` para uma implementação mais simples que mantenha o mesmo comportamento: contar as palavras separadas por espaços em branco em um texto, incluindo o caso de texto vazio.

### Restrições explícitas
- A função `word_count` deve receber um único parâmetro, que é uma string.
- O retorno da função deve ser um número inteiro representando a contagem de palavras.

### Critérios de aceitação verificáveis
1. Dado o texto `"um dois três"`, a função retorna `3`.
2. Dado o texto `"um dois três quatro"`, a função retorna `4`.
3. Dado o texto vazio `""`, a função retorna `0`.
4. Dado o texto `"   "` (três espaços), a função retorna `1`.
5. Dado o texto `"um"`, a função retorna `1`.
