from sqlalchemy import inspect, text

from backend.app.db.database import engine


def migrate():

    inspector = inspect(engine)

    columns = [
        column["name"]
        for column in inspector.get_columns("leave_requests")
    ]

    with engine.begin() as connection:

        if "idempotency_key" not in columns:

            connection.execute(
                text(
                    "ALTER TABLE leave_requests "
                    "ADD COLUMN idempotency_key VARCHAR(64)"
                )
            )

            print("Added idempotency_key column.")

        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "ix_leave_requests_idempotency_key "
                "ON leave_requests (idempotency_key)"
            )
        )

        print("Unique index created or already exists.")


if __name__ == "__main__":
    migrate()