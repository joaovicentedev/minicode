import pytest
from catalog import list_items


def test_pagination_boundaries():
    assert list_items([1, 2, 3], 3, 2) == []
    with pytest.raises(ValueError):
        list_items([1], 0, 2)
    with pytest.raises(ValueError):
        list_items([1], 1, 0)
