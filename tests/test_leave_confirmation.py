from uuid import uuid4

from backend.app.services.chat_service import process_chat
from backend.app.db.database import SessionLocal
from backend.app.models.leave_request import LeaveRequest


def get_leave_request_count():
    db = SessionLocal()
    try:
        return db.query(LeaveRequest).count()
    finally:
        db.close()


def test_leave_confirmation_workflow():

    session_id = f"leave-test-{uuid4()}"

    initial_count = get_leave_request_count()

    # Step 1: User requests leave.
    first_response = process_chat(
        question="Apply for 2 days of leave because of personal work.",
        session_id=session_id,
    )

    print("\nFirst response:")
    print(first_response)

    assert first_response["status"] == "awaiting_confirmation"

    # Verify that no database record was created yet.
    assert get_leave_request_count() == initial_count

    # Step 2: User gives an unclear response.
    second_response = process_chat(
        question="Maybe",
        session_id=session_id,
    )

    print("\nSecond response:")
    print(second_response)

    assert second_response["status"] == "awaiting_confirmation"

    # Still no database record.
    assert get_leave_request_count() == initial_count

    # Step 3: User confirms.
    third_response = process_chat(
        question="YES",
        session_id=session_id,
    )

    print("\nThird response:")
    print(third_response)

    assert third_response["status"] == "success"

    # Now exactly one record should exist.
    assert get_leave_request_count() == initial_count + 1

    print("\nLeave confirmation workflow test passed!")

    # Step 4: User sends YES again.
    fourth_response = process_chat(
        question="YES",
        session_id=session_id,
    )

    print("\nFourth response (duplicate YES):")
    print(fourth_response)

    # Duplicate confirmation must not create another record.
    assert get_leave_request_count() == initial_count + 1

print("\nDuplicate confirmation test passed!")

def test_leave_cancellation_workflow():

    session_id = f"leave-cancel-{uuid4()}"

    initial_count = get_leave_request_count()

    # Step 1: Request leave.
    first_response = process_chat(
        question="Apply for 3 days of leave for a family function.",
        session_id=session_id,
    )

    assert first_response["status"] == "awaiting_confirmation"

    # Step 2: Reject the request.
    second_response = process_chat(
        question="NO",
        session_id=session_id,
    )

    print("\nCancellation response:")
    print(second_response)

    assert second_response["status"] == "cancelled"

    # No database record should be created.
    assert get_leave_request_count() == initial_count

    print("\nLeave cancellation workflow test passed!")


if __name__ == "__main__":
    test_leave_confirmation_workflow()
    test_leave_cancellation_workflow()