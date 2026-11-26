
from pydantic import BaseModel, Field


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        description="User's current password",
    )

    new_password: str = Field(
        min_length=8,
        description="New password with at least 8 characters",
    )



class ForgotPasswordRequest(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=100,
        description="Username of the account",
    )


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=1,
        description="Password reset token",
    )

    new_password: str = Field(
        min_length=8,
        description="New password with at least 8 characters",
    )
