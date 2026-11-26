
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func

from backend.app.db.database import Base



class User(Base):

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "role IN ('employee', 'hr')",
            name="ck_users_role",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password = Column(
        String(255),
        nullable=False,
    )

    employee_id = Column(
        String(20),
        ForeignKey("employees.employee_id"),
        unique=True,
        nullable=True,
    )

    role = Column(
        String(20),
        nullable=False,
        default="employee",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    failed_login_attempts = Column(
        Integer,
        nullable=False,
        default=0,
    )

    locked_until = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    token_version = Column(
        Integer,
        nullable=False,
        default=0,
    )