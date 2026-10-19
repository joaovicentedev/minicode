from catalog import list_items


def test_second_page():
    assert list_items([1, 2, 3, 4], 2, 2) == [3, 4]
