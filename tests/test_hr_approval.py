
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.leave_request import LeaveRequest

from backend.app.services.approval_service import (
    approve_leave_request,
    reject_leave_request,
)


def test_hr_approval_workflow():

    employee_id = f"TEST{uuid4().hex[:10].upper()}"

    db = SessionLocal()

    try:
        # Create an isolated test employee.
        employee = Employee(
            employee_id=employee_id,
            name="Test Employee",
            total_leaves=10,
            used_leaves=0,
        )

        db.add(employee)

        # Create two pending leave requests.
        request_one = LeaveRequest(
            employee_id=employee_id,
            days=5,
            reason="Personal work",
            status="pending",
        )

        request_two = LeaveRequest(
            employee_id=employee_id,
            days=2,
            reason="Family function",
            status="pending",
        )

        db.add_all([request_one, request_two])
        db.commit()

        request_one_id = request_one.id
        request_two_id = request_two.id

    finally:
        db.close()

    try:
        # Test 1: Approve first request.
        result = approve_leave_request(request_one_id)

        print("\nApproval result:")
        print(result)

        assert result["status"] == "approved"
        assert result["used_leaves"] == 5
        assert result["remaining_leaves"] == 5

        # Test 2: Approve the same request again.
        duplicate_result = approve_leave_request(request_one_id)

        assert duplicate_result["status"] == "approved"

        db = SessionLocal()
        try:
            employee = db.get(Employee, employee_id)
            assert employee.used_leaves == 5
        finally:
            db.close()

        print("\nDuplicate approval test passed!")

        # Test 3: Reject second request.
        rejection_result = reject_leave_request(request_two_id)

        print("\nRejection result:")
        print(rejection_result)

        assert rejection_result["status"] == "rejected"

        db = SessionLocal()
        try:
            employee = db.get(Employee, employee_id)
            assert employee.used_leaves == 5
            assert employee.remaining_leaves == 5
        finally:
            db.close()

        print("\nRejection balance test passed!")

        # Test 4: Reject the same request again.
        duplicate_rejection = reject_leave_request(request_two_id)

        assert duplicate_rejection["status"] == "rejected"

        # Test 5: Reject approval when balance is insufficient.
        db = SessionLocal()
        try:
            insufficient_request = LeaveRequest(
                employee_id=employee_id,
                days=6,
                reason="Long leave",
                status="pending",
            )

            db.add(insufficient_request)
            db.commit()
            insufficient_request_id = insufficient_request.id

        finally:
            db.close()

        try:
            approve_leave_request(insufficient_request_id)
            raise AssertionError("Expected insufficient balance error")

        except ValueError as error:
            assert "insufficient available leave balance" in str(error).lower()
            print("\nInsufficient balance test passed!")

        print("\nAll HR approval tests passed!")

    finally:
        # Clean up only this test employee and its requests.
        db = SessionLocal()
        try:
            db.query(LeaveRequest).filter(
                LeaveRequest.employee_id == employee_id
            ).delete(synchronize_session=False)

            db.query(Employee).filter(
                Employee.employee_id == employee_id
            ).delete(synchronize_session=False)

            db.commit()

            print("\nTest employee and test requests cleaned up.")

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()


if __name__ == "__main__":
    test_hr_approval_workflow()
