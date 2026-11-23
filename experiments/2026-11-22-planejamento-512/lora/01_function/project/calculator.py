def sum_even(numbers):
    return sum(number for number in numbers if isinstance(number, int) and number % 2 == 0)
