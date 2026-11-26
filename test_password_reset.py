
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.password_reset import PasswordResetToken
from backend.app.core.security import hash_password
from backend.app.services.auth_service import create_password_reset_token


client = TestClient(app)

TEST_USERNAME = "password_reset_test"
OLD_PASSWORD = "OldPassword123"
NEW_PASSWORD = "RecoveredPassword456"


def cleanup_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.username == TEST_USERNAME
        ).first()

        if user:
            db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id
            ).delete(synchronize_session=False)

            db.delete(user)
            db.commit()
    finally:
        db.close()


def create_test_user():
    cleanup_user()

    db = SessionLocal()
    try:
        user = User(
            username=TEST_USERNAME,
            hashed_password=hash_password(OLD_PASSWORD),
            employee_id=None,
            role="hr",
            is_active=True,
            failed_login_attempts=3,
            locked_until=None,
        )

        db.add(user)
        db.commit()
    finally:
        db.close()


def test_password_reset():
    cleanup_user()
    create_test_user()

    try:
        # 1. Forgot password API
        response = client.post(
            "/api/auth/forgot-password",
            json={"username": TEST_USERNAME},
        )

        assert response.status_code == 200
        assert "message" in response.json()
        assert "token" not in response.json()

        print("Forgot password API test passed!")

        # 2. Unknown username should receive the same response
        response_unknown = client.post(
            "/api/auth/forgot-password",
            json={"username": "unknown_reset_user"},
        )

        assert response_unknown.status_code == 200
        assert response_unknown.json() == response.json()

        print("Account enumeration protection test passed!")

        # 3. Generate a token for testing
        raw_token = create_password_reset_token(TEST_USERNAME)

        assert raw_token is not None

        # 4. Invalid token
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": NEW_PASSWORD,
            },
        )

        assert response.status_code == 400

        print("Invalid token rejection test passed!")

        # 5. Successful password reset
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": raw_token,
                "new_password": NEW_PASSWORD,
            },
        )

        assert response.status_code == 200

        print("Successful password reset test passed!")

        # 6. Token reuse rejection
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": raw_token,
                "new_password": "AnotherPassword789",
            },
        )

        assert response.status_code == 400

        print("Single-use token test passed!")

        # 7. Verify login with old password fails
        response = client.post(
            "/api/auth/login",
            data={
                "username": TEST_USERNAME,
                "password": OLD_PASSWORD,
            },
        )

        assert response.status_code == 401

        print("Old password rejection test passed!")

        # 8. Verify login with new password works
        response = client.post(
            "/api/auth/login",
            data={
                "username": TEST_USERNAME,
                "password": NEW_PASSWORD,
            },
        )

        assert response.status_code == 200

        print("New password login test passed!")

        # 9. Verify login lockout counters were reset
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == TEST_USERNAME
            ).first()

            assert user.failed_login_attempts == 0
            assert user.locked_until is None
        finally:
            db.close()

        print("Login lockout reset test passed!")

        # 10. Expired token test
        expired_token = create_password_reset_token(TEST_USERNAME)

        token_hash = hashlib.sha256(
            expired_token.encode("utf-8")
        ).hexdigest()

        db = SessionLocal()
        try:
            reset_record = db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash == token_hash
            ).first()

            reset_record.expires_at = (
                datetime.now(timezone.utc) - timedelta(minutes=1)
            )

            db.commit()
        finally:
            db.close()

        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": expired_token,
                "new_password": "ExpiredPassword789",
            },
        )

        assert response.status_code == 400

        print("Expired token rejection test passed!")

        # 11. Short password validation
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "any-token",
                "new_password": "short",
            },
        )

        assert response.status_code == 422

        print("Short password validation test passed!")

    finally:
        cleanup_user()
        print("Temporary test data cleaned up.")


if __name__ == "__main__":
    test_password_reset()

