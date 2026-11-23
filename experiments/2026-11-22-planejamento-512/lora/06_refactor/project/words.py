def word_count(text):
    # Remove leading and trailing whitespaces
    text = text.strip()
    
    # Split the text by whitespace and filter out empty strings
    words = [word for word in text.split(' ') if word]
    
    return len(words)
