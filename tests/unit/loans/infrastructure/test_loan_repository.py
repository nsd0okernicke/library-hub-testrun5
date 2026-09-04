"""Unit tests for the SQLAlchemy loan repository (in-process SQLite, no container)."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from loans.domain.loan import Loan, LoanStatus
from loans.domain.user_loans import UserLoanQuery
from loans.infrastructure.persistence import Base, SqlAlchemyLoanRepository


def _repository() -> SqlAlchemyLoanRepository:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return SqlAlchemyLoanRepository(engine)


def _pending_loan(loan_id: str = "loan-1") -> Loan:
    return Loan(
        loan_id=loan_id,
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=LoanStatus.PENDING,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        due_date=None,
    )


def _active_loan(loan_id: str = "loan-2") -> Loan:
    return _pending_loan(loan_id).activate(due_date_term_days=28)


class TestSqlAlchemyLoanRepository:
    def test_save_and_get_by_id_round_trip_pending(self) -> None:
        repository = _repository()
        loan = _pending_loan()
        repository.save(loan)
        assert repository.get_by_id("loan-1") == loan

    def test_save_and_get_by_id_round_trip_active_with_due_date(self) -> None:
        repository = _repository()
        loan = _active_loan()
        repository.save(loan)
        stored = repository.get_by_id("loan-2")
        assert stored is not None
        assert stored.status is LoanStatus.ACTIVE
        assert stored.due_date is not None
        assert stored.due_date == loan.due_date

    def test_save_replaces_existing_row_for_same_loan_id(self) -> None:
        repository = _repository()
        repository.save(_pending_loan())
        repository.save(_pending_loan().activate(due_date_term_days=7))
        assert repository.count() == 1
        assert repository.get_by_id("loan-1").status is LoanStatus.ACTIVE

    def test_get_by_unknown_id_returns_none(self) -> None:
        repository = _repository()
        assert repository.get_by_id("nope") is None

    def test_multiple_loans_for_same_user_and_isbn_are_independent(self) -> None:
        repository = _repository()
        repository.save(_pending_loan("loan-1"))
        repository.save(_pending_loan("loan-2"))
        assert repository.count() == 2
        assert repository.get_by_id("loan-1") == _pending_loan("loan-1")

    def test_rejected_loan_remains_queryable(self) -> None:
        repository = _repository()
        repository.save(_pending_loan().reject())
        stored = repository.get_by_id("loan-1")
        assert stored is not None
        assert stored.status is LoanStatus.REJECTED


class TestListForUser:
    @staticmethod
    def _save(user_id: str, loan_id: str, created_at: datetime) -> None:
        repository = _repository()
        repository.save(
            Loan(
                loan_id=loan_id,
                user_id=user_id,
                isbn="978-0-20-163361-0",
                status=LoanStatus.PENDING,
                created_at=created_at,
                due_date=None,
            )
        )
        return repository

    def test_newest_first_and_only_requested_user(self) -> None:
        repository = _repository()
        same_day = datetime(2026, 1, 1, 12, 0, 0)
        other_user = datetime(2026, 2, 1, 9, 0, 0)
        repository.save(
            Loan("new", "usr-1", "isbn", LoanStatus.PENDING, same_day.replace(day=3), None)
        )
        repository.save(Loan("old", "usr-1", "isbn", LoanStatus.PENDING, same_day, None))
        repository.save(Loan("other", "usr-2", "isbn", LoanStatus.PENDING, other_user, None))
        page = repository.list_for_user(UserLoanQuery(user_id="usr-1", page=1, page_size=10))
        assert [loan.loan_id for loan in page] == ["new", "old"]

    def test_tie_on_created_at_breaks_by_loan_id_ascending(self) -> None:
        repository = _repository()
        same_instant = datetime(2026, 1, 1, 12, 0, 0)
        # Deliberately inserted in the opposite order of the expected result.
        for loan_id in ("c", "a", "b"):
            repository.save(Loan(loan_id, "usr-1", "isbn", LoanStatus.PENDING, same_instant, None))
        page = repository.list_for_user(UserLoanQuery(user_id="usr-1", page=1, page_size=10))
        assert [loan.loan_id for loan in page] == ["a", "b", "c"]

    def test_pagination_applies_limit_and_offset(self) -> None:
        repository = _repository()
        base = datetime(2026, 1, 1, 12, 0, 0)
        for index in range(4):
            repository.save(
                Loan(
                    f"loan-{index}",
                    "usr-1",
                    "isbn",
                    LoanStatus.PENDING,
                    base + timedelta(minutes=index),
                    None,
                )
            )
        page1 = repository.list_for_user(UserLoanQuery(user_id="usr-1", page=1, page_size=2))
        page2 = repository.list_for_user(UserLoanQuery(user_id="usr-1", page=2, page_size=2))
        page3 = repository.list_for_user(UserLoanQuery(user_id="usr-1", page=3, page_size=2))
        assert [loan.loan_id for loan in page1] == ["loan-3", "loan-2"]
        assert [loan.loan_id for loan in page2] == ["loan-1", "loan-0"]
        assert page3 == []

    def test_query_rejects_bad_parameters(self) -> None:
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="  ")
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="usr-1", page=0)
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="usr-1", page_size=0)
