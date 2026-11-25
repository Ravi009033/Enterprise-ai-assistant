
# Mock employee records for our enterprise assistant.
# We will replace this with a database later.

EMPLOYEE_DATA = {
    "EMP001": {
        "name": "Rahul",
        "total_leaves": 24,
        "used_leaves": 8,
        "remaining_leaves": 16,
    },
    "EMP002": {
        "name": "Priya",
        "total_leaves": 24,
        "used_leaves": 12,
        "remaining_leaves": 12,
    },
    "EMP003": {
        "name": "Amit",
        "total_leaves": 24,
        "used_leaves": 5,
        "remaining_leaves": 19,
    },
}


def get_leave_balance(employee_id: str) -> dict:
    employee = EMPLOYEE_DATA.get(employee_id)

    if employee is None:
        raise ValueError("Employee not found")

    return {
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "total_leaves": employee["total_leaves"],
        "used_leaves": employee["used_leaves"],
        "remaining_leaves": employee["remaining_leaves"],
    }
