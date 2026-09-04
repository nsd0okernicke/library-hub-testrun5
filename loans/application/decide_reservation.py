"""Use case for applying the catalog's reservation outcome to a pending loan."""

from loans.domain.exceptions import LoanNotFound
from loans.domain.loan import Loan, ReservationDecision
from loans.domain.ports import LoanRepository


class DecideReservation:
    """Apply a reservation decision to a pending loan.

    The due date term is a single global configuration value supplied at
    construction; it is not overridable per borrow request.
    """

    def __init__(self, loan_repository: LoanRepository, due_date_term_days: int) -> None:
        """Store the loan repository and the global due date term in days."""
        self._loan_repository = loan_repository
        self._due_date_term_days = due_date_term_days

    def __call__(self, loan_id: str, decision: ReservationDecision) -> Loan:
        """Decide the reservation for the loan and persist the result.

        Raises LoanNotFound for an unknown loan and LoanNotPending when the
        loan was already decided.
        """
        loan = self._loan_repository.get_by_id(loan_id)
        if loan is None:
            raise LoanNotFound(loan_id)
        if decision is ReservationDecision.ACTIVE:
            loan = loan.activate(self._due_date_term_days)
        else:
            loan = loan.reject()
        self._loan_repository.save(loan)
        return loan
