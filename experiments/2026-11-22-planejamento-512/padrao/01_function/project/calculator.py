def sum_even(numbers):
    total = 0
    for number in numbers:
        if isinstance(number, int) and number % 2 == 0:
            total += number
    return total