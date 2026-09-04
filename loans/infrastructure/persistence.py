"""SQLAlchemy persistence for loan user accounts and loans."""

from datetime import datetime

from sqlalchemy import DateTime, String, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from loans.domain.loan import Loan, LoanStatus
from loans.domain.ports import LoanRepository, UserRepository
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


class LoanModel(Base):
    """Table model for loans (one row per loan_id; a user may hold several loans)."""

    __tablename__ = "loans"

    loan_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    isbn: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def to_domain(self) -> Loan:
        """Convert the row into the domain Loan entity."""
        return Loan(
            loan_id=self.loan_id,
            user_id=self.user_id,
            isbn=self.isbn,
            status=LoanStatus(self.status),
            created_at=self.created_at,
            due_date=self.due_date,
        )

    @staticmethod
    def from_domain(loan: Loan) -> "LoanModel":
        """Convert a domain Loan entity into a table row."""
        return LoanModel(
            loan_id=loan.loan_id,
            user_id=loan.user_id,
            isbn=loan.isbn,
            status=loan.status.value,
            created_at=loan.created_at,
            due_date=loan.due_date,
        )


class SqlAlchemyLoanRepository(LoanRepository):
    """LoanRepository backed by a SQLAlchemy engine (one session per call)."""

    def __init__(self, engine: Engine) -> None:
        """Store the SQLAlchemy engine used for persistence."""
        self._engine = engine

    def save(self, loan: Loan) -> None:
        """Insert a new loan or update the existing row for its loan_id."""
        with Session(self._engine) as session, session.begin():
            session.merge(LoanModel.from_domain(loan))

    def get_by_id(self, loan_id: str) -> Loan | None:
        """Return the loan for a loan_id, or None (any status is queryable)."""
        with Session(self._engine) as session:
            row = session.execute(
                select(LoanModel).where(LoanModel.loan_id == loan_id)
            ).scalar_one_or_none()
            return row.to_domain() if row is not None else None

    def count(self) -> int:
        """Return the total number of stored loans."""
        with Session(self._engine) as session:
            return session.execute(select(func.count()).select_from(LoanModel)).scalar_one()
