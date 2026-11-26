
from sqlalchemy import inspect, text

from backend.app.db.database import engine


def migrate_login_security():
    inspector = inspect(engine)

    columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    with engine.begin() as connection:

        if "failed_login_attempts" not in columns:
            connection.execute(
                text("""
                    ALTER TABLE users
                    ADD COLUMN failed_login_attempts
                    INTEGER NOT NULL DEFAULT 0
                """)
            )
            print("Added failed_login_attempts column")

        if "locked_until" not in columns:
            connection.execute(
                text("""
                    ALTER TABLE users
                    ADD COLUMN locked_until DATETIME
                """)
            )
            print("Added locked_until column")

    print("Login security migration completed!")


if __name__ == "__main__":
    migrate_login_security()
