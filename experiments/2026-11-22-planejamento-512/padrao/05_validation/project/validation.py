def valid_age(age):
    if not isinstance(age, int):
        raise ValueError('Age must be an integer')
    if age < 0 or age > 120:
        raise ValueError('Age must be between 0 and 120')
    return age