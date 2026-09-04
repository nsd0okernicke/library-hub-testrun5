"""Domain exceptions for the catalog context."""


class BookAlreadyExists(Exception):
    """Raised when a book with the same ISBN is already registered."""

    def __init__(self, isbn: str) -> None:
        """Store the offending ISBN in the message."""
        super().__init__(f"Book with ISBN {isbn} is already registered")
        self.isbn = isbn


class BookNotFound(Exception):
    """Raised when no book is registered under the requested ISBN."""

    def __init__(self, isbn: str) -> None:
        """Store the requested ISBN in the message."""
        super().__init__(f"No book registered with ISBN {isbn}")
        self.isbn = isbn
