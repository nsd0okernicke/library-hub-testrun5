"""Unit tests for the ListUserLoans use case (mocked ports, no I/O)."""

from datetime import datetime

import pytest

from loans.application.list_user_loans import ListUserLoans
from loans.domain.loan import Loan, LoanStatus, utc_now
from loans.domain.user_loans import MAX_PAGE_SIZE, UserLoanQuery


def _loan(loan_id: str, user_id: str, isbn: str) -> Loan:
    return Loan(
        loan_id=loan_id,
        user_id=user_id,
        isbn=isbn,
        status=LoanStatus.PENDING,
        created_at=utc_now(),
        due_date=None,
    )


class FakeLoanRepository:
    """In-memory fake of the LoanRepository port (newest-first ordering)."""

    def __init__(self, loans: list[Loan]) -> None:
        self._loans = {loan.loan_id: loan for loan in loans}

    def save(self, loan: Loan) -> None:
        self._loans[loan.loan_id] = loan

    def get_by_id(self, loan_id: str) -> Loan | None:
        return self._loans.get(loan_id)

    def count(self) -> int:
        return len(self._loans)

    def list_for_user(self, query: UserLoanQuery) -> list[Loan]:
        # Newest first: stable sort by loan_id asc, then by created_at desc.
        ordered = sorted(
            (loan for loan in self._loans.values() if loan.user_id == query.user_id),
            key=lambda loan: loan.loan_id,
        )
        ordered = sorted(ordered, key=lambda loan: loan.created_at, reverse=True)
        return ordered[query.offset : query.offset + query.page_size]

    def list_overdue(self, now: datetime) -> list[Loan]:
        return [loan for loan in self._loans.values() if loan.is_overdue(now)]


@pytest.fixture
def two_user_loans() -> list[Loan]:
    return [
        _loan("loan-1", "usr-a", "isbn-1"),
        _loan("loan-2", "usr-a", "isbn-2"),
        _loan("loan-3", "usr-b", "isbn-3"),
    ]


@pytest.fixture
def loan_repository(two_user_loans: list[Loan]) -> FakeLoanRepository:
    return FakeLoanRepository(two_user_loans)


class TestListUserLoans:
    def test_returns_only_the_requested_users_loans(
        self, loan_repository: FakeLoanRepository
    ) -> None:
        page = ListUserLoans(loan_repository)("usr-a")
        assert {loan.loan_id for loan in page.loans} == {"loan-1", "loan-2"}

    def test_unknown_user_gets_an_empty_page(self, loan_repository: FakeLoanRepository) -> None:
        page = ListUserLoans(loan_repository)("usr-nobody")
        assert page.loans == []

    def test_blank_user_id_is_rejected_before_reaching_the_repository(
        self, loan_repository: FakeLoanRepository
    ) -> None:
        with pytest.raises(ValueError):
            ListUserLoans(loan_repository)("   ")

    def test_page_and_page_size_are_echoed(self, loan_repository: FakeLoanRepository) -> None:
        page = ListUserLoans(loan_repository)("usr-a", page=2, page_size=10)
        assert page.page == 2
        assert page.page_size == 10

    def test_over_sized_page_is_capped(self, loan_repository: FakeLoanRepository) -> None:
        page = ListUserLoans(loan_repository)("usr-a", page=1, page_size=500)
        assert page.page_size == MAX_PAGE_SIZE

    def test_zero_page_is_rejected(self, loan_repository: FakeLoanRepository) -> None:
        with pytest.raises(ValueError):
            ListUserLoans(loan_repository)("usr-a", page=0)

    def test_zero_page_size_is_rejected(self, loan_repository: FakeLoanRepository) -> None:
        with pytest.raises(ValueError):
            ListUserLoans(loan_repository)("usr-a", page=1, page_size=0)
