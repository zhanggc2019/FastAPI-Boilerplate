from app.core.security.password import PasswordHandler


def test_password_hashing():
    hashed_password = PasswordHandler.hash("password")
    assert isinstance(hashed_password, str)
    assert hashed_password != ""


def test_password_verification():
    password = "password"
    hashed_password = PasswordHandler.hash(password)
    assert PasswordHandler.verify(hashed_password, password)

    incorrect_password = "wrong_password"
    assert not PasswordHandler.verify(hashed_password, incorrect_password)
