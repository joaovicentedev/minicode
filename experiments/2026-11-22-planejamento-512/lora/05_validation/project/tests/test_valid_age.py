import pytest
from validation import valid_age


def test_valid_age_42():
    assert valid_age(42) == 42

def test_valid_age_negative_one():
    with pytest.raises(ValueError):
        valid_age(-1)

def test_valid_age_true():
    with pytest.raises(ValueError):
        valid_age(True)

def test_valid_age_false():
    with pytest.raises(ValueError):
        valid_age(False)