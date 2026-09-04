"""Value objects for listing one user's loans with pagination."""

from dataclasses import dataclass, field

from loans.domain.loan import Loan

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class UserLoanQuery:
    """A paged query for one user's loans.

    Pages are 1-based. A requested page size above :data:`MAX_PAGE_SIZE` is
    capped, not rejected. Loans are returned by the repository newest first
    (created_at descending, loan_id ascending on ties).
    """

    user_id: str
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        """Enforce the query invariants (non-blank user, 1-based page, positive size)."""
        if not self.user_id.strip():
            raise ValueError("User ID must not be blank")
        if self.page < 1:
            raise ValueError(f"page must be >= 1, got {self.page}")
        if self.page_size < 1:
            raise ValueError(f"page_size must be >= 1, got {self.page_size}")
        if self.page_size > MAX_PAGE_SIZE:
            object.__setattr__(self, "page_size", MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        """Return the number of loans to skip before this page starts."""
        return (self.page - 1) * self.page_size


@dataclass(frozen=True)
class UserLoanPage:
    """One page of a user's loans (newest first, ties broken by loan_id)."""

    loans: list[Loan] = field(default_factory=list)
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
