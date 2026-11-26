
from backend.app.services.auth_service import create_user
from backend.app.models.employee import Employee

create_user(
    username="employee_test",
    password="Employee@2026",
    role="employee",
    employee_id="EMP001",
)

print("Employee login account created successfully!")
print("Username: employee_test")
print("Password: Employee@2026")
