
from datetime import datetime, timedelta, timezone
import uuid

from fastapi.testclient import TestClient
from jose import jwt

from backend.app.main import app
from backend.app.config import settings
from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import hash_password
from backend.app.core.jwt import create_access_token


client = TestClient(app)
db = SessionLocal()

username = f"security_{uuid.uuid4().hex[:8]}"

try:
    # Create a temporary HR user.
    user = User(
        username=username,
        hashed_password=hash_password("TestPass123"),
        employee_id=None,
        role="hr",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate a valid token.
    valid_token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "employee_id": None,
        "token_version": user.token_version,
    })

    # Generate an expired token.
    expired_payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        "token_version": user.token_version,
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    # Test 1: Malformed token.
    response = client.get(
        "/api/hr/profile",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401

    print("Malformed token test passed!")

    # Test 2: Expired token.
    response = client.get(
        "/api/hr/profile",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401

    print("Expired token test passed!")

    # Test 3: Valid token.
    response = client.get(
        "/api/hr/profile",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 200, response.text

    print("Valid token test passed!")

    # Test 4: Disable the user account.
    user.is_active = False
    db.commit()

    response = client.get(
        "/api/hr/profile",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 401

    print("Disabled account token rejection test passed!")

finally:
    db.rollback()

    db.query(User).filter(
        User.username == username
    ).delete(synchronize_session=False)

    db.commit()
    db.close()

    print("Temporary test data cleaned up.")
