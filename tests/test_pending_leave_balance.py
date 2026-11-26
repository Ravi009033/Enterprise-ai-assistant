
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.leave_request import LeaveRequest
from sqlalchemy import func


def test_pending_leave_balance():

    db = SessionLocal()

    try:
        employee_id = "EMP001"

        employee = db.get(Employee, employee_id)

        pending_days = (
            db.query(func.coalesce(func.sum(LeaveRequest.days), 0))
            .filter(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status == "pending",
            )
            .scalar()
        )

        available_leaves = employee.remaining_leaves - pending_days

        print("\nEmployee:", employee.name)
        print("Remaining leaves:", employee.remaining_leaves)
        print("Pending leave days:", pending_days)
        print("Available leaves:", available_leaves)

        assert available_leaves >= 0

        print("\nPending leave balance calculation passed!")

    finally:
        db.close()


if __name__ == "__main__":
    test_pending_leave_balance()
