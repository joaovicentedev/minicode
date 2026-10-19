from calculator import sum_even


def test_sum_even_handles_negative_and_empty_lists():
    assert sum_even([-4, -3, 0, 5]) == -4
    assert sum_even([]) == 0
