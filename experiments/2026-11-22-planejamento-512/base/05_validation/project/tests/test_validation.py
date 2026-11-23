import pytest
from validation import valid_age


def test_valid_age():
    assert valid_age(42) == 42
    with pytest.raises(ValueError):
        valid_age(-1)


@pytest.mark.parametrize("value", [True, False])
def test_valid_age_rejects_booleans(value):
    with pytest.raises(ValueError):
        valid_age(value)
