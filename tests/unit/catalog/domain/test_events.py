"""Unit tests for catalog domain events (CAT-4 BookReturnedEvent)."""

import dataclasses

import pytest

from catalog.domain.events import BookReturnedEvent


def test_event_carries_user_id_and_isbn() -> None:
    """A valid event keeps the user id and ISBN it was built from."""
    event = BookReturnedEvent(user_id="alice", isbn="978-0-20-163361-0")

    assert event.user_id == "alice"
    assert event.isbn == "978-0-20-163361-0"


def test_blank_isbn_is_rejected() -> None:
    """An event with a blank ISBN violates the domain invariant."""
    with pytest.raises(ValueError):
        BookReturnedEvent(user_id="alice", isbn="   ")


def test_empty_isbn_is_rejected() -> None:
    """An event without any ISBN violates the domain invariant."""
    with pytest.raises(ValueError):
        BookReturnedEvent(user_id="alice", isbn="")


def test_event_is_immutable() -> None:
    """Events are frozen value objects and cannot be mutated after creation."""
    event = BookReturnedEvent(user_id="alice", isbn="978-0-20-163361-0")

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.isbn = "978-1-40-289462-6"  # type: ignore[misc]
