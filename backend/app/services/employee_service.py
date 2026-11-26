
from backend.app.db.database import SessionLocal
from backend.app.models.employee import Employee


def get_leave_balance(employee_id: str) -> dict:
    db = SessionLocal()

    try:
        employee = db.get(Employee, employee_id)

        if employee is None:
            raise ValueError("Employee not found")

        return {
            "employee_id": employee.employee_id,
            "employee_name": employee.name,
            "total_leaves": employee.total_leaves,
            "used_leaves": employee.used_leaves,
            "remaining_leaves": employee.remaining_leaves,
        }

    finally:
        db.close()
