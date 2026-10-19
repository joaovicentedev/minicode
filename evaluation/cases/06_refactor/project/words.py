def word_count(text):
    words = []
    for part in text.split(" "):
        if part:
            words.append(part)
    return len(words)
