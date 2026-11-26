
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import hash_password


client = TestClient(app)

TEST_USERNAME = "logout_test_user"
TEST_PASSWORD = "LogoutPassword123"


def cleanup_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.username == TEST_USERNAME
        ).first()

        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_logout():
    cleanup_user()

    try:
        db = SessionLocal()
        try:
            user = User(
                username=TEST_USERNAME,
                hashed_password=hash_password(TEST_PASSWORD),
                employee_id=None,
                role="hr",
                is_active=True,
                failed_login_attempts=0,
                token_version=0,
            )
            db.add(user)
            db.commit()
        finally:
            db.close()

        # Login
        response = client.post(
            "/api/auth/login",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
            },
        )
        assert response.status_code == 200

        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login test passed!")

        # Verify JWT before logout
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        print("Authentication before logout passed!")

        # Logout
        response = client.post("/api/auth/logout", headers=headers)
        assert response.status_code == 200
        print("Logout API test passed!")

        # Old JWT must now fail
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
        print("JWT revocation after logout passed!")

        # Verify database version
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == TEST_USERNAME
            ).first()
            assert user.token_version == 1
        finally:
            db.close()

        print("Database token version test passed!")

    finally:
        cleanup_user()
        print("Temporary test data cleaned up.")


if __name__ == "__main__":
    test_logout()
