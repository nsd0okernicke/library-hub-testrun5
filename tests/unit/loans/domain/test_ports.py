"""Unit tests for the loans UserRepository port contract."""

import typing

import pytest

from loans.domain.ports import UserRepository
from loans.domain.user import User


def test_user_repository_is_abstract() -> None:
    """The port itself cannot be instantiated; all four methods must be abstract."""
    with pytest.raises(TypeError):
        UserRepository()  # type: ignore[abstract]
    assert UserRepository.__abstractmethods__ == frozenset(
        {"save", "get_by_email", "count_by_email", "count"}
    )


def test_get_by_email_return_annotation_resolves() -> None:
    """Force annotation evaluation so `User | None` is actually checked (PEP 649)."""
    hints = typing.get_type_hints(UserRepository.get_by_email)
    assert hints["return"] == (User | None)


def test_count_methods_return_int() -> None:
    """count_by_email and count must resolve to int return annotations."""
    for method in (UserRepository.count_by_email, UserRepository.count):
        hints = typing.get_type_hints(method)
        assert hints["return"] is int
