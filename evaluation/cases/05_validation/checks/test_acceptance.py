import pytest
from validation import valid_age


def test_valid_age_boundaries_and_types():
    assert valid_age(0) == 0
    assert valid_age(120) == 120
    for value in (121, True, False, 20.5, "20"):
        with pytest.raises(ValueError):
            valid_age(value)
