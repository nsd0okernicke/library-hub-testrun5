"""Runtime configuration for the loans service."""

from dataclasses import dataclass

DEFAULT_DUE_DATE_TERM_DAYS = 28


@dataclass
class LoanSettings:
    """Mutable global settings of the loans service.

    The due date term is a single global configuration value (default 28 days);
    it is not overridable per borrow request.
    """

    due_date_term_days: int = DEFAULT_DUE_DATE_TERM_DAYS
