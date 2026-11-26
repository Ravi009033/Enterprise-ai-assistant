
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.services.auth_service import create_user

client = TestClient(app)


def test_jwt_authentication():

    suffix = uuid4().hex[:8]
    employee_id = f"JWT{suffix.upper()}"
    username = f"jwt_employee_{suffix}"
    password = "SecurePassword123"

    db = SessionLocal()

    try:
        employee = Employee(
            employee_id=employee_id,
            name="JWT Test Employee",
            total_leaves=24,
            used_leaves=0,
        )

        db.add(employee)
        db.commit()

    finally:
        db.close()

    try:
        create_user(
            username=username,
            password=password,
            role="employee",
            employee_id=employee_id,
        )

        # Login and obtain token.
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": password,
            },
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        # Test 1: Access without token.
        response = client.get("/api/auth/me")

        assert response.status_code == 401

        print("\nMissing token rejection passed!")

        # Test 2: Access with invalid token.
        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": "Bearer invalid.token.value"
            },
        )

        assert response.status_code == 401

        print("Invalid token rejection passed!")

        # Test 3: Access with valid token.
        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200

        result = response.json()

        assert result["username"] == username
        assert result["employee_id"] == employee_id
        assert result["role"] == "employee"

        print("Valid token authentication passed!")

        # Test 4: Disabled account cannot use an existing token.
        db = SessionLocal()

        try:
            user = (
                db.query(User)
                .filter(User.username == username)
                .first()
            )

            user.is_active = False
            db.commit()

        finally:
            db.close()

        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 401

        print("Inactive account token rejection passed!")

        print("\nAll JWT authentication tests passed!")

    finally:
        db = SessionLocal()

        try:
            db.query(User).filter(
                User.username == username
            ).delete(synchronize_session=False)

            db.query(Employee).filter(
                Employee.employee_id == employee_id
            ).delete(synchronize_session=False)

            db.commit()

            print("Temporary test data cleaned up!")

        finally:
            db.close()


if __name__ == "__main__":
    test_jwt_authentication()
