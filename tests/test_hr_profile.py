
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.employee import Employee
from backend.app.core.security import hash_password
from backend.app.core.jwt import create_access_token
import uuid


client = TestClient(app)
db = SessionLocal()

suffix = uuid.uuid4().hex[:8]

employee_id = f"HRPROF{suffix}"
employee_username = f"employee_{suffix}"
hr_username = f"hr_{suffix}"

try:
    # Create a temporary employee record.
    employee = Employee(
        employee_id=employee_id,
        name="HR Profile Test Employee",
        total_leaves=20,
        used_leaves=5,
    )

    db.add(employee)
    db.commit()

    # Create an employee user.
    employee_user = User(
        username=employee_username,
        hashed_password=hash_password("TestPass123"),
        employee_id=employee_id,
        role="employee",
        is_active=True,
    )

    # Create an HR user.
    hr_user = User(
        username=hr_username,
        hashed_password=hash_password("TestPass123"),
        employee_id=None,
        role="hr",
        is_active=True,
    )

    db.add_all([employee_user, hr_user])
    db.commit()

    db.refresh(employee_user)
    db.refresh(hr_user)

    # Generate employee JWT.
    employee_token = create_access_token({
        "sub": str(employee_user.id),
        "username": employee_user.username,
        "role": employee_user.role,
        "employee_id": employee_user.employee_id,
    })

    # Generate HR JWT.
    hr_token = create_access_token({
        "sub": str(hr_user.id),
        "username": hr_user.username,
        "role": hr_user.role,
        "employee_id": hr_user.employee_id,
    })

    employee_headers = {
        "Authorization": f"Bearer {employee_token}"
    }

    hr_headers = {
        "Authorization": f"Bearer {hr_token}"
    }

    # Test 1: Unauthenticated access.
    response = client.get("/api/hr/profile")

    assert response.status_code == 401

    print("Unauthenticated access test passed!")

    # Test 2: HR accesses own profile.
    response = client.get(
        "/api/hr/profile",
        headers=hr_headers,
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["user_id"] == hr_user.id
    assert result["username"] == hr_username
    assert result["role"] == "hr"
    assert result["account_status"] == "active"

    print("HR profile access test passed!")
    print(result)

    # Test 3: Employee tries to access HR profile.
    response = client.get(
        "/api/hr/profile",
        headers=employee_headers,
    )

    assert response.status_code == 403

    print("Employee access prevention test passed!")

finally:
    # Clean up temporary test data.
    db.rollback()

    db.query(User).filter(
        User.username.in_([
            employee_username,
            hr_username,
        ])
    ).delete(synchronize_session=False)

    db.query(Employee).filter(
        Employee.employee_id == employee_id
    ).delete(synchronize_session=False)

    db.commit()
    db.close()

    print("Temporary test data cleaned up.")
