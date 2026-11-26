
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.leave_request import LeaveRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func


def apply_for_leave(
    employee_id: str,
    days: int,
    reason: str,
    idempotency_key: str,
) -> dict:

    if days <= 0:
        raise ValueError("Leave days must be greater than zero")

    if not reason.strip():
        raise ValueError("Leave reason is required")

    if not idempotency_key or not idempotency_key.strip():
        raise ValueError("Idempotency key is required")

    db = SessionLocal()

    try:
        # Step 1: Check for an existing request.
        existing_request = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.idempotency_key == idempotency_key
            )
            .first()
        )

        if existing_request:
            if existing_request.employee_id != employee_id:
                raise ValueError("Invalid idempotency key")

            return {
                "request_id": existing_request.id,
                "employee_id": existing_request.employee_id,
                "days": existing_request.days,
                "reason": existing_request.reason,
                "status": existing_request.status,
            }

        # Step 2: Validate employee.
        employee = db.get(Employee, employee_id)

        if employee is None:
            raise ValueError("Employee not found")

        # Calculate all currently pending leave days.
        pending_leave_days = (
            db.query(func.coalesce(func.sum(LeaveRequest.days), 0))
            .filter(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == "pending",
            )
            .scalar()
        )

        # Calculate available leaves after pending requests.
        available_leaves = employee.remaining_leaves - pending_leave_days

        if available_leaves < days:
            raise ValueError(
                f"Insufficient leave balance. "
                f"Available leaves: {available_leaves}, "
                f"Requested leaves: {days}"
            )

        # Step 3: Create the request.
        leave_request = LeaveRequest(
            employee_id=employee_id,
            days=days,
            reason=reason,
            status="pending",
            idempotency_key=idempotency_key,
        )

        db.add(leave_request)
        db.commit()
        db.refresh(leave_request)

        return {
            "request_id": leave_request.id,
            "employee_id": employee_id,
            "days": leave_request.days,
            "reason": leave_request.reason,
            "status": leave_request.status,
        }

    except IntegrityError:

        db.rollback()

        existing_request = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.idempotency_key == idempotency_key
            )
            .first()
        )

        if existing_request is None:
            raise

        if existing_request.employee_id != employee_id:
            raise ValueError("Invalid idempotency key")

        return {
            "request_id": existing_request.id,
            "employee_id": existing_request.employee_id,
            "days": existing_request.days,
            "reason": existing_request.reason,
            "status": existing_request.status,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
