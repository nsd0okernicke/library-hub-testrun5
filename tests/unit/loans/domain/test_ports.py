"""Unit tests for the loans port contracts (UserRepository, LoanRepository, EventPublisher)."""

import typing

import pytest

from loans.domain.loan import Loan
from loans.domain.ports import EventPublisher, LoanRepository, UserRepository
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


def test_loan_repository_is_abstract() -> None:
    """The LoanRepository port cannot be instantiated; all methods must be abstract."""
    with pytest.raises(TypeError):
        LoanRepository()  # type: ignore[abstract]
    assert LoanRepository.__abstractmethods__ == frozenset({"save", "get_by_id", "count"})


def test_loan_repository_get_by_id_annotation_resolves() -> None:
    """Force annotation evaluation so `Loan | None` is actually checked (PEP 649)."""
    hints = typing.get_type_hints(LoanRepository.get_by_id)
    assert hints["return"] == (Loan | None)


def test_event_publisher_is_abstract() -> None:
    """The EventPublisher port cannot be instantiated without a publish method."""
    with pytest.raises(TypeError):
        EventPublisher()  # type: ignore[abstract]
    assert EventPublisher.__abstractmethods__ == frozenset({"publish"})
