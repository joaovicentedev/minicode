def normalize_name(name):
    # Remove spaces at the ends and replace sequences of internal spaces with a single space
    return ' '.join(name.strip().split())
