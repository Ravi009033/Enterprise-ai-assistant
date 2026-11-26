
from sqlalchemy import inspect

from backend.app.db.database import Base, engine
from backend.app.models.password_reset import PasswordResetToken
from backend.app.models.user import User


def migrate():
    inspector = inspect(engine)

    if "password_reset_tokens" in inspector.get_table_names():
        print("Password reset table already exists.")
        return

    Base.metadata.create_all(
        bind=engine,
        tables=[PasswordResetToken.__table__],
    )

    print("Password reset table created successfully!")


if __name__ == "__main__":
    migrate()
