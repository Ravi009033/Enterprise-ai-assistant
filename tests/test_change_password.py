
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import hash_password
from backend.app.core.jwt import create_access_token


client = TestClient(app)

TEST_USERNAME = "password_change_test"
TEST_PASSWORD = "OldPassword123"
NEW_PASSWORD = "NewPassword456"


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


def create_test_user():
    cleanup_user()

    db = SessionLocal()
    try:
        user = User(
            username=TEST_USERNAME,
            hashed_password=hash_password(TEST_PASSWORD),
            employee_id=None,
            role="hr",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id

        token = create_access_token({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "employee_id": user.employee_id,
            "token_version": user.token_version,
        })

        return user_id, token
    finally:
        db.close()


def test_change_password():
    cleanup_user()
    user_id, token = create_test_user()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 1. Unauthenticated request
    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": TEST_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 401
    print("Unauthenticated password change test passed!")

    # 2. Incorrect current password
    response = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": "WrongPassword123",
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 400
    print("Incorrect current password test passed!")

    # 3. Same old and new password
    response = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": TEST_PASSWORD,
            "new_password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 400
    print("Same password rejection test passed!")

    # 4. Successful password change
    response = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": TEST_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 200
    print("Successful password change test passed!")

    # 5. Old password should no longer work
    response = client.post(
        "/api/auth/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401
    print("Old password rejection test passed!")

   
    # 6. New password should work
    response = client.post(
        "/api/auth/login",
        data={
            "username": TEST_USERNAME,
            "password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 200

    new_token = response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {new_token}"
    }

    print("New password login test passed!")
    # 7. Short password validation
    response = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={
            "current_password": NEW_PASSWORD,
            "new_password": "short",
        },
    )

    assert response.status_code == 422
    print("Short password validation test passed!")

    cleanup_user()


if __name__ == "__main__":
    try:
        test_change_password()
    finally:
        cleanup_user()
        print("Temporary test data cleaned up.")
