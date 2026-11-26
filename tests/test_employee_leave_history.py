
import uuid

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

suffix = uuid.uuid4().hex[:8]

employee1_id = f"HISTORY1{suffix}"
employee2_id = f"HISTORY2{suffix}"

username1 = f"history1_{suffix}"
username2 = f"history2_{suffix}"

try:
    # Create two temporary employees.
    employee1 = Employee(
        employee_id=employee1_id,
        name="History Test Employee 1",
        total_leaves=20,
        used_leaves=0,
    )

    employee2 = Employee(
        employee_id=employee2_id,
        name="History Test Employee 2",
        total_leaves=20,
        used_leaves=0,
    )

    db.add_all([employee1, employee2])
    db.commit()

    # Create employee accounts.
    user1 = User(
        username=username1,
        hashed_password=hash_password("TestPass123"),
        employee_id=employee1_id,
        role="employee",
        is_active=True,
    )

    user2 = User(
        username=username2,
        hashed_password=hash_password("TestPass123"),
        employee_id=employee2_id,
        role="employee",
        is_active=True,
    )

    db.add_all([user1, user2])
    db.commit()
    db.refresh(user1)
    db.refresh(user2)

    # Create leave requests for employee 1.
    request1 = LeaveRequest(
        employee_id=employee1_id,
        days=2,
        reason="Personal work",
        status="pending",
    )

    request2 = LeaveRequest(
        employee_id=employee1_id,
        days=1,
        reason="Family function",
        status="approved",
    )

    # Create a leave request for employee 2.
    request3 = LeaveRequest(
        employee_id=employee2_id,
        days=3,
        reason="Vacation",
        status="pending",
    )

    db.add_all([request1, request2, request3])
    db.commit()

    # Generate JWT tokens.
    token1 = create_access_token({
        "sub": str(user1.id),
        "username": user1.username,
        "role": user1.role,
        "employee_id": user1.employee_id,
    })

    token2 = create_access_token({
        "sub": str(user2.id),
        "username": user2.username,
        "role": user2.role,
        "employee_id": user2.employee_id,
    })

    headers1 = {
        "Authorization": f"Bearer {token1}"
    }

    headers2 = {
        "Authorization": f"Bearer {token2}"
    }

    # Test 1: Unauthenticated access.
    response = client.get("/api/employee/leave-requests")

    assert response.status_code == 401

    print("Unauthenticated access test passed!")

    # Test 2: Employee 1 sees only their own requests.
    response1 = client.get(
        "/api/employee/leave-requests",
        headers=headers1,
    )

    assert response1.status_code == 200, response1.text

    history1 = response1.json()

    assert len(history1) == 2
    assert all(
        item["employee_id"] == employee1_id
        for item in history1
    )

    print("Employee 1 history test passed!")
    print(history1)

    # Test 3: Employee 2 sees only their own request.
    response2 = client.get(
        "/api/employee/leave-requests",
        headers=headers2,
    )

    assert response2.status_code == 200, response2.text

    history2 = response2.json()

    assert len(history2) == 1
    assert history2[0]["employee_id"] == employee2_id
    assert history2[0]["reason"] == "Vacation"

    print("Employee 2 isolation test passed!")
    print(history2)

    # Test 4: Empty history for a new employee.
    # Employee 2 has a request, so this test is covered
    # separately in the next test step if needed.

finally:
    # Clean up only temporary test records.
    db.rollback()

    db.query(LeaveRequest).filter(
        LeaveRequest.employee_id.in_([
            employee1_id,
            employee2_id,
        ])
    ).delete(synchronize_session=False)

    db.query(User).filter(
        User.username.in_([
            username1,
            username2,
        ])
    ).delete(synchronize_session=False)

    db.query(Employee).filter(
        Employee.employee_id.in_([
            employee1_id,
            employee2_id,
        ])
    ).delete(synchronize_session=False)

    db.commit()
    db.close()

    print("Temporary test data cleaned up.")
