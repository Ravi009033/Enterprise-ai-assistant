
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.services.auth_service import (
    change_user_password,
    authenticate_user,
    create_password_reset_token,
    reset_user_password,
    logout_user,
)
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from backend.app.schemas.auth import ChangePasswordRequest
from backend.app.core.jwt import create_access_token
from backend.app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):

    user = authenticate_user(
        username=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "sub": str(user["user_id"]),
        "username": user["username"],
        "role": user["role"],
        "employee_id": user["employee_id"],
        "token_version": user["token_version"],
    }

    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }

@router.get("/me")
def get_logged_in_user(
    current_user: dict = Depends(get_current_user),
):
    return current_user





@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        success = change_user_password(
            user_id=current_user["user_id"],
            current_password=request.current_password,
            new_password=request.new_password,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect or account is unavailable",
            )

        return {
            "message": "Password changed successfully"
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )



@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):

    token = create_password_reset_token(request.username)

    # Always return the same response to avoid revealing
    # whether an account exists.
    return {
        "message": (
            "If the account exists, password reset instructions "
            "will be sent."
        )
    }



@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):

    try:
        success = reset_user_password(
            raw_token=request.token,
            new_password=request.new_password,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        return {
            "message": "Password reset successfully"
        }

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )



@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):

    success = logout_user(current_user["user_id"])

    if not success:
        raise HTTPException(
            status_code=401,
            detail="Unable to logout. Please authenticate again.",
        )

    return {
        "message": "Logout successful. Please log in again."
    }



