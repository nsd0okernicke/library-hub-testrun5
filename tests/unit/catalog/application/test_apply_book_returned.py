"""Unit tests for the ApplyBookReturnedEvent use case (CAT-4)."""

import typing
from dataclasses import replace
from unittest.mock import Mock

import pytest

from catalog.application.apply_book_returned import ApplyBookReturnedEvent
from catalog.domain.book import Book
from catalog.domain.events import BookReturnedEvent


def make_book(stock: int = 0) -> Book:
    """Build a registered book with the given stock."""
    return Book(
        isbn="978-0-20-163361-0",
        title="Dune",
        author="Frank Herbert",
        genre="Sci-Fi",
        description=None,
        stock=stock,
    )


def make_repository(book: Book | None) -> Mock:
    """Build a mock BookRepository that returns `book` for get_by_isbn."""
    repository: Mock = Mock()
    repository.get_by_isbn.return_value = book
    return repository


def make_event(isbn: str = "978-0-20-163361-0") -> BookReturnedEvent:
    """Build a book returned event for the given ISBN."""
    return BookReturnedEvent(user_id="alice", isbn=isbn)


def test_registered_book_stock_increased_by_one() -> None:
    """A received event adds exactly one copy to the registered book's stock."""
    repository = make_repository(make_book(stock=0))
    use_case = ApplyBookReturnedEvent(repository)

    result = use_case(make_event())

    assert result is not None
    assert result.stock == 1
    saved = repository.save.call_args.args[0]
    assert saved.stock == 1


def test_registered_book_existing_stock_increments() -> None:
    """An existing stock of 3 becomes 4 after one returned event."""
    repository = make_repository(make_book(stock=3))
    use_case = ApplyBookReturnedEvent(repository)

    result = use_case(make_event())

    assert result is not None
    assert result.stock == 4


def test_multiple_events_each_add_one_copy() -> None:
    """Every event adds one copy; three events raise stock by three."""
    book = make_book(stock=1)
    repository = make_repository(book)
    use_case = ApplyBookReturnedEvent(repository)

    use_case(make_event())
    repository.get_by_isbn.return_value = replace(book, stock=2)
    use_case(make_event())
    repository.get_by_isbn.return_value = replace(book, stock=3)
    result = use_case(make_event())

    assert result is not None
    assert result.stock == 4


def test_metadata_unchanged() -> None:
    """The event never touches title, author or genre."""
    repository = make_repository(make_book(stock=0))
    use_case = ApplyBookReturnedEvent(repository)

    result = use_case(make_event())

    assert result is not None
    assert result.title == "Dune"
    assert result.author == "Frank Herbert"
    assert result.genre == "Sci-Fi"
    assert result.description is None


def test_unregistered_isbn_is_ignored() -> None:
    """An event for an unknown ISBN changes nothing and saves nothing."""
    repository = make_repository(None)
    use_case = ApplyBookReturnedEvent(repository)

    result = use_case(BookReturnedEvent(user_id="bob", isbn="978-1-40-289462-6"))

    assert result is None
    repository.save.assert_not_called()


def test_unregistered_isbn_does_not_raise() -> None:
    """Ignoring an unknown ISBN must not block later events."""
    repository = make_repository(None)
    use_case = ApplyBookReturnedEvent(repository)

    use_case(BookReturnedEvent(user_id="alice", isbn="978-1-40-289462-6"))
    repository.get_by_isbn.return_value = make_book(stock=2)
    result = use_case(make_event())

    assert result is not None
    assert result.stock == 3


def test_event_requires_an_isbn() -> None:
    """A returned event without an ISBN cannot be applied."""
    with pytest.raises(ValueError):
        BookReturnedEvent(user_id="alice", isbn="   ")


def test_return_annotation_is_book_or_none() -> None:
    """The return annotation must evaluate (guards the `Book | None` union)."""
    hints = typing.get_type_hints(ApplyBookReturnedEvent.__call__)

    assert hints["return"] == Book | None
