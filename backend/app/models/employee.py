
from sqlalchemy import Column, Integer, String

from backend.app.db.database import Base


class Employee(Base):

    __tablename__ = "employees"

    employee_id = Column(
        String(20),
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    total_leaves = Column(
        Integer,
        nullable=False,
        default=24
    )

    used_leaves = Column(
        Integer,
        nullable=False,
        default=0
    )

    @property
    def remaining_leaves(self):
        return self.total_leaves - self.used_leaves
