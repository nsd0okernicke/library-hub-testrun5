"""Unit tests for the catalog domain port interfaces."""

import typing

import pytest

from catalog.domain.ports import BookRepository


class TestBookRepositoryPort:
    def test_port_is_abstract(self) -> None:
        """The persistence port must not be instantiable, and every method
        must be abstract (a missing `@abstractmethod` on any one would
        leave the rest abstract by coincidence)."""
        assert BookRepository.__abstractmethods__ == {
            "save",
            "get_by_isbn",
            "count_by_isbn",
            "search",
        }
        with pytest.raises(TypeError):
            BookRepository()

    def test_annotations_are_valid(self) -> None:
        """Public signatures must evaluate (guards the `Book | None` union)."""
        typing.get_type_hints(BookRepository.save)
        typing.get_type_hints(BookRepository.get_by_isbn)
        typing.get_type_hints(BookRepository.count_by_isbn)
        typing.get_type_hints(BookRepository.search)
