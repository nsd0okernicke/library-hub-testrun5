"""Unit tests for the CreateUser use case (mocked repository port)."""

import pytest

from loans.application.create_user import CreateUser
from loans.domain.exceptions import EmailAlreadyRegistered
from loans.domain.user import User


class FakeUserRepository:
    """In-memory fake of the UserRepository port."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def save(self, user: User) -> None:
        self.users[user.email] = user

    def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    def count_by_email(self, email: str) -> int:
        return 1 if email in self.users else 0

    def count(self) -> int:
        return len(self.users)


@pytest.fixture
def repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def use_case(repository: FakeUserRepository) -> CreateUser:
    return CreateUser(repository)


class TestCreateUser:
    def test_creates_user_with_system_generated_id(
        self, use_case: CreateUser, repository: FakeUserRepository
    ) -> None:
        result = use_case(name="Alice", email="alice@example.com")
        assert result.name == "Alice"
        assert result.email == "alice@example.com"
        assert result.user_id  # system-generated, non-blank
        assert repository.get_by_email("alice@example.com") is result

    def test_two_users_get_different_ids(self, use_case: CreateUser) -> None:
        first = use_case(name="Alice", email="alice@example.com")
        second = use_case(name="Bob", email="bob@example.com")
        assert first.user_id != second.user_id

    def test_rejects_already_registered_email(
        self, use_case: CreateUser, repository: FakeUserRepository
    ) -> None:
        repository.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        with pytest.raises(EmailAlreadyRegistered):
            use_case(name="Carol", email="alice@example.com")
        assert repository.count_by_email("alice@example.com") == 1
        assert repository.get_by_email("alice@example.com").name == "Alice"

    def test_blank_name_is_rejected(self, use_case: CreateUser) -> None:
        with pytest.raises(ValueError):
            use_case(name="", email="alice@example.com")

    def test_blank_email_is_rejected(self, use_case: CreateUser) -> None:
        with pytest.raises(ValueError):
            use_case(name="Alice", email="")

    def test_nothing_is_persisted_when_creation_is_rejected(
        self, use_case: CreateUser, repository: FakeUserRepository
    ) -> None:
        with pytest.raises(ValueError):
            use_case(name="Alice", email="")
        assert repository.users == {}
