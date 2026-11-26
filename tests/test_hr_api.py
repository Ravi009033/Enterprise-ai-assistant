
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.leave_request import LeaveRequest

client = TestClient(app)


def test_hr_api():

    employee_id = f"API{uuid4().hex[:10].upper()}"

    db = SessionLocal()

    try:
        employee = Employee(
            employee_id=employee_id,
            name="HR API Test Employee",
            total_leaves=10,
            used_leaves=0,
        )

        request_one = LeaveRequest(
            employee_id=employee_id,
            days=3,
            reason="Personal work",
            status="pending",
        )

        request_two = LeaveRequest(
            employee_id=employee_id,
            days=2,
            reason="Family function",
            status="pending",
        )

        db.add(employee)
        db.add_all([request_one, request_two])
        db.commit()

        request_one_id = request_one.id
        request_two_id = request_two.id

    finally:
        db.close()

    try:
        # Test 1: Get pending requests
        response = client.get("/api/hr/leave-requests")

        assert response.status_code == 200
        assert any(
            item["request_id"] == request_one_id
            for item in response.json()
        )

        print("\nGET pending requests passed!")

        # Test 2: Approve request
        response = client.post(
            f"/api/hr/leave-requests/{request_one_id}/approve"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"

        print("POST approve request passed!")

        # Test 3: Reject request
        response = client.post(
            f"/api/hr/leave-requests/{request_two_id}/reject"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

        print("POST reject request passed!")

        print("\nAll HR API tests passed!")

    finally:
        db = SessionLocal()

        try:
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
    test_hr_api()
