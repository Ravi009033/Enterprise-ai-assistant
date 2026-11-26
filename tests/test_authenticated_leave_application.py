
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.models.leave_request import LeaveRequest
from backend.app.core.security import hash_password
from backend.app.core.jwt import create_access_token


client = TestClient(app)
db = SessionLocal()

try:
    # Create temporary employee.
    employee = Employee(
        employee_id="LEAVETEST01",
        name="Leave Test Employee",
        total_leaves=20,
        used_leaves=5,
    )

    db.add(employee)
    db.commit()

    # Create authenticated employee account.
    user = User(
        username="leavetest01",
        hashed_password=hash_password("TestPass123"),
        employee_id="LEAVETEST01",
        role="employee",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "employee_id": user.employee_id,
    })

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Step 1: Request leave.
    first_response = client.post(
        "/api/chat",
        headers=headers,
        json={
            "question": "Apply for 2 days of leave because of personal work.",
            "session_id": "authenticated-leave-test",
            "history": [],
        },
    )

    assert first_response.status_code == 200, first_response.text

    first_result = first_response.json()

    assert first_result["status"] == "awaiting_confirmation"
    assert "YES" in first_result["answer"]

    print("\nLeave confirmation preview passed!")
    print(first_result["answer"])

    # Step 2: Confirm leave application.
    second_response = client.post(
        "/api/chat",
        headers=headers,
        json={
            "question": "YES",
            "session_id": "authenticated-leave-test",
            "history": [
                {
                    "role": "user",
                    "content": "Apply for 2 days of leave because of personal work.",
                },
                {
                    "role": "assistant",
                    "content": first_result["answer"],
                },
            ],
        },
    )

    assert second_response.status_code == 200, second_response.text

    second_result = second_response.json()

    assert second_result["status"] == "success"
    assert "submitted successfully" in second_result["answer"].lower()

    print("\nLeave submission passed!")
    print(second_result["answer"])

    # Step 3: Verify database record.
    leave_request = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == "LEAVETEST01"
        )
        .first()
    )

    assert leave_request is not None
    assert leave_request.days == 2
    assert leave_request.status == "pending"

    print("\nDatabase verification passed!")
    print("Employee ID:", leave_request.employee_id)
    print("Leave days:", leave_request.days)
    print("Status:", leave_request.status)

finally:
    # Remove only temporary test records.
    db.rollback()

    test_user = db.query(User).filter(
        User.username == "leavetest01"
    ).first()

    if test_user:
        db.delete(test_user)

    test_requests = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == "LEAVETEST01"
    ).all()

    for request in test_requests:
        db.delete(request)

    test_employee = db.get(Employee, "LEAVETEST01")

    if test_employee:
        db.delete(test_employee)

    db.commit()
    db.close()

    print("\nTemporary test data cleaned up.")
