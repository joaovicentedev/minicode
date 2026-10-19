from names import normalize_name


def test_normalize_name():
    assert normalize_name("  Ana   Maria  ") == "Ana Maria"
