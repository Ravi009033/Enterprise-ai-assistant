
from backend.app.core.security import (
    hash_password,
    verify_password,
)


def test_password_security():

    password = "MySecurePassword123"

    # Generate password hash.
    hashed_password = hash_password(password)

    print("Generated password hash:")
    print(hashed_password)

    # Original password should not equal hash.
    assert password != hashed_password

    # Correct password should verify.
    assert verify_password(password, hashed_password)

    # Incorrect password should fail.
    assert not verify_password(
        "WrongPassword123",
        hashed_password,
    )

    print("\nPassword hashing test passed!")
    print("Correct password verification passed!")
    print("Incorrect password verification passed!")


if __name__ == "__main__":
    test_password_security()
