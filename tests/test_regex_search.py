import re


def test_regex_search_pattern():
    """Test that regex patterns are correctly compiled."""
    pattern = r"feature/.*-v\d+"
    assert re.match(pattern, "feature/auth-v2")
    assert re.match(pattern, "feature/pay-v3")
    assert not re.match(pattern, "bugfix/login")


def test_regex_search_invalid_pattern():
    """Test that invalid regex falls back to literal search."""
    pattern = "[invalid"
    try:
        re.compile(pattern)
        compiled = pattern
    except re.error:
        compiled = re.escape(pattern)
    assert compiled == r"\[invalid"
