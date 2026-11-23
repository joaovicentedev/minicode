#!/usr/bin/env python
import pytest
from clamp import clamp

class TestClamp:
    def test_value_within_interval(self):
        # Test when the value is within the interval
        assert clamp(5, 0, 10) == 5

    def test_value_below_interval(self):
        # Test when the value is below the interval
        assert clamp(-3, 0, 10) == 0

    def test_value_above_interval(self):
        # Test when the value is above the interval
        assert clamp(15, 0, 10) == 10