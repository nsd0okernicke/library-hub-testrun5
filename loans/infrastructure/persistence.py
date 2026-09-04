"""SQLAlchemy persistence for loan user accounts."""

from sqlalchemy import String, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from loans.domain.ports import UserRepository
from loans.domain.user import User


class Base(DeclarativeBase):
    """Declarative base for loans persistence models."""


class UserModel(Base):
    """Table model for registered user accounts (one row per email)."""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)

    def to_domain(self) -> User:
        """Convert the row into the domain User entity."""
        return User(user_id=self.user_id, name=self.name, email=self.email)


class SqlAlchemyUserRepository(UserRepository):
    """UserRepository backed by a SQLAlchemy engine (one session per call)."""

    def __init__(self, engine: Engine) -> None:
        """Store the SQLAlchemy engine used for persistence."""
        self._engine = engine

    def save(self, user: User) -> None:
        """Persist a new user account."""
        row = UserModel(user_id=user.user_id, name=user.name, email=user.email)
        with Session(self._engine) as session, session.begin():
            session.add(row)

    def get_by_email(self, email: str) -> User | None:
        """Return the registered user for an email, or None."""
        with Session(self._engine) as session:
            row = session.execute(
                select(UserModel).where(UserModel.email == email)
            ).scalar_one_or_none()
            return row.to_domain() if row is not None else None

    def count_by_email(self, email: str) -> int:
        """Return how many users are registered under an email."""
        with Session(self._engine) as session:
            return session.execute(
                select(func.count()).select_from(UserModel).where(UserModel.email == email)
            ).scalar_one()

    def count(self) -> int:
        """Return the total number of registered users."""
        with Session(self._engine) as session:
            return session.execute(select(func.count()).select_from(UserModel)).scalar_one()
