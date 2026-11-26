
from sqlalchemy import inspect

from backend.app.db.database import Base, engine
from backend.app.models.employee import Employee
from backend.app.models.user import User

def test_user_model():

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    assert "users" in tables

    columns = [
        column["name"]
        for column in inspector.get_columns("users")
    ]

    expected_columns = [
        "id",
        "username",
        "hashed_password",
        "employee_id",
        "role",
        "is_active",
        "created_at",
    ]

    for column in expected_columns:
        assert column in columns, f"Missing column: {column}"

    print("Users table created successfully!")
    print("All expected columns are present!")
    print(columns)


if __name__ == "__main__":
    test_user_model()
