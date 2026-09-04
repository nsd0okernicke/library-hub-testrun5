"""Unit tests for the loans User entity (pure Python, no I/O)."""

import dataclasses

import pytest

from loans.domain.user import User


class TestUser:
    def test_user_carries_system_id_name_and_email(self) -> None:
        user = User(user_id="usr-1", name="Alice", email="alice@example.com")
        assert user.user_id == "usr-1"
        assert user.name == "Alice"
        assert user.email == "alice@example.com"

    def test_user_is_immutable(self) -> None:
        user = User(user_id="usr-1", name="Alice", email="alice@example.com")
        with pytest.raises(dataclasses.FrozenInstanceError):
            user.name = "Bob"  # type: ignore[misc]

    def test_equal_users_share_all_fields(self) -> None:
        first = User(user_id="usr-1", name="Alice", email="alice@example.com")
        second = User(user_id="usr-1", name="Alice", email="alice@example.com")
        assert first == second

    def test_blank_name_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            User(user_id="usr-1", name="", email="alice@example.com")

    def test_whitespace_only_name_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            User(user_id="usr-1", name="   ", email="alice@example.com")

    def test_blank_email_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            User(user_id="usr-1", name="Alice", email="")

    def test_whitespace_only_email_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            User(user_id="usr-1", name="Alice", email="   ")

    def test_blank_user_id_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            User(user_id="", name="Alice", email="alice@example.com")

    def test_name_with_special_characters_is_accepted(self) -> None:
        user = User(user_id="usr-1", name="O'Neil", email="oneil@example.org")
        assert user.name == "O'Neil"
