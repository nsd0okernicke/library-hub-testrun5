"""Unit tests for the BookAvailability value object."""

import pytest

from catalog.domain.availability import BookAvailability


class TestBookAvailability:
    def test_carries_isbn_and_available_count(self) -> None:
        availability = BookAvailability(isbn="978-0-20-163361-0", available_count=3)
        assert availability.isbn == "978-0-20-163361-0"
        assert availability.available_count == 3

    def test_is_immutable(self) -> None:
        availability = BookAvailability(isbn="978-0-20-163361-0", available_count=3)
        with pytest.raises(AttributeError):
            availability.available_count = 5  # type: ignore[misc]
