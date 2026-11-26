
from backend.app.db.database import SessionLocal
from backend.app.models import user
from backend.app.models.user import User
from backend.app.core.security import (
    hash_password,
    verify_password,
)
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from backend.app.models.password_reset import PasswordResetToken


def create_user(
    username: str,
    password: str,
    role: str = "employee",
    employee_id: str | None = None,
) -> dict:

    username = username.strip().lower()

    if not username:
        raise ValueError("Username cannot be empty")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")

    if role not in ["employee", "hr"]:
        raise ValueError("Invalid user role")

    if role == "employee" and not employee_id:
        raise ValueError("Employee ID is required")

    if role == "hr" and employee_id:
        raise ValueError("HR account cannot be linked to an employee")

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existing_user:
            raise ValueError("Username already exists")

        user = User(
            username=username,
            hashed_password=hash_password(password),
            employee_id=employee_id,
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "user_id": user.id,
            "username": user.username,
            "employee_id": user.employee_id,
            "role": user.role,
            "is_active": user.is_active,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


def authenticate_user(
    username: str,
    password: str,
) -> dict | None:

    username = username.strip().lower()

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if user is None:
            return None

        if not user.is_active:
            return None

        # Check whether the account is currently locked.
        if user.locked_until is not None:
            locked_until = user.locked_until

            # SQLite may return a naive datetime.
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(
                    tzinfo=timezone.utc
                )

            if datetime.now(timezone.utc) < locked_until:
                return None

            # Lock period has expired.
            user.locked_until = None
            user.failed_login_attempts = 0
            db.commit()

        # Verify password.
        if not verify_password(password, user.hashed_password):

            user.failed_login_attempts += 1

            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = (
                    datetime.now(timezone.utc)
                    + timedelta(minutes=LOCK_DURATION_MINUTES)
                )

            db.commit()
            return None

        # Successful login: reset failed attempts.
        user.failed_login_attempts = 0
        user.locked_until = None

        db.commit()

        return {
            "user_id": user.id,
            "username": user.username,
            "employee_id": user.employee_id,
            "role": user.role,
            "is_active": user.is_active,
            "token_version": user.token_version,
        }

    finally:
        db.close()



def change_user_password(
    user_id: int,
    current_password: str,
    new_password: str,
) -> bool:

    if len(new_password) < 8:
        raise ValueError("New password must contain at least 8 characters")

    if current_password == new_password:
        raise ValueError("New password must be different from current password")

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if user is None or not user.is_active:
            return False

        if not verify_password(
            current_password,
            user.hashed_password,
        ):
            return False

        user.hashed_password = hash_password(new_password)
        # Revoke all previously issued JWTs.
        user.token_version += 1

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



PASSWORD_RESET_EXPIRY_MINUTES = 15


def create_password_reset_token(username: str) -> str | None:
    username = username.strip().lower()

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.username == username,
            User.is_active == True,
        ).first()

        if user is None:
            return None

        # Generate a cryptographically secure random token.
        raw_token = secrets.token_urlsafe(32)

        # Store only its SHA-256 hash.
        token_hash = hashlib.sha256(
            raw_token.encode("utf-8")
        ).hexdigest()

        # Invalidate previous unused reset tokens.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        ).update(
            {"used_at": datetime.now(timezone.utc)},
            synchronize_session=False,
        )

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=PASSWORD_RESET_EXPIRY_MINUTES)
            ),
        )

        db.add(reset_record)
        db.commit()

        return raw_token

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def reset_user_password(
    raw_token: str,
    new_password: str,
) -> bool:

    if len(new_password) < 8:
        raise ValueError(
            "New password must contain at least 8 characters"
        )

    # Hash the token received from the user.
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    db = SessionLocal()

    try:
        reset_record = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()

        if reset_record is None:
            return False

        # Reject tokens that have already been used.
        if reset_record.used_at is not None:
            return False

        # SQLite may return timezone-naive datetimes.
        expires_at = reset_record.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if datetime.now(timezone.utc) >= expires_at:
            return False

        user = db.query(User).filter(
            User.id == reset_record.user_id
        ).first()

        if user is None or not user.is_active:
            return False

        user.hashed_password = hash_password(new_password)
        # Revoke all previously issued JWTs.
        user.token_version += 1
        # Reset login lockout counters after password recovery.
        user.failed_login_attempts = 0
        user.locked_until = None

        # Mark token as used.
        reset_record.used_at = datetime.now(timezone.utc)

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



def logout_user(user_id: int) -> bool:
    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if user is None or not user.is_active:
            return False

        # Revoke all previously issued JWTs.
        user.token_version += 1

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
