"""Acceptance fixtures: real PostgreSQL via Testcontainers, FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, then, when
from sqlalchemy import create_engine
from testcontainers.community.postgres import PostgresContainer

from catalog.infrastructure.api.main import create_app
from catalog.infrastructure.broker import InMemoryBroker
from catalog.infrastructure.persistence import Base, SqlAlchemyBookRepository
from loans.infrastructure.api.main import create_app as create_loans_app
from loans.infrastructure.config import LoanSettings
from loans.infrastructure.persistence import Base as LoansBase
from loans.infrastructure.persistence import SqlAlchemyLoanRepository, SqlAlchemyUserRepository


class RecordingEventPublisher:
    """EventPublisher adapter that records events for acceptance assertions.

    When a broker is given, the event is also forwarded to it, mirroring the
    loans service publishing to the shared message broker.
    """

    def __init__(self, broker: InMemoryBroker | None = None) -> None:
        self.events: list[object] = []
        self._broker = broker

    def publish(self, event: object) -> None:
        """Record the published event and forward it to the shared broker."""
        self.events.append(event)
        if self._broker is not None:
            self._broker.publish(event)


@given("the loan service is running")
def loan_service_running(loan_client):
    """Shared Background step: the TestClient is wired to the loans service by the fixture."""
    assert loan_client is not None


@pytest.fixture()
def scenario_state() -> dict[str, object]:
    """Per-scenario state shared between steps (e.g. the response of the When step)."""
    return {}


@then(parsers.parse("the creation is rejected with status code {status:d}"))
def rejected_status(scenario_state, status):
    """Shared step: several feature files word the rejection check identically."""
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@given(parsers.parse("a user {name} with email {email} exists"))
def user_exists(loan_client, scenario_state, name, email):
    """Shared step: register a user account before borrowing scenarios."""
    response = loan_client.post("/users", json={"name": name, "email": email})
    assert response.status_code == 201, response.text
    scenario_state.setdefault("users", {})[name] = response.json()


@given("the catalog service is running")
def catalog_service_running(client):
    """Shared Background step: the TestClient is wired to the catalog service."""
    assert client is not None


@given(parsers.parse("a book with ISBN {isbn} is already registered"))
def book_already_registered(client, isbn):
    """Shared step: register a book with default metadata and stock 3."""
    response = client.post(
        "/books",
        json={
            "isbn": isbn,
            "title": "Already There",
            "author": "Some Author",
            "genre": "Mystery",
            "stock": 3,
        },
    )
    assert response.status_code == 201, response.text


@given(parsers.parse("a book with ISBN {isbn} is registered in the catalog"))
def book_registered_in_catalog(client, isbn):
    """Shared step: register a book in the catalog service."""
    response = client.post(
        "/books",
        json={
            "isbn": isbn,
            "title": f"Book {isbn}",
            "author": "Some Author",
            "genre": "Fiction",
            "stock": 1,
        },
    )
    assert response.status_code == 201, response.text


@given(parsers.parse("the loan due date term is {term:d} days"))
def loan_due_date_term(loan_client, term):
    """Shared step: override the global due date term in days."""
    loan_client.settings.due_date_term_days = int(term)  # type: ignore[attr-defined]


@when(parsers.parse("user {name} requests to borrow book {isbn}"))
def request_borrow(loan_client, scenario_state, name, isbn):
    """Shared step: post a borrow request for the named user and book."""
    user = scenario_state["users"][name]  # type: ignore[index]
    scenario_state["response"] = loan_client.post(
        "/loans", json={"user_email": user["email"], "isbn": isbn}
    )


@when(parsers.parse("the reservation for the loan is decided as {decision}"))
def decide_reservation(loan_client, scenario_state, decision):
    """Shared step: apply the reservation outcome to the borrow response's loan."""
    loan_id = scenario_state["response"].json()["loan_id"]
    if decision == "PENDING":
        # Nothing to decide: the loan simply stays PENDING as created.
        return
    response = loan_client.post(f"/loans/{loan_id}/reservation", json={"decision": decision})
    assert response.status_code == 200, response.text


@pytest.fixture()
def broker() -> InMemoryBroker:
    """In-process broker shared by the catalog and loans TestClients per scenario."""
    return InMemoryBroker()


@pytest.fixture(scope="session")
def postgres_container():
    """Shared PostgreSQL container for the acceptance session."""
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture()
def client(postgres_container, broker):
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
    app = create_app(repository, broker=broker)
    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        test_client.broker = broker  # type: ignore[attr-defined]
        yield test_client
    engine.dispose()


@pytest.fixture()
def loan_client(postgres_container, broker):
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
    user_repository = SqlAlchemyUserRepository(engine)
    loan_repository = SqlAlchemyLoanRepository(engine)
    settings = LoanSettings()
    publisher = RecordingEventPublisher(broker)
    app = create_loans_app(user_repository, loan_repository, publisher=publisher, settings=settings)
    with TestClient(app) as test_client:
        test_client.repository = user_repository  # type: ignore[attr-defined]
        test_client.loan_repository = loan_repository  # type: ignore[attr-defined]
        test_client.settings = settings  # type: ignore[attr-defined]
        test_client.events = publisher.events  # type: ignore[attr-defined]
        yield test_client
    engine.dispose()
