
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.services.auth_service import create_user
from backend.app.core.jwt import decode_access_token

client = TestClient(app)


def test_auth_api():

    suffix = uuid4().hex[:8]
    employee_id = f"API{suffix.upper()}"
    username = f"api_employee_{suffix}"
    password = "TestPassword123"

    db = SessionLocal()

    try:
        employee = Employee(
            employee_id=employee_id,
            name="API Authentication Test",
            total_leaves=24,
            used_leaves=0,
        )

        db.add(employee)
        db.commit()

    finally:
        db.close()

    try:
        # Create temporary login account.
        create_user(
            username=username,
            password=password,
            role="employee",
            employee_id=employee_id,
        )

        # Test 1: Successful login.
        response = client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": password,
            },
        )

        assert response.status_code == 200

        result = response.json()

        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["user"]["role"] == "employee"

        print("\nSuccessful login API test passed!")

        # Test 2: Verify returned JWT.
        decoded = decode_access_token(
            result["access_token"]
        )

        assert decoded is not None
        assert decoded["username"] == username
        assert decoded["role"] == "employee"
        assert decoded["employee_id"] == employee_id

        print("JWT identity verification passed!")

        # Test 3: Incorrect password.
        response = client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401

        print("Incorrect password API test passed!")

        # Test 4: Unknown username.
        response = client.post(
            "/api/auth/login",
            data={
                "username": "unknown_user",
                "password": "SomePassword123",
            },
        )

        assert response.status_code == 401

        print("Unknown username API test passed!")

        print("\nAll authentication API tests passed!")

    finally:
        # Clean up only temporary test data.
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
    test_auth_api()
