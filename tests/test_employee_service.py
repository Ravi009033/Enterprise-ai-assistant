
from backend.app.services.employee_service import get_leave_balance


def test_valid_employee():
    result = get_leave_balance("EMP001")

    assert result["employee_name"] == "Rahul"
    assert result["total_leaves"] == 24
    assert result["used_leaves"] == 8
    assert result["remaining_leaves"] == 16

    print("Valid employee test passed!")
    print(result)


def test_invalid_employee():
    try:
        get_leave_balance("EMP999")
        assert False, "Expected ValueError"
    except ValueError as error:
        assert str(error) == "Employee not found"

    print("Invalid employee test passed!")


if __name__ == "__main__":
    test_valid_employee()
    test_invalid_employee()
