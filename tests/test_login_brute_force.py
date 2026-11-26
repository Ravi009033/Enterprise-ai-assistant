
from datetime import datetime, timedelta, timezone
import uuid

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import hash_password


client = TestClient(app)
db = SessionLocal()

username = f"bruteforce_{uuid.uuid4().hex[:8]}"
password = "CorrectPass123"

try:
    # Create temporary HR account.
    user = User(
        username=username,
        hashed_password=hash_password(password),
        employee_id=None,
        role="hr",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Test 1: Two incorrect attempts.
    for attempt in range(2):
        response = client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401

    print("Incorrect password attempts test passed!")

    # Test 2: Successful login resets failed attempts.
    response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    db.refresh(user)

    assert user.failed_login_attempts == 0
    assert user.locked_until is None

    print("Successful login reset test passed!")

    # Test 3: Five consecutive incorrect attempts.
    for attempt in range(5):
        response = client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401

    db.refresh(user)

    assert user.failed_login_attempts == 5
    assert user.locked_until is not None

    print("Five-attempt account lockout test passed!")

    # Test 4: Correct password must not bypass active lock.
    response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 401

    print("Locked account rejection test passed!")

    # Test 5: Simulate expiration of the lock period.
    user.locked_until = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    )
    db.commit()

    response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    db.refresh(user)

    assert user.failed_login_attempts == 0
    assert user.locked_until is None

    print("Login recovery after lock expiration test passed!")

finally:
    db.rollback()

    db.query(User).filter(
        User.username == username
    ).delete(synchronize_session=False)

    db.commit()
    db.close()

    print("Temporary test data cleaned up.")
