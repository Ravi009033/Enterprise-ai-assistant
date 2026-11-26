
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.services.auth_service import create_user

client = TestClient(app)


def test_employee_authorization():

    suffix = uuid4().hex[:8]
    employee_id = f"EMP{suffix.upper()}"
    username = f"employee_{suffix}"
    password = "EmployeePass123"

    db = SessionLocal()

    try:
        employee = Employee(
            employee_id=employee_id,
            name="Employee API Test",
            total_leaves=24,
            used_leaves=8,
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

        # Login.
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": username,
                "password": password,
            },
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        # Test 1: Access without token.
        response = client.get(
            "/api/employee/leave-balance"
        )

        assert response.status_code == 401

        print("\nUnauthenticated access rejected!")

        # Test 2: Access with valid employee token.
        response = client.get(
            "/api/employee/leave-balance",
            headers=headers,
        )

        assert response.status_code == 200

        result = response.json()

        assert result["employee_id"] == employee_id
        assert result["remaining_leaves"] == 16

        print("Employee can access own leave balance!")

        print("\nAll employee authorization tests passed!")

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
    test_employee_authorization()
