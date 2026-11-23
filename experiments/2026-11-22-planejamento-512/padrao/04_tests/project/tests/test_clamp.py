import pytest
from clamp import clamp

def test_value_below_interval():
    assert clamp(-1, 0, 10) == 0

def test_value_within_interval():
    assert clamp(5, 0, 10) == 5

def test_value_above_interval():
    assert clamp(15, 0, 10) == 10