from names import normalize_name


def test_normalize_name_handles_tabs_and_plain_names():
    assert normalize_name("  João\t  Silva ") == "João Silva"
    assert normalize_name("Lia") == "Lia"
