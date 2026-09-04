"""Port interfaces for the catalog context."""

import abc

from catalog.domain.book import Book
from catalog.domain.search import BookSearchCriteria, BookSearchResult


class BookRepository(abc.ABC):
    """Persistence port for books (one row per ISBN)."""

    @abc.abstractmethod
    def save(self, book: Book) -> None:
        """Persist the book (insert, or update the existing row for the ISBN)."""

    @abc.abstractmethod
    def get_by_isbn(self, isbn: str) -> Book | None:
        """Return the registered book for an ISBN, or None."""

    @abc.abstractmethod
    def count_by_isbn(self, isbn: str) -> int:
        """Return how many books are registered under an ISBN."""

    @abc.abstractmethod
    def search(self, criteria: BookSearchCriteria) -> BookSearchResult:
        """Search books by case-insensitive substring filters (AND), title ascending, paginated."""
