from codesnap.formatters import format_code


def test_format_python_code():
    raw_python = "def add(x,y):\n    return x+y\n"
    formatted = format_code(raw_python, lang="python")
    # Should be properly formatted with spaces after commas and operators
    assert "def add(x, y):" in formatted
    assert "return x + y" in formatted


def test_format_python_syntax_error_fallback():
    # Incomplete syntax should not raise an exception; it falls back safely to original text
    incomplete = "def broken(:"
    formatted = format_code(incomplete, lang="python")
    assert formatted == incomplete


def test_format_non_python_passthrough():
    js_code = "const x = 10;"
    assert format_code(js_code, lang="javascript") == js_code
