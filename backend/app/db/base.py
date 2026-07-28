from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """All table models inherit from this. Alembic uses it to
    discover every table you define."""

    pass
