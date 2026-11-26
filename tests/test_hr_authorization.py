
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.models.leave_request import LeaveRequest
from backend.app.services.auth_service import create_user

client = TestClient(app)


def get_token(username, password):

    response = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_hr_authorization():

    suffix = uuid4().hex[:8]

    employee_id = f"ROLE{suffix.upper()}"
    employee_username = f"employee_{suffix}"
    hr_username = f"hr_{suffix}"

    employee_password = "EmployeePass123"
    hr_password = "HRPassword123"

    db = SessionLocal()

    try:
        employee = Employee(
            employee_id=employee_id,
            name="Role Test Employee",
            total_leaves=10,
            used_leaves=0,
        )

        leave_request = LeaveRequest(
            employee_id=employee_id,
            days=2,
            reason="Personal work",
            status="pending",
        )

        db.add(employee)
        db.add(leave_request)
        db.commit()

        request_id = leave_request.id

    finally:
        db.close()

    try:
        # Create employee and HR accounts.
        create_user(
            username=employee_username,
            password=employee_password,
            role="employee",
            employee_id=employee_id,
        )

        create_user(
            username=hr_username,
            password=hr_password,
            role="hr",
        )

        employee_token = get_token(
            employee_username,
            employee_password,
        )

        hr_token = get_token(
            hr_username,
            hr_password,
        )

        employee_headers = {
            "Authorization": f"Bearer {employee_token}"
        }

        hr_headers = {
            "Authorization": f"Bearer {hr_token}"
        }

        # Test 1: Employee cannot view HR requests.
        response = client.get(
            "/api/hr/leave-requests",
            headers=employee_headers,
        )

        assert response.status_code == 403

        print("\nEmployee cannot view HR requests!")

        # Test 2: Employee cannot approve.
        response = client.post(
            f"/api/hr/leave-requests/{request_id}/approve",
            headers=employee_headers,
        )

        assert response.status_code == 403

        print("Employee cannot approve leave!")

        # Test 3: Employee cannot reject.
        response = client.post(
            f"/api/hr/leave-requests/{request_id}/reject",
            headers=employee_headers,
        )

        assert response.status_code == 403

        print("Employee cannot reject leave!")

        # Test 4: HR can view pending requests.
        response = client.get(
            "/api/hr/leave-requests",
            headers=hr_headers,
        )

        assert response.status_code == 200

        assert any(
            item["request_id"] == request_id
            for item in response.json()
        )

        print("HR can view pending requests!")

        # Test 5: HR can approve leave.
        response = client.post(
            f"/api/hr/leave-requests/{request_id}/approve",
            headers=hr_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"

        print("HR can approve leave!")

        print("\nAll HR authorization tests passed!")

    finally:
        # Clean up temporary records.
        db = SessionLocal()

        try:
            db.query(User).filter(
                User.username.in_([
                    employee_username,
                    hr_username,
                ])
            ).delete(synchronize_session=False)

            db.query(LeaveRequest).filter(
                LeaveRequest.employee_id == employee_id
            ).delete(synchronize_session=False)

            db.query(Employee).filter(
                Employee.employee_id == employee_id
            ).delete(synchronize_session=False)

            db.commit()

            print("Temporary test data cleaned up!")

        finally:
            db.close()


if __name__ == "__main__":
    test_hr_authorization()
