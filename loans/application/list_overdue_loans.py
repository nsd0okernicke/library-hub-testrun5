"""Use case for listing all overdue loans (admin)."""

from datetime import datetime

from loans.domain.loan import Loan, utc_now
from loans.domain.ports import LoanRepository


class ListOverdueLoans:
    """List every loan that is overdue at the current moment.

    A loan is overdue exactly when its status is ACTIVE and its due date lies
    in the past (due_date < now). The repository applies that filter; the use
    case only picks the reference moment (injected for testability).
    """

    def __init__(self, loan_repository: LoanRepository) -> None:
        """Store the loan repository used to fetch overdue loans."""
        self._loan_repository = loan_repository

    def __call__(self, now: datetime | None = None) -> list[Loan]:
        """Return all overdue loans as of ``now`` (defaults to the current time)."""
        return self._loan_repository.list_overdue(now if now is not None else utc_now())
