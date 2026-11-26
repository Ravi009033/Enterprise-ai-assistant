from backend.app.db.database import SessionLocal
from backend.app.models.leave_request import LeaveRequest


def test_pending_leave_details():

    db = SessionLocal()

    try:
        requests = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.employee_id == "EMP001",
                LeaveRequest.status == "pending",
            )
            .order_by(LeaveRequest.id)
            .all()
        )

        print("\nPending leave requests:")

        for request in requests:
            print({
                "request_id": request.id,
                "days": request.days,
                "reason": request.reason,
                "status": request.status,
            })

        print("\nTotal pending requests:", len(requests))

        print(
            "Total pending days:",
            sum(request.days for request in requests)
        )

    finally:
        db.close()


if __name__ == "__main__":
    test_pending_leave_details()