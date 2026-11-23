from clamp import clamp


def test_clamp_basic():
    assert clamp(5, 0, 10) == 5
