
from backend.app.db.seed import seed_employees
from backend.app.services.employee_service import get_leave_balance


def test_database_employee_retrieval():

    # Ensure development records exist.
    seed_employees()

    # Retrieve Rahul's leave balance.
    result = get_leave_balance("EMP001")

    print("\nEmployee details:")
    print(result)

    assert result["employee_name"] == "Rahul"
    assert result["total_leaves"] == 24
    assert result["used_leaves"] == 8
    assert result["remaining_leaves"] == 16

    print("\nDatabase employee retrieval test passed!")


def test_invalid_employee():

    try:
        get_leave_balance("EMP999")
        assert False, "Expected ValueError"

    except ValueError as error:
        assert str(error) == "Employee not found"

    print("Invalid employee test passed!")


if __name__ == "__main__":
    test_database_employee_retrieval()
    test_invalid_employee()
