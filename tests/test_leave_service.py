
from backend.app.db.seed import seed_employees
from backend.app.services.leave_service import apply_for_leave


def test_valid_leave_application():

    seed_employees()

    result = apply_for_leave(
        employee_id="EMP001",
        days=2,
        reason="Personal work",
    )

    print("\nLeave application result:")
    print(result)

    assert result["employee_id"] == "EMP001"
    assert result["days"] == 2
    assert result["status"] == "pending"

    print("\nValid leave application test passed!")


def test_insufficient_balance():

    try:
        apply_for_leave(
            employee_id="EMP001",
            days=100,
            reason="Long vacation",
        )

        assert False, "Expected insufficient balance error"

    except ValueError as error:
        assert str(error) == "Insufficient leave balance"

    print("Insufficient balance test passed!")


def test_invalid_days():

    try:
        apply_for_leave(
            employee_id="EMP001",
            days=0,
            reason="Personal work",
        )

        assert False, "Expected invalid days error"

    except ValueError as error:
        assert str(error) == "Leave days must be greater than zero"

    print("Invalid days test passed!")


if __name__ == "__main__":
    test_valid_leave_application()
    test_insufficient_balance()
    test_invalid_days()
