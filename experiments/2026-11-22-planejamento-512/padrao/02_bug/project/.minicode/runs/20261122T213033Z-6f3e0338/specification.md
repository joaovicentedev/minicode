### Objetivo
O objetivo é criar uma função `normalize_name` que limpe strings de nomes, removendo espaços em branco nas extremidades e substituindo sequências de espaços internos por um único espaço, enquanto preserva as letras do nome.

### Restrições explícitas
- A função deve receber uma string como parâmetro.
- O retorno deve ser uma string formatada conforme especificado.

### Critérios de aceitação verificáveis
1. A função retorna `"Ana Maria"` quando fornecida com `"  Ana   Maria  "` como entrada.
2. A função retorna `"João Silva"` quando fornecida com `"João  Silva"` como entrada.
3. A função retorna `"Maria Clara"` quando fornecida com `"Maria  Clara"` como entrada.
