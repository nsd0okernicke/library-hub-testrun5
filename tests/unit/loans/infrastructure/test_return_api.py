"""Unit tests for the loans return endpoint (fake repositories, no I/O)."""

from datetime import datetime

from fastapi.testclient import TestClient

from loans.domain.loan import Loan
from loans.domain.user import User
from loans.infrastructure.api.main import create_app


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

    def list_overdue(self, now: datetime) -> list[Loan]:
        return [loan for loan in self.loans.values() if loan.is_overdue(now)]

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


def _active_loan_id(client: TestClient, user_repository: InMemoryUserRepository) -> str:
    """Create a user with an ACTIVE loan via the API and return its loan_id."""
    user_repository.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
    created = client.post(
        "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
    )
    loan_id = created.json()["loan_id"]
    decided = client.post(f"/loans/{loan_id}/reservation", json={"decision": "ACTIVE"})
    assert decided.status_code == 200
    return loan_id


class TestReturnEndpoint:
    def test_returning_active_loan_returns_200_and_marks_returned(self) -> None:
        client, users, loans, _ = _client()
        loan_id = _active_loan_id(client, users)
        response = client.post(f"/loans/{loan_id}/return")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "RETURNED"
        assert body["due_date"] is None
        assert loans.get_by_id(loan_id).status.name == "RETURNED"

    def test_returning_overdue_active_loan_still_returns_200(self) -> None:
        client, users, loans, _ = _client()
        loan_id = _active_loan_id(client, users)
        loan = loans.get_by_id(loan_id)
        # Push the due date into the past: overdue, but the return still succeeds.
        loans.save(
            Loan(
                loan_id=loan.loan_id,
                user_id=loan.user_id,
                isbn=loan.isbn,
                status=loan.status,
                created_at=datetime(2025, 1, 1),
                due_date=datetime(2025, 1, 29),
            )
        )
        response = client.post(f"/loans/{loan_id}/return")
        assert response.status_code == 200
        assert response.json()["status"] == "RETURNED"

    def test_returning_pending_loan_returns_409_and_keeps_loan(self) -> None:
        client, users, loans, publisher = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        loan_id = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        ).json()["loan_id"]
        events_before = len(publisher.events)
        response = client.post(f"/loans/{loan_id}/return")
        assert response.status_code == 409
        assert loans.get_by_id(loan_id).status.name == "PENDING"
        assert len(publisher.events) == events_before  # no BookReturned published

    def test_returning_rejected_loan_returns_409(self) -> None:
        client, users, loans, _ = _client()
        users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        loan_id = client.post(
            "/loans", json={"user_email": "alice@example.com", "isbn": "978-0-20-163361-0"}
        ).json()["loan_id"]
        client.post(f"/loans/{loan_id}/reservation", json={"decision": "REJECTED"})
        response = client.post(f"/loans/{loan_id}/return")
        assert response.status_code == 409
        assert loans.get_by_id(loan_id).status.name == "REJECTED"

    def test_returning_an_already_returned_loan_returns_409(self) -> None:
        client, users, loans, _ = _client()
        loan_id = _active_loan_id(client, users)
        assert client.post(f"/loans/{loan_id}/return").status_code == 200
        assert client.post(f"/loans/{loan_id}/return").status_code == 409

    def test_returning_unknown_loan_returns_404(self) -> None:
        client, users, _, _ = _client()
        assert client.post("/loans/nope/return").status_code == 404

    def test_return_publishes_book_returned_event(
        self,
    ) -> None:
        client, users, _, publisher = _client()
        loan_id = _active_loan_id(client, users)
        client.post(f"/loans/{loan_id}/return")
        events = [e for e in publisher.events if e.__class__.__name__ == "BookReturned"]
        assert len(events) == 1
        event = events[0]
        assert event.loan_id == loan_id
        assert event.user_id == "usr-1"
        assert event.isbn == "978-0-20-163361-0"
