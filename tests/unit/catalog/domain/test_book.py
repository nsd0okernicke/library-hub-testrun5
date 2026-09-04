"""Unit tests for the catalog domain Book entity."""

import dataclasses
import typing

import pytest

from catalog.domain.book import Book
from catalog.domain.exceptions import BookAlreadyExists


class TestBook:
    def test_book_holds_metadata_and_stock(self) -> None:
        book = Book(
            isbn="978-3-16-148410-0",
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            description="Arrakis saga",
            stock=5,
        )
        assert book.isbn == "978-3-16-148410-0"
        assert book.title == "Dune"
        assert book.author == "Frank Herbert"
        assert book.genre == "Sci-Fi"
        assert book.description == "Arrakis saga"
        assert book.stock == 5

    def test_book_without_description(self) -> None:
        book = Book(
            isbn="978-3-49-961840-5",
            title="Neuromancer",
            author="William Gibson",
            genre="Sci-Fi",
            description=None,
            stock=12,
        )
        assert book.description is None

    def test_book_rejects_blank_isbn(self) -> None:
        with pytest.raises(ValueError):
            Book(
                isbn="   ",
                title="Dune",
                author="Frank Herbert",
                genre="Sci-Fi",
                description=None,
                stock=1,
            )

    def test_book_rejects_negative_stock(self) -> None:
        with pytest.raises(ValueError):
            Book(
                isbn="978-3-16-148410-0",
                title="Dune",
                author="Frank Herbert",
                genre="Sci-Fi",
                description=None,
                stock=-1,
            )

    def test_book_is_immutable(self) -> None:
        book = Book(
            isbn="978-3-16-148410-0",
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            description=None,
            stock=5,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            book.stock = 6  # type: ignore[misc]

    def test_annotations_are_valid(self) -> None:
        """Field annotations must evaluate (guards the `str | None` union)."""
        hints = typing.get_type_hints(Book)
        assert "description" in hints

    def test_book_already_exists_carries_isbn(self) -> None:
        error = BookAlreadyExists("978-3-16-148410-0")
        assert "978-3-16-148410-0" in str(error)


class TestBookAddCopies:
    @pytest.fixture
    def dune(self) -> Book:
        return Book(
            isbn="978-0-20-163361-0",
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            description="Arrakis saga",
            stock=3,
        )

    def test_add_copies_returns_new_book_with_increased_stock(self, dune: Book) -> None:
        updated = dune.add_copies(2)
        assert updated.stock == 5

    def test_add_copies_keeps_all_metadata(self, dune: Book) -> None:
        updated = dune.add_copies(7)
        assert (updated.isbn, updated.title, updated.author, updated.genre) == (
            dune.isbn,
            dune.title,
            dune.author,
            dune.genre,
        )
        assert updated.description == dune.description

    def test_add_copies_does_not_mutate_the_original(self, dune: Book) -> None:
        dune.add_copies(4)
        assert dune.stock == 3

    def test_add_copies_from_zero_stock(self) -> None:
        book = Book(
            isbn="978-3-16-148410-0",
            title="The Hobbit",
            author="J.R.R. Tolkien",
            genre="Fantasy",
            description=None,
            stock=0,
        )
        assert book.add_copies(5).stock == 5

    @pytest.mark.parametrize("amount", [0, -1, -100])
    def test_add_copies_rejects_non_positive_amount(self, dune: Book, amount: int) -> None:
        with pytest.raises(ValueError):
            dune.add_copies(amount)

    def test_add_copies_rejection_message_contains_amount(self, dune: Book) -> None:
        with pytest.raises(ValueError, match="-2"):
            dune.add_copies(-2)
