from codesnap.cleaner import clean_code_text


def test_clean_preserves_numbers_and_identifiers():
    code = "x = 100 + col0\nstep1 = calculate(sha256, utf8)\nitems = [0, 1, 2, 3, 4, 5, 8]"
    cleaned = clean_code_text(code)
    # Numbers and valid variable names with digits must NOT be corrupted!
    assert "100" in cleaned
    assert "col0" in cleaned
    assert "step1" in cleaned
    assert "sha256" in cleaned
    assert "utf8" in cleaned
    assert "[0, 1, 2, 3, 4, 5, 8]" in cleaned


def test_clean_fixes_common_ocr_errors():
    code = "det foo():\n    priot('hello')\n    retum 42\ne1se:\n    pass\n"
    cleaned = clean_code_text(code)
    assert "def foo():" in cleaned
    assert "print('hello')" in cleaned
    assert "return 42" in cleaned
    assert "else:" in cleaned


def test_clean_fixes_stray_ocr_margin_pipes():
    code = "| def example():\n|     return True"
    cleaned = clean_code_text(code)
    assert cleaned.startswith("def example():")
    assert "return True" in cleaned


def test_clean_does_not_corrupt_uppercase_constants():
    code = "SELECT id, name FROM users WHERE active = TRUE"
    cleaned = clean_code_text(code)
    # SQL uppercase keywords should be preserved, not forced to lowercase
    assert "FROM" in cleaned
    assert "TRUE" in cleaned
