
import uuid

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.core.security import hash_password
from backend.app.core.jwt import create_access_token


client = TestClient(app)
db = SessionLocal()

suffix = uuid.uuid4().hex[:8]

employee_id = f"PROFILE{suffix}"
username = f"profile_{suffix}"

try:
    # Create temporary employee.
    employee = Employee(
        employee_id=employee_id,
        name="Profile Test Employee",
        total_leaves=20,
        used_leaves=5,
    )

    db.add(employee)
    db.commit()

    # Create employee account.
    user = User(
        username=username,
        hashed_password=hash_password("TestPass123"),
        employee_id=employee_id,
        role="employee",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate JWT token.
    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "employee_id": user.employee_id,
    })

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Test 1: Unauthenticated access.
    response = client.get("/api/employee/profile")

    assert response.status_code == 401

    print("Unauthenticated access test passed!")

    # Test 2: Authenticated employee profile.
    response = client.get(
        "/api/employee/profile",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["employee_id"] == employee_id
    assert result["name"] == "Profile Test Employee"
    assert result["total_leaves"] == 20
    assert result["used_leaves"] == 5
    assert result["remaining_leaves"] == 15

    print("Employee profile test passed!")
    print(result)

finally:
    # Clean up temporary test data.
    db.rollback()

    db.query(User).filter(
        User.username == username
    ).delete(synchronize_session=False)

    db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).delete(synchronize_session=False)

    db.commit()
    db.close()

    print("Temporary test data cleaned up.")
