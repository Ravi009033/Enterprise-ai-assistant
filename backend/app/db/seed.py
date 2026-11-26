
from backend.app.db.database import Base, engine, SessionLocal
from backend.app.models.employee import Employee


def seed_employees():
    # Ensure database tables exist.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    employees = [
        Employee(
            employee_id="EMP001",
            name="Rahul",
            total_leaves=24,
            used_leaves=8,
        ),
        Employee(
            employee_id="EMP002",
            name="Priya",
            total_leaves=24,
            used_leaves=12,
        ),
        Employee(
            employee_id="EMP003",
            name="Amit",
            total_leaves=24,
            used_leaves=5,
        ),
    ]

    try:
        for employee in employees:
            existing = db.get(Employee, employee.employee_id)

            if existing is None:
                db.add(employee)

        db.commit()
        print("Employee records inserted successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_employees()
