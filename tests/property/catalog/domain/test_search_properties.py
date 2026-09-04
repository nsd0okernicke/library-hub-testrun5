"""Property tests for the catalog domain search value objects."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from catalog.domain.book import Book
from catalog.domain.search import BookSearchCriteria, BookSearchResult


def _book(isbn: str, title: str) -> Book:
    """Build a minimal valid Book for property data."""
    return Book(
        isbn=isbn,
        title=title,
        author="A",
        genre="G",
        description=None,
        stock=1,
    )


class TestBookSearchCriteriaProperties:
    @given(
        page=st.integers(min_value=1, max_value=10_000),
        page_size=st.integers(min_value=1, max_value=10_000),
    )
    @settings(max_examples=25)
    def test_valid_pagination_is_always_accepted(self, page: int, page_size: int) -> None:
        criteria = BookSearchCriteria(page=page, page_size=page_size)
        assert criteria.page == page
        assert criteria.page_size == page_size

    @given(page=st.integers(max_value=0))
    @settings(max_examples=25)
    def test_page_below_one_is_always_rejected(self, page: int) -> None:
        with pytest.raises(ValueError):
            BookSearchCriteria(page=page)

    @given(page_size=st.integers(max_value=0))
    @settings(max_examples=25)
    def test_page_size_below_one_is_always_rejected(self, page_size: int) -> None:
        with pytest.raises(ValueError):
            BookSearchCriteria(page_size=page_size)


class TestBookSearchResultProperties:
    @given(
        n_items=st.integers(min_value=0, max_value=10),
        extra=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=25)
    def test_consistent_counts_are_always_preserved(self, n_items: int, extra: int) -> None:
        items = [_book(f"978-0-0-0000000-{i:05d}", f"Title {i}") for i in range(n_items)]
        result = BookSearchResult(items=items, total_count=n_items + extra)
        assert len(result.items) == n_items
        assert result.total_count == n_items + extra

    @given(n_items=st.integers(min_value=1, max_value=10))
    @settings(max_examples=25)
    def test_total_below_item_count_is_always_rejected(self, n_items: int) -> None:
        items = [_book(f"978-0-0-0000000-{i:05d}", f"Title {i}") for i in range(n_items)]
        with pytest.raises(ValueError):
            BookSearchResult(items=items, total_count=n_items - 1)
