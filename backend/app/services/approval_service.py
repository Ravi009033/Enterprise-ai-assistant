
from sqlalchemy import func

from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.leave_request import LeaveRequest


def approve_leave_request(request_id: int) -> dict:

    db = SessionLocal()

    try:
        # Step 1: Find the leave request.
        leave_request = db.get(LeaveRequest, request_id)

        if leave_request is None:
            raise ValueError("Leave request not found")

        # Step 2: Prevent duplicate approval.
        if leave_request.status == "approved":
            return {
                "request_id": leave_request.id,
                "status": "approved",
                "message": "Leave request was already approved.",
            }

        if leave_request.status != "pending":
            raise ValueError(
                f"Cannot approve a request with status: "
                f"{leave_request.status}"
            )

        # Step 3: Find employee.
        employee = db.get(Employee, leave_request.employee_id)

        if employee is None:
            raise ValueError("Employee not found")

        # Step 4: Calculate other pending leave days.
        other_pending_days = (
            db.query(func.coalesce(func.sum(LeaveRequest.days), 0))
            .filter(
                LeaveRequest.employee_id == employee.employee_id,
                LeaveRequest.status == "pending",
                LeaveRequest.id != request_id,
            )
            .scalar()
        )

        # Step 5: Check whether approval would overbook balance.
        available_for_this_request = (
            employee.remaining_leaves - other_pending_days
        )

        if available_for_this_request < leave_request.days:
            raise ValueError(
                "Cannot approve this request because the employee "
                "has insufficient available leave balance. "
                "Review or reject other pending requests first."
            )

        # Step 6: Approve and update used leaves.
        employee.used_leaves += leave_request.days
        leave_request.status = "approved"

        db.commit()

        return {
            "request_id": leave_request.id,
            "employee_id": employee.employee_id,
            "days": leave_request.days,
            "used_leaves": employee.used_leaves,
            "remaining_leaves": employee.remaining_leaves,
            "status": leave_request.status,
            "message": "Leave request approved successfully.",
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def reject_leave_request(request_id: int) -> dict:

    db = SessionLocal()

    try:
        # Step 1: Find the leave request.
        leave_request = db.get(LeaveRequest, request_id)

        if leave_request is None:
            raise ValueError("Leave request not found")

        # Step 2: Prevent invalid status changes.
        if leave_request.status == "rejected":
            return {
                "request_id": leave_request.id,
                "status": "rejected",
                "message": "Leave request was already rejected.",
            }

        if leave_request.status != "pending":
            raise ValueError(
                f"Cannot reject a request with status: "
                f"{leave_request.status}"
            )

        # Step 3: Reject the request.
        leave_request.status = "rejected"

        # No employee leave balance deduction.
        db.commit()

        return {
            "request_id": leave_request.id,
            "employee_id": leave_request.employee_id,
            "days": leave_request.days,
            "status": leave_request.status,
            "message": "Leave request rejected successfully.",
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
