
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
    employee = Employee(
        employee_id="TOOLTEST01",
        name="Tool Test Employee",
        total_leaves=20,
        used_leaves=5,
    )

    db.add(employee)
    db.commit()

    user = User(
        username="tooltest01",
        hashed_password=hash_password("TestPass123"),
        employee_id="TOOLTEST01",
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

    response = client.post(
        "/api/chat",
        headers=headers,
        json={
            "question": "What is my remaining leave balance?",
            "session_id": "authenticated-tool-test",
            "history": [],
        },
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["status"] == "success"
    assert "15 days" in result["answer"]

    print("Authenticated employee tool test passed!")
    print(result)

finally:
    db.rollback()

    test_user = db.query(User).filter(
        User.username == "tooltest01"
    ).first()

    if test_user:
        db.delete(test_user)

    test_employee = db.get(Employee, "TOOLTEST01")

    if test_employee:
        db.delete(test_employee)

    db.commit()
    db.close()
