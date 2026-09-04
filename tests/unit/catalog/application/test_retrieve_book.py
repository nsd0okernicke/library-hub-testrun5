"""Unit tests for the RetrieveBook use case (mocked repository port)."""

import pytest

from catalog.application.retrieve_book import RetrieveBook
from catalog.domain.book import Book
from catalog.domain.exceptions import BookNotFound


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
def use_case(dune: Book) -> RetrieveBook:
    return RetrieveBook(FakeBookRepository({dune.isbn: dune}))


class TestRetrieveBook:
    def test_returns_registered_book(self, use_case: RetrieveBook, dune: Book) -> None:
        assert use_case(dune.isbn) is dune

    def test_returns_book_without_description(self) -> None:
        book = Book(
            isbn="978-0-13-468599-1",
            title="Refactoring",
            author="Martin Fowler",
            genre="Software",
            description=None,
            stock=0,
        )
        result = RetrieveBook(FakeBookRepository({book.isbn: book}))(book.isbn)
        assert result is book
        assert result.description is None

    def test_unknown_isbn_raises_book_not_found(self, use_case: RetrieveBook) -> None:
        with pytest.raises(BookNotFound):
            use_case("978-1-40-289462-6")

    def test_book_not_found_message_contains_isbn(self, use_case: RetrieveBook) -> None:
        with pytest.raises(BookNotFound, match="978-1-40-289462-6"):
            use_case("978-1-40-289462-6")
