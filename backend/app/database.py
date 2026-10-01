import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stylnauki.db")

_connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # Ogranicza czekanie na blokadę SQLite (np. inny proces trzyma plik .db otwarty).
    _connect_args = {"check_same_thread": False, "timeout": 20.0}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=_connect_args)

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_foreign_keys(dbapi_connection, _record):
        # SQLite ignores ON DELETE CASCADE / SET NULL unless this is switched on per connection
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Bazowy model ORM: app.models.Base (DeclarativeBase, SQLAlchemy 2.0)
# Schemat bazy tworzą migracje Alembic: `alembic upgrade head`.
