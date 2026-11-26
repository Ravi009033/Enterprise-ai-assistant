
from sqlalchemy import inspect, text

from backend.app.db.database import engine


def migrate():
    inspector = inspect(engine)

    columns = [
        column["name"]
        for column in inspector.get_columns("users")
    ]

    if "token_version" in columns:
        print("token_version column already exists.")
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE users "
                "ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"
            )
        )

    print("token_version column added successfully!")


if __name__ == "__main__":
    migrate()
