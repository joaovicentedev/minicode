from words import word_count


def test_word_count_handles_whitespace():
    assert word_count("\t\n") == 0
    assert word_count("  um\t dois\ntrês  ") == 3
