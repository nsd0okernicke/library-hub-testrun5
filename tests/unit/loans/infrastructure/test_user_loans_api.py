"""Unit tests for the GET /users/{user_id}/loans endpoint (fake repository, no I/O)."""

import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from loans.domain.loan import Loan, LoanStatus, utc_now
from loans.domain.user import User
from loans.domain.user_loans import UserLoanQuery
from loans.infrastructure.api.main import create_app


class InMemoryLoanRepository:
    """In-memory fake of the LoanRepository port (newest-first ordering)."""

    def __init__(self) -> None:
        self.loans: list[Loan] = []

    def save(self, loan: Loan) -> None:
        existing = next(
            (candidate for candidate in self.loans if candidate.loan_id == loan.loan_id),
            None,
        )
        if existing is None:
            self.loans.append(loan)
        else:
            self.loans[self.loans.index(existing)] = loan

    def get_by_id(self, loan_id: str) -> Loan | None:
        return next((loan for loan in self.loans if loan.loan_id == loan_id), None)

    def count(self) -> int:
        return len(self.loans)

    def list_for_user(self, query: UserLoanQuery) -> list[Loan]:
        # Newest first: stable sort by loan_id asc, then by created_at desc.
        owned = sorted(
            (loan for loan in self.loans if loan.user_id == query.user_id),
            key=lambda loan: loan.loan_id,
        )
        newest_first = sorted(owned, key=lambda loan: loan.created_at, reverse=True)
        return newest_first[query.offset : query.offset + query.page_size]


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


def _loan(
    loan_id: str, user_id: str, isbn: str, created_at: datetime, status=LoanStatus.PENDING
) -> Loan:
    due = created_at + timedelta(days=28) if status is LoanStatus.ACTIVE else None
    return Loan(
        loan_id=loan_id,
        user_id=user_id,
        isbn=isbn,
        status=status,
        created_at=created_at,
        due_date=due,
    )


class TestListUserLoansApi:
    def setup_method(self) -> None:
        self.user_repository = InMemoryUserRepository()
        self.loan_repository = InMemoryLoanRepository()
        self.client = TestClient(create_app(self.user_repository, self.loan_repository))
        now = utc_now()
        self.user_id = self._make_user("Alice", "alice@example.com")
        other_user = User(user_id="usr-b", name="Bob", email="bob@example.com")
        self.user_repository.save(other_user)
        self.oldest = _loan("oldest", self.user_id, "isbn-old", now - timedelta(hours=2))
        self.middle = _loan("middle", self.user_id, "isbn-mid", now - timedelta(hours=1))
        self.newest = _loan("newest", self.user_id, "isbn-new", now, LoanStatus.ACTIVE)
        self.ours = _loan("ours", "usr-b", "isbn-ours", now)
        for loan in (self.oldest, self.middle, self.newest, self.ours):
            self.loan_repository.save(loan)

    def _make_user(self, name: str, email: str) -> str:
        user_id = str(uuid.uuid4())
        self.user_repository.save(User(user_id=user_id, name=name, email=email))
        return user_id

    def test_returns_200_with_newest_first_order(self) -> None:
        response = self.client.get(f"/users/{self.user_id}/loans")
        assert response.status_code == 200
        isbns = [entry["isbn"] for entry in response.json()["loans"]]
        assert isbns == ["isbn-new", "isbn-mid", "isbn-old"]

    def test_entry_contains_loan_id_isbn_status_and_due_date(self) -> None:
        response = self.client.get(f"/users/{self.user_id}/loans")
        entries = {entry["loan_id"]: entry for entry in response.json()["loans"]}
        assert set(entries) == {"oldest", "middle", "newest"}
        for entry in entries.values():
            assert "isbn" in entry and "status" in entry
        assert entries["newest"]["status"] == "ACTIVE"
        assert entries["newest"]["due_date"] is not None
        assert entries["oldest"]["status"] == "PENDING"
        assert entries["oldest"]["due_date"] is None

    def test_pagination_page_and_page_size(self) -> None:
        response = self.client.get(
            f"/users/{self.user_id}/loans", params={"page": 2, "page_size": 2}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["page"] == 2
        assert body["page_size"] == 2
        assert [entry["loan_id"] for entry in body["loans"]] == ["oldest"]

    def test_defaults_are_page_one_size_20(self) -> None:
        body = self.client.get(f"/users/{self.user_id}/loans").json()
        assert body["page"] == 1
        assert body["page_size"] == 20

    def test_page_size_above_maximum_is_capped_to_100(self) -> None:
        body = self.client.get(
            f"/users/{self.user_id}/loans", params={"page": 1, "page_size": 150}
        ).json()
        assert body["page_size"] == 100

    def test_page_beyond_the_last_page_is_an_empty_list_with_200(self) -> None:
        response = self.client.get(
            f"/users/{self.user_id}/loans", params={"page": 5, "page_size": 1}
        )
        assert response.status_code == 200
        assert response.json()["loans"] == []

    def test_unknown_user_gets_an_empty_list_with_200(self) -> None:
        response = self.client.get(f"/users/{uuid.uuid4()}/loans")
        assert response.status_code == 200
        assert response.json()["loans"] == []

    def test_other_users_loans_are_excluded(self) -> None:
        response = self.client.get(f"/users/{self.user_id}/loans")
        isbns = [entry["isbn"] for entry in response.json()["loans"]]
        assert "isbn-ours" not in isbns

    def test_page_zero_is_rejected_with_422(self) -> None:
        response = self.client.get(
            f"/users/{self.user_id}/loans", params={"page": 0, "page_size": 10}
        )
        assert response.status_code == 422

    def test_page_size_zero_is_rejected_with_422(self) -> None:
        response = self.client.get(
            f"/users/{self.user_id}/loans", params={"page": 1, "page_size": 0}
        )
        assert response.status_code == 422
