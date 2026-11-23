def word_count(text):
    # Dividimos o texto em palavras usando espaços em branco como delimitadores
    words = text.split()
    # Contamos o número de palavras, ignorando espaços adicionais
    return len(words)
