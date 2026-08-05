from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# The engine is the actual connection pool to Postgres
engine = create_engine(settings.DATABASE_URL, future=True)

# SessionLocal() gives you a short-lived conversation with the DB
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
