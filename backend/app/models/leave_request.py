from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func

from backend.app.db.database import Base


class LeaveRequest(Base):

    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        String(20),
        ForeignKey("employees.employee_id"),
        nullable=False,
        index=True,
    )

    days = Column(Integer, nullable=False)

    reason = Column(String(500), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Unique identifier to prevent duplicate submissions.
    # Nullable temporarily to support existing database records.
    idempotency_key = Column(
        String(64),
        unique=True,
        index=True,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )