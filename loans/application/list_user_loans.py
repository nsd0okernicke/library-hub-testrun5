"""Use case for listing one user's loans, paginated and newest first."""

from loans.domain.ports import LoanRepository
from loans.domain.user_loans import DEFAULT_PAGE_SIZE, UserLoanPage, UserLoanQuery


class ListUserLoans:
    """List a user's loans one page at a time.

    Pagination parameters are validated (and the page size capped) by the
    domain query before the repository is reached. Loans are returned newest
    first, created_at descending with loan_id ascending as the tie-break.
    """

    def __init__(self, loan_repository: LoanRepository) -> None:
        """Store the loan repository used to fetch the page."""
        self._loan_repository = loan_repository

    def __call__(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> UserLoanPage:
        """Return the requested page of the user's loans (empty beyond the last)."""
        query = UserLoanQuery(user_id=user_id, page=page, page_size=page_size)
        loans = self._loan_repository.list_for_user(query)
        return UserLoanPage(loans=loans, page=query.page, page_size=query.page_size)
