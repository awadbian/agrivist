from backend.service.signup_validation import validate_signup


def test_signup_valid_input():
    errors = validate_signup(
        "Bian Awad",
        "bian@gmail.com",
        "12345678",
        "12345678",
        True
    )
    assert errors == {}


def test_signup_empty_full_name():
    errors = validate_signup(
        "",
        "bian@gmail.com",
        "12345678",
        "12345678",
        True
    )
    assert "full_name" in errors


def test_signup_empty_email():
    errors = validate_signup(
        "Bian Awad",
        "",
        "12345678",
        "12345678",
        True
    )
    assert "email" in errors


def test_signup_invalid_email():
    errors = validate_signup(
        "Bian Awad",
        "biangmail.com",
        "12345678",
        "12345678",
        True
    )
    assert "email" in errors


def test_signup_short_password():
    errors = validate_signup(
        "Bian Awad",
        "bian@gmail.com",
        "123",
        "123",
        True
    )
    assert "password" in errors


def test_signup_password_mismatch():
    errors = validate_signup(
        "Bian Awad",
        "bian@gmail.com",
        "12345678",
        "65432178",
        True
    )
    assert "confirm_password" in errors or "password" in errors


def test_signup_terms_not_checked():
    errors = validate_signup(
        "Bian Awad",
        "bian@gmail.com",
        "12345678",
        "12345678",
        False
    )
    assert "terms" in errors
