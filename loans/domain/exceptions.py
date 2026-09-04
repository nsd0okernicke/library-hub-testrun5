"""Domain exceptions for the loans context."""


class EmailAlreadyRegistered(Exception):
    """Raised when a user with the same email is already registered."""

    def __init__(self, email: str) -> None:
        """Store the offending email in the message."""
        super().__init__(f"A user with email {email} is already registered")
        self.email = email


class UserNotFound(Exception):
    """Raised when a borrow request names a user that is not registered."""

    def __init__(self, email: str) -> None:
        """Store the offending email in the message."""
        super().__init__(f"No user is registered with email {email}")
        self.email = email


class LoanNotFound(Exception):
    """Raised when a loan with the given id does not exist."""

    def __init__(self, loan_id: str) -> None:
        """Store the offending loan id in the message."""
        super().__init__(f"No loan exists with id {loan_id}")
        self.loan_id = loan_id


class LoanNotPending(Exception):
    """Raised when a reservation outcome is applied to an already decided loan."""

    def __init__(self, loan_id: str) -> None:
        """Store the offending loan id in the message."""
        super().__init__(f"Loan {loan_id} is not PENDING; its outcome is already decided")
        self.loan_id = loan_id
