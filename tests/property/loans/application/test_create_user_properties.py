"""Property tests for the CreateUser use case (mocked repository port)."""

import uuid

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from loans.application.create_user import CreateUser
from loans.domain.exceptions import EmailAlreadyRegistered
from loans.domain.user import User


class FakeUserRepository:
    """In-memory fake of the UserRepository port."""

    def __init__(self) -> None:
        self.users: list[User] = []

    def save(self, user: User) -> None:
        self.users.append(user)

    def get_by_email(self, email: str) -> User | None:
        for user in self.users:
            if user.email == email:
                return user
        return None

    def count_by_email(self, email: str) -> int:
        return sum(1 for user in self.users if user.email == email)

    def count(self) -> int:
        return len(self.users)


email_strategy = st.from_regex(r"[a-z0-9]+@[a-z0-9]+(\.[a-z]{2,4})+", fullmatch=True)


class TestCreateUserProperties:
    @given(name=st.text(min_size=1, max_size=50), email=email_strategy)
    @settings(max_examples=50)
    def test_created_user_preserves_name_and_email_and_gets_a_valid_id(
        self, name: str, email: str
    ) -> None:
        repository = FakeUserRepository()
        result = CreateUser(repository)(name=name, email=email)
        assert result.name == name
        assert result.email == email
        uuid.UUID(result.user_id)
        assert repository.get_by_email(email) is result

    @given(email=email_strategy)
    @settings(max_examples=25)
    def test_second_creation_with_same_email_is_always_rejected(self, email: str) -> None:
        repository = FakeUserRepository()
        use_case = CreateUser(repository)
        use_case(name="Alice", email=email)
        with pytest.raises(EmailAlreadyRegistered):
            use_case(name="Bob", email=email)
        assert repository.count_by_email(email) == 1

    @given(email=email_strategy)
    @settings(max_examples=25)
    def test_rejected_creation_persists_nothing(self, email: str) -> None:
        repository = FakeUserRepository()
        with pytest.raises((ValueError, EmailAlreadyRegistered)):
            CreateUser(repository)(name="", email=email)
        assert repository.count() == 0

    @given(email_a=email_strategy, email_b=email_strategy)
    @settings(max_examples=25)
    def test_distinct_emails_get_distinct_user_ids(self, email_a: str, email_b: str) -> None:
        repository = FakeUserRepository()
        use_case = CreateUser(repository)
        first = use_case(name="Alice", email=email_a)
        if email_b == email_a:
            with pytest.raises(EmailAlreadyRegistered):
                use_case(name="Bob", email=email_b)
            assert repository.count() == 1
        else:
            second = use_case(name="Bob", email=email_b)
            assert first.user_id != second.user_id
