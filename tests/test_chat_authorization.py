
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.core.security import hash_password
from backend.app.core.jwt import create_access_token


client = TestClient(app)

db = SessionLocal()

try:
    # Create a temporary employee.
    employee = Employee(
        employee_id="CHATTEST01",
        name="Chat Test Employee",
        total_leaves=20,
        used_leaves=5,
    )

    db.add(employee)
    db.commit()

    # Create a temporary employee user.
    user = User(
        username="chattest01",
        hashed_password=hash_password("TestPass123"),
        employee_id="CHATTEST01",
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

    # Test 1: No authentication.
    response = client.post(
        "/api/chat",
        json={
            "question": "What is Python?",
            "session_id": "chat-test-01",
            "history": [],
        },
    )

    assert response.status_code == 401
    print("Unauthenticated chat test passed!")

    # Test 2: Authenticated employee.
    response = client.post(
        "/api/chat",
        headers=headers,
        json={
            "question": "What is Python?",
            "session_id": "chat-test-02",
            "history": [],
        },
    )

    assert response.status_code == 200, response.text
    print("Authenticated chat test passed!")
    print(response.json())

finally:
    db.rollback()

    test_user = db.query(User).filter(
        User.username == "chattest01"
    ).first()

    if test_user:
        db.delete(test_user)

    test_employee = db.get(Employee, "CHATTEST01")

    if test_employee:
        db.delete(test_employee)

    db.commit()
    db.close()
