
from backend.app.db.database import Base, engine

# Import model so SQLAlchemy registers its table.
from backend.app.models.employee import Employee
from backend.app.models.leave_request import LeaveRequest


def test_database_setup():

    Base.metadata.create_all(bind=engine)

    print("Database created successfully!")

    print("Registered tables:")
    print(Base.metadata.tables.keys())

  
    assert "employees" in Base.metadata.tables
    assert "leave_requests" in Base.metadata.tables

    print("Employee table created successfully!")


if __name__ == "__main__":
    test_database_setup()
