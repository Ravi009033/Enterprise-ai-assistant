
from datetime import datetime, timedelta, timezone

from jose import jwt

from backend.app.core.jwt import (
    create_access_token,
    decode_access_token,
)
from backend.app.config import settings


def test_jwt():

    # Test 1: Generate JWT token.
    user_data = {
        "sub": "test_user_001",
        "username": "test_employee",
        "role": "employee",
    }

    token = create_access_token(user_data)

    assert isinstance(token, str)
    assert len(token) > 0

    print("\nJWT token generation passed!")

    # Test 2: Decode a valid token.
    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "test_user_001"
    assert decoded["username"] == "test_employee"
    assert decoded["role"] == "employee"
    assert "exp" in decoded

    print("Valid JWT decoding passed!")

    # Test 3: Invalid token.
    invalid_token = decode_access_token("invalid.token.value")

    assert invalid_token is None

    print("Invalid JWT rejection passed!")

    # Test 4: Expired token.
    expired_payload = {
        "sub": "test_user_001",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    expired_result = decode_access_token(expired_token)

    assert expired_result is None

    print("Expired JWT rejection passed!")

    print("\nAll JWT tests passed!")


if __name__ == "__main__":
    test_jwt()
