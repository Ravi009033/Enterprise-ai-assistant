
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.app.core.jwt import decode_access_token
from backend.app.db.database import SessionLocal
from backend.app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def get_user_from_token(token: str):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
    )

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    db = SessionLocal()

    try:
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            raise credentials_exception

        user = db.get(User, user_id)

        if user is None or not user.is_active:
            raise credentials_exception

        token_version = payload.get("token_version")

        if token_version != user.token_version:
            raise credentials_exception

        return {
            "user_id": user.id,
            "username": user.username,
            "employee_id": user.employee_id,
            "role": user.role,
        }

    finally:
        db.close()
        

def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    return get_user_from_token(token)


def require_roles(*allowed_roles):

    def role_checker(
        current_user: dict = Depends(get_current_user),
    ):

        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )

        return current_user

    return role_checker
