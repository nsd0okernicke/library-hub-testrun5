"""Unit tests for the loans FastAPI application (fake repository, no I/O)."""

from fastapi.testclient import TestClient

from loans.domain.user import User
from loans.infrastructure.api.main import create_app


class InMemoryLoanRepository:
    """In-memory fake of the LoanRepository port for API unit tests."""

    def __init__(self) -> None:
        self.loans: dict[str, object] = {}

    def save(self, loan: object) -> None:
        self.loans[loan.loan_id] = loan  # type: ignore[attr-defined]

    def get_by_id(self, loan_id: str) -> object | None:
        return self.loans.get(loan_id)

    def list_overdue(self, now: object) -> list[object]:
        return [
            loan
            for loan in self.loans.values()
            if getattr(loan, "is_overdue", lambda reference: False)(now)
        ]

    def count(self) -> int:
        return len(self.loans)


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


class TestCreateUserApi:
    def setup_method(self) -> None:
        self.repository = InMemoryUserRepository()
        self.loan_repository = InMemoryLoanRepository()
        self.app = create_app(self.repository, self.loan_repository)
        self.client = TestClient(self.app)

    def test_create_user_returns_201_with_generated_id(self) -> None:
        response = self.client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        assert response.status_code == 201
        body = response.json()
        assert body["user_id"]
        assert body["name"] == "Alice"
        assert body["email"] == "alice@example.com"

    def test_created_user_ids_are_unique(self) -> None:
        first = self.client.post("/users", json={"name": "Alice", "email": "a@example.com"})
        second = self.client.post("/users", json={"name": "Bob", "email": "b@example.com"})
        assert first.json()["user_id"] != second.json()["user_id"]

    def test_duplicate_email_returns_409(self) -> None:
        payload = {"name": "Alice", "email": "alice@example.com"}
        first = self.client.post("/users", json=payload)
        second = self.client.post("/users", json={"name": "Carol", "email": "alice@example.com"})
        assert first.status_code == 201
        assert second.status_code == 409
        assert self.repository.count_by_email("alice@example.com") == 1

    def test_missing_name_returns_422_and_creates_nothing(self) -> None:
        response = self.client.post("/users", json={"email": "alice@example.com"})
        assert response.status_code == 422
        assert self.repository.users == {}

    def test_missing_email_returns_422_and_creates_nothing(self) -> None:
        response = self.client.post("/users", json={"name": "Carol"})
        assert response.status_code == 422
        assert self.repository.users == {}

    def test_missing_body_returns_422(self) -> None:
        assert self.client.post("/users").status_code == 422
        assert self.repository.users == {}
