"""Domain exceptions for the catalog context."""


class BookAlreadyExists(Exception):
    """Raised when a book with the same ISBN is already registered."""

    def __init__(self, isbn: str) -> None:
        """Store the offending ISBN in the message."""
        super().__init__(f"Book with ISBN {isbn} is already registered")
        self.isbn = isbn
