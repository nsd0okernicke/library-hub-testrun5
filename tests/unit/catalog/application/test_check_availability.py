"""Unit tests for the CheckBookAvailability use case (mocked repository port)."""

import pytest

from catalog.application.check_availability import CheckBookAvailability
from catalog.domain.availability import BookAvailability
from catalog.domain.book import Book
from catalog.domain.exceptions import BookNotFound
from catalog.domain.search import BookSearchCriteria, BookSearchResult


class FakeBookRepository:
    """In-memory fake of the BookRepository port."""

    def __init__(self, books: dict[str, Book] | None = None) -> None:
        self.books = books or {}

    def save(self, book: Book) -> None:
        self.books[book.isbn] = book

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.books.get(isbn)

    def count_by_isbn(self, isbn: str) -> int:
        return 1 if isbn in self.books else 0

    def search(self, criteria: BookSearchCriteria) -> BookSearchResult:
        raise NotImplementedError


@pytest.fixture
def dune() -> Book:
    return Book(
        isbn="978-0-20-163361-0",
        title="Dune",
        author="Frank Herbert",
        genre="Sci-Fi",
        description="Arrakis saga",
        stock=3,
    )


@pytest.fixture
def use_case(dune: Book) -> CheckBookAvailability:
    return CheckBookAvailability(FakeBookRepository({dune.isbn: dune}))


class TestCheckBookAvailability:
    def test_returns_isbn_and_available_count(
        self, use_case: CheckBookAvailability, dune: Book
    ) -> None:
        result = use_case(dune.isbn)
        assert result == BookAvailability(isbn=dune.isbn, available_count=dune.stock)

    def test_zero_stock_is_reported(self) -> None:
        book = Book(
            isbn="978-0-13-468599-1",
            title="Refactoring",
            author="Martin Fowler",
            genre="Software",
            description=None,
            stock=0,
        )
        result = CheckBookAvailability(FakeBookRepository({book.isbn: book}))(book.isbn)
        assert result.available_count == 0

    def test_availability_carries_no_other_book_details(
        self, use_case: CheckBookAvailability, dune: Book
    ) -> None:
        result = use_case(dune.isbn)
        assert not hasattr(result, "title")
        assert not hasattr(result, "author")

    def test_unknown_isbn_raises_book_not_found(self, use_case: CheckBookAvailability) -> None:
        with pytest.raises(BookNotFound):
            use_case("978-1-40-289462-6")
