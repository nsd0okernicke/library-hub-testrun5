"""Property tests for the ApplyBookReturnedEvent use case (CAT-4)."""

from dataclasses import replace
from unittest.mock import Mock

from hypothesis import given, settings
from hypothesis import strategies as st

from catalog.application.apply_book_returned import ApplyBookReturnedEvent
from catalog.domain.book import Book
from catalog.domain.events import BookReturnedEvent

ISBN = "978-0-20-163361-0"


def make_book(stock: int) -> Book:
    """Build a registered book with the given stock."""
    return Book(
        isbn=ISBN,
        title="Dune",
        author="Frank Herbert",
        genre="Sci-Fi",
        description=None,
        stock=stock,
    )


@given(
    stock=st.integers(min_value=0, max_value=10_000),
    count=st.integers(min_value=1, max_value=50),
)
@settings(max_examples=100)
def test_each_returned_event_adds_exactly_one_copy(stock: int, count: int) -> None:
    """Applying n events raises the stock from S to S + n, whatever S and n are."""
    book = make_book(stock)
    repository: Mock = Mock()
    current = book
    repository.get_by_isbn.side_effect = lambda _isbn: current
    saved: list[Book] = []
    repository.save.side_effect = lambda saved_book: saved.append(saved_book)

    use_case = ApplyBookReturnedEvent(repository)
    for _ in range(count):
        result = use_case(BookReturnedEvent(user_id="alice", isbn=ISBN))
        assert result is not None
        current = replace(current, stock=current.stock + 1)

    assert saved[-1].stock == stock + count


@given(stock=st.integers(min_value=0, max_value=10_000))
@settings(max_examples=50)
def test_unknown_isbn_never_changes_any_state(stock: int) -> None:
    """An event for an unregistered ISBN saves nothing, whatever the other book's stock."""
    repository: Mock = Mock()
    repository.get_by_isbn.return_value = None

    use_case = ApplyBookReturnedEvent(repository)
    result = use_case(BookReturnedEvent(user_id="bob", isbn="978-1-40-289462-6"))

    assert result is None
    repository.save.assert_not_called()


@given(stock=st.integers(min_value=0, max_value=10_000))
@settings(max_examples=50)
def test_metadata_survives_returned_events(stock: int) -> None:
    """Events never change metadata fields."""
    book = make_book(stock)
    repository: Mock = Mock()
    repository.get_by_isbn.return_value = book

    use_case = ApplyBookReturnedEvent(repository)
    result = use_case(BookReturnedEvent(user_id="alice", isbn=ISBN))

    assert result is not None
    assert (result.title, result.author, result.genre, result.description) == (
        "Dune",
        "Frank Herbert",
        "Sci-Fi",
        None,
    )
