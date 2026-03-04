from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    """Create a SQLAlchemy engine pointing at the test database."""
    engine = create_engine(
        settings.TEST_DATABASE_URL,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables(test_engine: Engine) -> Generator[None, None, None]:
    """Delete all rows after each test for isolation."""
    yield
    with test_engine.connect() as conn:
        conn.execute(text("DELETE FROM analysis_results"))
        conn.execute(text("DELETE FROM operational_records"))
        conn.commit()


@pytest.fixture(scope="function")
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Yield a database session. Cleanup is handled by _clean_tables."""
    session_factory: sessionmaker[Session] = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Return a TestClient with the db dependency overridden."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
