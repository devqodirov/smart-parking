import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_test_db = os.environ.get("SMART_PARKING_TEST_DB", "")
_env_url = os.environ.get("DATABASE_URL", "")

if _test_db:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{_test_db}"
    _connect_args = {"check_same_thread": False}
elif _env_url:
    SQLALCHEMY_DATABASE_URL = _env_url
    _connect_args = {}
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./smart_parking.db"
    _connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_postgres() -> bool:
    return engine.url.get_backend_name() == "postgresql"


def setup_postgis():
    if not is_postgres():
        return
    try:
        with engine.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            conn.commit()
    except Exception:
        pass
