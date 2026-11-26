
from uuid import uuid4

from backend.app.services.leave_service import apply_for_leave
from backend.app.db.database import SessionLocal
from backend.app.models.leave_request import LeaveRequest


def get_leave_request_count():
    db = SessionLocal()
    try:
        return db.query(LeaveRequest).count()
    finally:
        db.close()


def test_duplicate_leave_submission():

    employee_id = "EMP001"
    idempotency_key = str(uuid4())

    initial_count = get_leave_request_count()

    # First submission.
    first_request = apply_for_leave(
        employee_id=employee_id,
        days=1,
        reason="Personal work",
        idempotency_key=idempotency_key,
    )

    # Second submission with the SAME key.
    second_request = apply_for_leave(
        employee_id=employee_id,
        days=1,
        reason="Personal work",
        idempotency_key=idempotency_key,
    )

    print("\nFirst request:")
    print(first_request)

    print("\nSecond request:")
    print(second_request)

    # Both calls must return the same database request.
    assert first_request["request_id"] == second_request["request_id"]

    # Only one new database record must exist.
    assert get_leave_request_count() == initial_count + 1

    print("\nDatabase idempotency test passed!")


if __name__ == "__main__":
    test_duplicate_leave_submission()
