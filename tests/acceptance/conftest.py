"""Acceptance fixtures: real PostgreSQL via Testcontainers, FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer

from catalog.infrastructure.api.main import create_app
from catalog.infrastructure.persistence import Base, SqlAlchemyBookRepository


@pytest.fixture(scope="session")
def postgres_container():
    """Shared PostgreSQL container for the acceptance session."""
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture()
def client(postgres_container):
    """TestClient wired to a fresh catalog database (tables reset per scenario)."""
    url = (
        f"postgresql+psycopg://{postgres_container.username}:"
        f"{postgres_container.password}"
        f"@{postgres_container.host}:{postgres_container.port}/{postgres_container.database}"
    )
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    repository = SqlAlchemyBookRepository(engine)
    app = create_app(repository)
    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        yield test_client
    engine.dispose()
