"""Unit tests for the SearchBooks use case (fake repository, no I/O)."""

import pytest

from catalog.application.search_books import SearchBooks
from catalog.domain.book import Book
from catalog.domain.search import BookSearchCriteria, BookSearchResult


class FakeBookRepository:
    """In-memory fake that records the criteria it received."""

    def __init__(self, result: BookSearchResult) -> None:
        self.result = result
        self.last_criteria: BookSearchCriteria | None = None

    def save(self, book: Book) -> None:  # pragma: no cover - unused port stub
        raise NotImplementedError

    def get_by_isbn(self, isbn: str) -> Book | None:  # pragma: no cover - unused
        return None

    def count_by_isbn(self, isbn: str) -> int:  # pragma: no cover - unused
        return 0

    def search(self, criteria: BookSearchCriteria) -> BookSearchResult:
        self.last_criteria = criteria
        return self.result


def _result() -> BookSearchResult:
    return BookSearchResult(
        items=[
            Book(
                isbn="978-0-20-163361-0",
                title="Dune",
                author="Frank Herbert",
                genre="Sci-Fi",
                description=None,
                stock=4,
            )
        ],
        total_count=1,
    )


class TestSearchBooks:
    def test_passes_filters_and_pagination_to_the_repository(self) -> None:
        repository = FakeBookRepository(_result())
        search_books = SearchBooks(repository)

        result = search_books(title="dune", author="herbert", genre="sci-fi", page=2, page_size=5)

        assert result is not None
        assert repository.last_criteria == BookSearchCriteria(
            title="dune", author="herbert", genre="sci-fi", page=2, page_size=5
        )

    def test_defaults_to_first_page_when_not_given(self) -> None:
        repository = FakeBookRepository(_result())
        search_books = SearchBooks(repository)

        search_books()

        assert repository.last_criteria == BookSearchCriteria()

    def test_returns_the_repository_result_unchanged(self) -> None:
        expected = _result()
        search_books = SearchBooks(FakeBookRepository(expected))
        assert search_books() == expected

    @pytest.mark.parametrize(
        "kwargs", [{"page": 0}, {"page": -3}, {"page_size": 0}, {"page_size": -1}]
    )
    def test_invalid_pagination_rejected_before_reaching_repository(self, kwargs) -> None:
        repository = FakeBookRepository(_result())
        search_books = SearchBooks(repository)
        with pytest.raises(ValueError):
            search_books(**kwargs)
        assert repository.last_criteria is None
