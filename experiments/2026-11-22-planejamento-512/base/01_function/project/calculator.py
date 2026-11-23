def sum_even(numbers):
    total = 0
    for num in numbers:
        if isinstance(num, int) and num % 2 == 0:
            total += num
    return total