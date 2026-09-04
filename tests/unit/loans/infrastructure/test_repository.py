"""Unit tests for the SQLAlchemy user repository (in-process SQLite, no container)."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from loans.domain.user import User
from loans.infrastructure.persistence import Base, SqlAlchemyUserRepository


def _repository() -> SqlAlchemyUserRepository:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return SqlAlchemyUserRepository(engine)


class TestSqlAlchemyUserRepository:
    def test_save_and_get_by_email_round_trip(self) -> None:
        repository = _repository()
        user = User(user_id="usr-1", name="Alice", email="alice@example.com")
        repository.save(user)
        assert repository.get_by_email("alice@example.com") == user

    def test_get_by_unknown_email_returns_none(self) -> None:
        repository = _repository()
        assert repository.get_by_email("nobody@example.com") is None

    def test_count_by_email_counts_registered_users(self) -> None:
        repository = _repository()
        repository.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        assert repository.count_by_email("alice@example.com") == 1
        assert repository.count_by_email("nobody@example.com") == 0

    def test_users_with_different_emails_are_stored_independently(self) -> None:
        repository = _repository()
        repository.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
        repository.save(User(user_id="usr-2", name="Bob", email="bob@example.com"))
        assert repository.count_by_email("alice@example.com") == 1
        assert repository.count_by_email("bob@example.com") == 1
        assert repository.get_by_email("bob@example.com").name == "Bob"
