"""Domain exceptions for the loans context."""


class EmailAlreadyRegistered(Exception):
    """Raised when a user with the same email is already registered."""

    def __init__(self, email: str) -> None:
        """Store the offending email in the message."""
        super().__init__(f"A user with email {email} is already registered")
        self.email = email
