"""Property tests for the ManualStockReturn use case (in-memory fake repository)."""

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from catalog.application.return_stock import ManualStockReturn
from catalog.domain.book import Book
from catalog.domain.exceptions import BookNotFound


class InMemoryBookRepository:
    """In-memory fake of the BookRepository port."""

    def __init__(self, books: dict[str, Book] | None = None) -> None:
        self.books = books or {}

    def save(self, book: Book) -> None:
        self.books[book.isbn] = book

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.books.get(isbn)

    def count_by_isbn(self, isbn: str) -> int:
        return 1 if isbn in self.books else 0


book_data = st.builds(
    Book,
    isbn=st.from_regex(r"97[89]-[0-9]-[0-9]{1,7}-[0-9]{1,7}-[0-9]", fullmatch=True),
    title=st.text(min_size=1, max_size=50),
    author=st.text(min_size=1, max_size=50),
    genre=st.text(min_size=1, max_size=30),
    description=st.one_of(st.none(), st.text(max_size=200)),
    stock=st.integers(min_value=0, max_value=10_000),
)

positive_copies = st.integers(min_value=1, max_value=10_000)
non_positive_copies = st.integers(max_value=0)


def _request(book: Book, copies: int) -> Any:
    return (book, copies)


class TestManualStockReturnProperties:
    @given(request=st.builds(_request, book=book_data, copies=positive_copies))
    @settings(max_examples=50)
    def test_stock_increases_by_exactly_the_added_copies(self, request: Any) -> None:
        book, copies = request
        repository = InMemoryBookRepository({book.isbn: book})
        use_case = ManualStockReturn(repository)
        result = use_case(book.isbn, copies)
        assert result.stock == book.stock + copies
        assert repository.get_by_isbn(book.isbn).stock == book.stock + copies

    @given(request=st.builds(_request, book=book_data, copies=positive_copies))
    @settings(max_examples=50)
    def test_metadata_is_never_touched(self, request: Any) -> None:
        book, copies = request
        repository = InMemoryBookRepository({book.isbn: book})
        use_case = ManualStockReturn(repository)
        result = use_case(book.isbn, copies)
        assert (result.isbn, result.title, result.author, result.genre, result.description) == (
            book.isbn,
            book.title,
            book.author,
            book.genre,
            book.description,
        )

    @given(request=st.builds(_request, book=book_data, copies=non_positive_copies))
    @settings(max_examples=50)
    def test_non_positive_copies_are_always_rejected_and_leave_the_book_unchanged(
        self, request: Any
    ) -> None:
        book, copies = request
        repository = InMemoryBookRepository({book.isbn: book})
        use_case = ManualStockReturn(repository)
        with pytest.raises(ValueError):
            use_case(book.isbn, copies)
        assert repository.get_by_isbn(book.isbn) == book

    @given(copies=positive_copies)
    @settings(max_examples=20)
    def test_unregistered_isbn_is_always_not_found(self, copies: int) -> None:
        repository = InMemoryBookRepository()
        use_case = ManualStockReturn(repository)
        with pytest.raises(BookNotFound):
            use_case("978-1-40-289462-6", copies)

    @given(request=st.builds(_request, book=book_data, copies=positive_copies))
    @settings(max_examples=50)
    def test_returns_are_commutative_over_amounts(self, request: Any) -> None:
        """Adding a+b copies in one go equals adding a then b (final stock only)."""
        book, copies = request
        repository = InMemoryBookRepository({book.isbn: book})
        use_case = ManualStockReturn(repository)
        one_go = use_case(book.isbn, copies).stock
        repository2 = InMemoryBookRepository({book.isbn: book})
        use_case2 = ManualStockReturn(repository2)
        half = max(copies // 2, 1)
        rest = copies - half
        if rest == 0:
            two_goes = use_case2(book.isbn, half).stock
        else:
            use_case2(book.isbn, half)
            two_goes = use_case2(book.isbn, rest).stock
        assert one_go == two_goes
