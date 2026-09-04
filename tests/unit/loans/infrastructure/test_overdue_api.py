"""Unit tests for the GET /loans/overdue endpoint (fake repository, no I/O)."""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from loans.domain.loan import Loan, LoanStatus, utc_now
from loans.domain.user import User
from loans.infrastructure.api.main import create_app


class InMemoryLoanRepository:
    """In-memory fake of the LoanRepository port for API unit tests."""

    def __init__(self) -> None:
        self.loans: dict[str, Loan] = {}

    def save(self, loan: Loan) -> None:
        self.loans[loan.loan_id] = loan

    def get_by_id(self, loan_id: str) -> Loan | None:
        return self.loans.get(loan_id)

    def list_for_user(self, query: object) -> list[Loan]:
        raise NotImplementedError

    def list_overdue(self, now: datetime) -> list[Loan]:
        return [loan for loan in self.loans.values() if loan.is_overdue(now)]

    def count(self) -> int:
        return len(self.loans)


class InMemoryUserRepository:
    """In-memory fake of the UserRepository port."""

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


def _active_loan(loan_id: str, due_date: datetime) -> Loan:
    return Loan(
        loan_id=loan_id,
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=LoanStatus.ACTIVE,
        created_at=due_date - timedelta(days=28),
        due_date=due_date,
    )


class TestOverdueLoansApi:
    def setup_method(self) -> None:
        self.repository = InMemoryLoanRepository()
        self.user_repository = InMemoryUserRepository()
        self.app = create_app(self.user_repository, self.repository)
        self.client = TestClient(self.app)

    def test_returns_200_with_only_overdue_entries(self) -> None:
        now = utc_now()
        overdue = _active_loan("loan-overdue", now - timedelta(days=2))
        future = _active_loan("loan-future", now + timedelta(days=1))
        self.repository.save(overdue)
        self.repository.save(future)
        response = self.client.get("/loans/overdue")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 1
        entry = body[0]
        assert entry["loan_id"] == "loan-overdue"
        assert entry["user_id"] == "usr-1"
        assert entry["isbn"] == "978-0-20-163361-0"
        assert datetime.fromisoformat(entry["due_date"]) < now

    def test_no_overdue_loans_returns_an_empty_list(self) -> None:
        response = self.client.get("/loans/overdue")
        assert response.status_code == 200
        assert response.json() == []

    def test_overdue_route_is_not_shadowed_by_loan_id_route(self) -> None:
        response = self.client.get("/loans/overdue")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
