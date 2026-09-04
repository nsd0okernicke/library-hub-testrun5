"""Acceptance fixtures: real PostgreSQL via Testcontainers, FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import parsers, then
from sqlalchemy import create_engine
from testcontainers.community.postgres import PostgresContainer

from catalog.infrastructure.api.main import create_app
from catalog.infrastructure.persistence import Base, SqlAlchemyBookRepository
from loans.infrastructure.api.main import create_app as create_loans_app
from loans.infrastructure.persistence import Base as LoansBase
from loans.infrastructure.persistence import SqlAlchemyUserRepository


@pytest.fixture()
def scenario_state() -> dict[str, object]:
    """Per-scenario state shared between steps (e.g. the response of the When step)."""
    return {}


@then(parsers.parse("the creation is rejected with status code {status:d}"))
def rejected_status(scenario_state, status):
    """Shared step: several feature files word the rejection check identically."""
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@pytest.fixture(scope="session")
def postgres_container():
    """Shared PostgreSQL container for the acceptance session."""
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture()
def client(postgres_container):
    """TestClient wired to a fresh catalog database (tables reset per scenario)."""
    port = postgres_container.get_exposed_port(5432)
    url = (
        f"postgresql+psycopg://{postgres_container.username}:"
        f"{postgres_container.password}"
        f"@{postgres_container.get_container_host_ip()}:{port}/{postgres_container.dbname}"
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


@pytest.fixture()
def loan_client(postgres_container):
    """TestClient wired to the loans service (tables reset per scenario)."""
    port = postgres_container.get_exposed_port(5432)
    url = (
        f"postgresql+psycopg://{postgres_container.username}:"
        f"{postgres_container.password}"
        f"@{postgres_container.get_container_host_ip()}:{port}/{postgres_container.dbname}"
    )
    engine = create_engine(url)
    LoansBase.metadata.drop_all(engine)
    LoansBase.metadata.create_all(engine)
    repository = SqlAlchemyUserRepository(engine)
    app = create_loans_app(repository)
    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        yield test_client
    engine.dispose()
