"""Unit tests for the loans borrow endpoints (fake repositories, no I/O)."""

import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from loans.domain.loan import Loan
from loans.domain.user import User
from loans.infrastructure.api.main import create_app
from loans.infrastructure.config import LoanSettings


class InMemoryUserRepository:
    """In-memory fake of the UserRepository port for API unit tests."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def save(self, user: User) -> None:
        self.users[user.email] = user

    def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    def count_by_email(self, email: str) -> int:
        return 1 if email in self.users else 0

    def count(self) -> int:
        return len(self.users)


class InMemoryLoanRepository:
    """In-memory fake of the LoanRepository port for API unit tests."""

    def __init__(self) -> None:
        self.loans: dict[str, Loan] = {}

    def save(self, loan: Loan) -> None:
        self.loans[loan.loan_id] = loan

    def get_by_id(self, loan_id: str) -> Loan | None:
        return self.loans.get(loan_id)

    def count(self) -> int:
        return len(self.loans)


class RecordingPublisher:
    """Fake EventPublisher that records every published event."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> None:
        self.events.append(event)


def _client() -> tuple[
    TestClient, InMemoryUserRepository, InMemoryLoanRepository, RecordingPublisher
]:
    user_repository = InMemoryUserRepository()
    loan_repository = InMemoryLoanRepository()
    publisher = RecordingPublisher()
    app = create_app(user_repository, loan_repository, publisher=publisher)
    return TestClient(app), user_repository, loan_repository, publisher


class TestBorrowEndpoint:
    def test_borrow_returns_202_with_pending_loan(self) -> None:
        client, users, loans, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        response = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        )
        assert response.status_code == 202
        body = response.json()
        uuid.UUID(body["loan_id"])
        assert body["status"] == "PENDING"
        assert body["user_id"] == "usr-1"
        assert body["isbn"] == "978-0-20-163361-0"
        assert body["due_date"] is None
        assert loans.count() == 1

    def test_borrow_for_unknown_user_returns_404_and_creates_nothing(self) -> None:
        client, _, loans, publisher = _client()
        response = client.post(
            "/loans", json={"user_email": "nobody@example.com", "isbn": "978-0-20-163361-0"}
        )
        assert response.status_code == 404
        assert loans.count() == 0
        assert publisher.events == []

    def test_borrow_without_isbn_returns_422(self) -> None:
        client, users, _, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        response = client.post("/loans", json={"user_email": "alice@example.com"})
        assert response.status_code == 422

    def test_multiple_borrows_are_not_limited_by_existing_loans(self) -> None:
        client, users, loans, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        payload = {"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        first = client.post("/loans", json=payload)
        second = client.post("/loans", json=payload)
        assert first.status_code == 202
        assert second.status_code == 202
        assert first.json()["loan_id"] != second.json()["loan_id"]
        assert loans.count() == 2


class TestGetLoanEndpoint:
    def test_loan_is_queryable_by_id(self) -> None:
        client, users, _, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        created = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        )
        response = client.get(f"/loans/{created.json()['loan_id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "PENDING"

    def test_unknown_loan_returns_404(self) -> None:
        client, _, _, _ = _client()
        assert client.get("/loans/missing").status_code == 404

    def test_rejected_loan_remains_queryable(self) -> None:
        client, users, _, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        created = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        )
        loan_id = created.json()["loan_id"]
        client.post(f"/loans/{loan_id}/reservation", json={"decision": "REJECTED"})
        response = client.get(f"/loans/{loan_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "REJECTED"


class TestReservationEndpoint:
    def test_active_decision_sets_due_date_from_global_term(self) -> None:
        client, users, _, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        created = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        )
        loan_id = created.json()["loan_id"]
        response = client.post(f"/loans/{loan_id}/reservation", json={"decision": "ACTIVE"})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ACTIVE"
        delta = datetime.fromisoformat(body["due_date"]) - datetime.fromisoformat(
            body["created_at"]
        )
        assert delta == timedelta(days=28)

    def test_rejected_decision_keeps_loan_queryable(self) -> None:
        client, users, _, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        created = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        )
        loan_id = created.json()["loan_id"]
        response = client.post(f"/loans/{loan_id}/reservation", json={"decision": "REJECTED"})
        assert response.status_code == 200
        assert response.json()["status"] == "REJECTED"
        assert response.json()["due_date"] is None

    def test_unknown_loan_returns_404(self) -> None:
        client, _, _, _ = _client()
        response = client.post("/loans/nope/reservation", json={"decision": "ACTIVE"})
        assert response.status_code == 404

    def test_unknown_decision_returns_422(self) -> None:
        client, users, _, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        created = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        )
        response = client.post(
            f"/loans/{created.json()['loan_id']}/reservation", json={"decision": "MAYBE"}
        )
        assert response.status_code == 422

    def test_deciding_twice_returns_409(self) -> None:
        client, users, _, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        created = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        )
        loan_id = created.json()["loan_id"]
        assert (
            client.post(f"/loans/{loan_id}/reservation", json={"decision": "ACTIVE"}).status_code
            == 200
        )
        assert (
            client.post(f"/loans/{loan_id}/reservation", json={"decision": "REJECTED"}).status_code
            == 409
        )

    def test_term_is_read_from_settings_at_decision_time(self) -> None:
        user_repository = InMemoryUserRepository()
        loan_repository = InMemoryLoanRepository()
        publisher = RecordingPublisher()
        app = create_app(
            user_repository,
            loan_repository,
            publisher=publisher,
            settings=LoanSettings(due_date_term_days=7),
        )
        client = TestClient(app)
        user_repository.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        created = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        )
        response = client.post(
            f"/loans/{created.json()['loan_id']}/reservation", json={"decision": "ACTIVE"}
        )
        body = response.json()
        delta = datetime.fromisoformat(body["due_date"]) - datetime.fromisoformat(
            body["created_at"]
        )
        assert delta == timedelta(days=7)
