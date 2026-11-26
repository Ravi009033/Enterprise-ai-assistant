
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.password_reset import PasswordResetToken
from backend.app.core.security import hash_password
from backend.app.core.jwt import create_access_token
from backend.app.services.auth_service import create_password_reset_token


client = TestClient(app)

TEST_USERNAME = "token_revocation_test"
OLD_PASSWORD = "OldPassword123"
CHANGED_PASSWORD = "ChangedPassword456"
RESET_PASSWORD = "ResetPassword789"


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
            failed_login_attempts=0,
            token_version=0,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "employee_id": user.employee_id,
            "token_version": user.token_version,
        })

        return token
    finally:
        db.close()


def test_token_revocation():
    cleanup_user()

    try:
        # Create user and initial JWT.
        old_token = create_test_user()

        old_headers = {
            "Authorization": f"Bearer {old_token}"
        }

        # 1. Initial JWT should work.
        response = client.get(
            "/api/auth/me",
            headers=old_headers,
        )

        assert response.status_code == 200
        print("Initial JWT authentication test passed!")

        # 2. Change password.
        response = client.post(
            "/api/auth/change-password",
            headers=old_headers,
            json={
                "current_password": OLD_PASSWORD,
                "new_password": CHANGED_PASSWORD,
            },
        )

        assert response.status_code == 200
        print("Password change test passed!")

        # 3. Old JWT must now be rejected.
        response = client.get(
            "/api/auth/me",
            headers=old_headers,
        )

        assert response.status_code == 401
        print("JWT revocation after password change passed!")

        # 4. Login with changed password.
        response = client.post(
            "/api/auth/login",
            data={
                "username": TEST_USERNAME,
                "password": CHANGED_PASSWORD,
            },
        )

        assert response.status_code == 200

        current_token = response.json()["access_token"]

        current_headers = {
            "Authorization": f"Bearer {current_token}"
        }

        print("Login after password change passed!")

        # 5. Generate a password reset token.
        reset_token = create_password_reset_token(
            TEST_USERNAME
        )

        assert reset_token is not None

        # 6. Reset password.
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": RESET_PASSWORD,
            },
        )

        assert response.status_code == 200
        print("Password reset test passed!")

        # 7. JWT issued before reset must be rejected.
        response = client.get(
            "/api/auth/me",
            headers=current_headers,
        )

        assert response.status_code == 401
        print("JWT revocation after password reset passed!")

        # 8. Login with recovered password.
        response = client.post(
            "/api/auth/login",
            data={
                "username": TEST_USERNAME,
                "password": RESET_PASSWORD,
            },
        )

        assert response.status_code == 200

        new_token = response.json()["access_token"]

        # 9. New JWT should work.
        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {new_token}"
            },
        )

        assert response.status_code == 200
        print("New JWT authentication test passed!")

        # 10. Verify database token version.
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == TEST_USERNAME
            ).first()

            assert user.token_version == 2
        finally:
            db.close()

        print("Database token version test passed!")

    finally:
        cleanup_user()
        print("Temporary test data cleaned up.")


if __name__ == "__main__":
    test_token_revocation()
