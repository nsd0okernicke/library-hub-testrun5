"""Unit tests for the BookSearchCriteria and BookSearchResult value objects."""

import dataclasses

import pytest

from catalog.domain.book import Book
from catalog.domain.search import BookSearchCriteria, BookSearchResult


def _book(isbn: str, title: str) -> Book:
    """Build a minimal valid Book for test data."""
    return Book(
        isbn=isbn,
        title=title,
        author="A",
        genre="G",
        description=None,
        stock=1,
    )


class TestBookSearchCriteria:
    def test_defaults_are_first_page_with_empty_filters(self) -> None:
        criteria = BookSearchCriteria()
        assert criteria.title is None
        assert criteria.author is None
        assert criteria.genre is None
        assert criteria.page == 1
        assert criteria.page_size == 20

    def test_criteria_are_immutable(self) -> None:
        criteria = BookSearchCriteria(title="dune")
        with pytest.raises(dataclasses.FrozenInstanceError):
            criteria.title = "other"  # type: ignore[misc]

    @pytest.mark.parametrize("page", [-1, 0])
    def test_page_below_one_is_rejected(self, page: int) -> None:
        with pytest.raises(ValueError):
            BookSearchCriteria(page=page)

    @pytest.mark.parametrize("page_size", [-1, 0])
    def test_page_size_below_one_is_rejected(self, page_size: int) -> None:
        with pytest.raises(ValueError):
            BookSearchCriteria(page_size=page_size)


class TestBookSearchResult:
    def test_holds_returned_books_and_total(self) -> None:
        dune = _book("978-0-20-163361-0", "Dune")
        result = BookSearchResult(items=[dune], total_count=3)
        assert result.items == [dune]
        assert result.total_count == 3

    def test_empty_result_is_valid(self) -> None:
        result = BookSearchResult(items=[], total_count=0)
        assert result.items == []
        assert result.total_count == 0

    def test_result_is_immutable(self) -> None:
        result = BookSearchResult(items=[], total_count=0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.total_count = 1  # type: ignore[misc]

    def test_default_total_count_is_zero(self) -> None:
        assert BookSearchResult().total_count == 0

    def test_negative_total_count_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            BookSearchResult(items=[], total_count=-1)

    def test_total_count_must_cover_the_returned_books(self) -> None:
        with pytest.raises(ValueError):
            BookSearchResult(items=[_book("978-3-16-148410-0", "Dune")], total_count=0)
