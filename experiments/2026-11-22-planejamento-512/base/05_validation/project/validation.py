#!/usr/bin/env python


def valid_age(age):
    # Verifica se 'age' é um número inteiro
    if not isinstance(age, int):
        raise ValueError('Age must be an integer')
    
    # Verifica se 'age' é True ou False
    if age is True or age is False:
        raise ValueError('Age must be an integer')
    
    # Verifica se 'age' está entre 0 e 120 (inclusive)
    if age < 0 or age > 120:
        raise ValueError('Age must be between 0 and 120')
    
    # Retorna a idade válida
    return age