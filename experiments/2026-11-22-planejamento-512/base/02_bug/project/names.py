def normalize_name(name):
    # Remove spaces at the ends and replace internal multiple spaces with a single space
    return ' '.join(name.strip().split())
