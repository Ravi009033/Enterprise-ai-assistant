
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee
from backend.app.models.user import User
from backend.app.services.auth_service import (
    create_user,
    authenticate_user,
)


def test_auth_service():

    suffix = uuid4().hex[:8]
    employee_id = f"AUTH{suffix.upper()}"
    employee_username = f"employee_{suffix}"
    hr_username = f"hr_{suffix}"

    db = SessionLocal()

    try:
        # Create an isolated employee.
        employee = Employee(
            employee_id=employee_id,
            name="Authentication Test Employee",
            total_leaves=24,
            used_leaves=0,
        )

        db.add(employee)
        db.commit()

    finally:
        db.close()

    try:
        # Test 1: Employee registration.
        employee_result = create_user(
            username=employee_username,
            password="EmployeePass123",
            role="employee",
            employee_id=employee_id,
        )

        assert employee_result["role"] == "employee"
        assert employee_result["employee_id"] == employee_id

        print("\nEmployee registration passed!")

        # Test 2: HR registration.
        hr_result = create_user(
            username=hr_username,
            password="HRPassword123",
            role="hr",
        )

        assert hr_result["role"] == "hr"
        assert hr_result["employee_id"] is None

        print("HR registration passed!")

        # Test 3: Duplicate username.
        try:
            create_user(
                username=employee_username,
                password="AnotherPass123",
                role="employee",
                employee_id=employee_id,
            )

            raise AssertionError("Duplicate username should fail")

        except ValueError as error:
            assert "already exists" in str(error).lower()

        print("Duplicate username validation passed!")

        # Test 4: Correct employee login.
        login_result = authenticate_user(
            employee_username,
            "EmployeePass123",
        )

        assert login_result is not None
        assert login_result["role"] == "employee"

        print("Employee login passed!")

        # Test 5: Incorrect password.
        wrong_login = authenticate_user(
            employee_username,
            "WrongPassword123",
        )

        assert wrong_login is None

        print("Incorrect password validation passed!")

        # Test 6: Correct HR login.
        hr_login = authenticate_user(
            hr_username,
            "HRPassword123",
        )

        assert hr_login is not None
        assert hr_login["role"] == "hr"

        print("HR login passed!")

        # Test 7: Inactive user cannot log in.
        db = SessionLocal()

        try:
            hr_user = (
                db.query(User)
                .filter(User.username == hr_username)
                .first()
            )

            hr_user.is_active = False
            db.commit()

        finally:
            db.close()

        inactive_login = authenticate_user(
            hr_username,
            "HRPassword123",
        )

        assert inactive_login is None

        print("Inactive account validation passed!")

        print("\nAll authentication service tests passed!")

    finally:
        # Clean up only the temporary test records.
        db = SessionLocal()

        try:
            db.query(User).filter(
                User.username.in_([employee_username, hr_username])
            ).delete(synchronize_session=False)

            db.query(Employee).filter(
                Employee.employee_id == employee_id
            ).delete(synchronize_session=False)

            db.commit()

            print("Temporary authentication test data cleaned up!")

        finally:
            db.close()


if __name__ == "__main__":
    test_auth_service()
