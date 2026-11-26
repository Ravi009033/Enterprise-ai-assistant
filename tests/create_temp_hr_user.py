
import uuid

from backend.app.db.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import hash_password
from backend.app.models.employee import Employee


username = f"temp_hr_{uuid.uuid4().hex[:8]}"
password = "TempHR@2026"

db = SessionLocal()

try:
    user = User(
        username=username,
        hashed_password=hash_password(password),
        employee_id=None,
        role="hr",
        is_active=True,
        failed_login_attempts=0,
        token_version=0,
    )

    db.add(user)
    db.commit()

    print("\nTemporary HR account created!")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("Role: HR")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
