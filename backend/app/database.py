import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kahvecell.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


# SQLite ignores foreign keys unless this is switched on for every connection.
@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _):
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
