#!/usr/bin/env python

def valid_age(age):
    if isinstance(age, bool):
        raise ValueError('Invalid age')
    if not isinstance(age, int):
        raise ValueError('Invalid age')
    if age < 0 or age > 120:
        raise ValueError('Invalid age')
    return age