"""Property tests for the loans domain User entity."""

import uuid

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from loans.domain.user import User

user_data = st.builds(
    User,
    user_id=st.uuids().map(str),
    name=st.text(min_size=1, max_size=50).filter(str.strip),
    email=st.from_regex(r"[a-z0-9]+@[a-z0-9]+(\.[a-z]{2,4})+", fullmatch=True),
)


class TestUserProperties:
    @given(data=user_data)
    @settings(max_examples=50)
    def test_constructed_user_preserves_all_fields(self, data: User) -> None:
        assert data.user_id.strip()
        assert data.name.strip()
        assert data.email.strip()

    @given(user_id=st.text().filter(lambda v: not v.strip()))
    @settings(max_examples=25)
    def test_blank_user_id_is_always_rejected(self, user_id: str) -> None:
        with pytest.raises(ValueError):
            User(user_id=user_id, name="Alice", email="alice@example.com")

    @given(name=st.text().filter(lambda v: not v.strip()))
    @settings(max_examples=25)
    def test_blank_name_is_always_rejected(self, name: str) -> None:
        with pytest.raises(ValueError):
            User(user_id="usr-1", name=name, email="alice@example.com")

    @given(email=st.text().filter(lambda v: not v.strip()))
    @settings(max_examples=25)
    def test_blank_email_is_always_rejected(self, email: str) -> None:
        with pytest.raises(ValueError):
            User(user_id="usr-1", name="Alice", email=email)

    @given(data=user_data)
    @settings(max_examples=25)
    def test_user_id_is_a_valid_uuid(self, data: User) -> None:
        uuid.UUID(data.user_id)
