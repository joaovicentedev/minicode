### Objetivo
O objetivo é corrigir a função `normalize_name` no módulo `names.py`, de modo que ela remova espaços em branco nas extremidades da string e compacte qualquer sequência de espaços em branco internos em uma única instância de espaço. As letras devem ser mantidas conforme estão.

### Restrições explícitas
- A função deve receber uma string como entrada.
- A saída deve ser uma string onde espaços em branco extras são removidos.

### Critérios de aceitação verificáveis
1. A função deve retornar uma string com espaços em branco nas extremidades removidos.
2. Sequências de espaços em branco internos devem ser compactadas em um único espaço.
3. Teste com uma entrada contendo múltiplos espaços consecutivos antes e depois de nomes para verificar se a função funciona corretamente.

Exemplo de verificação:
- Entrada: `"  Ana   Maria  "`
- Saída esperada: `"Ana Maria"`
