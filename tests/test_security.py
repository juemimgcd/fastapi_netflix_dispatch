from utils.security import hash_password, verify_password


def test_hash_password_and_verify_round_trip():
    password = "12345678"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False
