"""FastAPI application for the loans service."""

import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine

from loans.application.borrow_book import BorrowBook
from loans.application.create_user import CreateUser
from loans.application.decide_reservation import DecideReservation
from loans.domain.exceptions import (
    EmailAlreadyRegistered,
    LoanNotFound,
    LoanNotPending,
    UserNotFound,
)
from loans.domain.loan import Loan, ReservationDecision
from loans.domain.ports import EventPublisher, LoanRepository, UserRepository
from loans.domain.user import User
from loans.infrastructure.config import DEFAULT_DUE_DATE_TERM_DAYS, LoanSettings
from loans.infrastructure.events import NullEventPublisher
from loans.infrastructure.persistence import (
    Base,
    SqlAlchemyLoanRepository,
    SqlAlchemyUserRepository,
)


class CreateUserRequest(BaseModel):
    """Request body for creating a user account."""

    name: str
    email: str


class BorrowRequest(BaseModel):
    """Request body for requesting a book for borrowing."""

    user_email: str
    isbn: str


class ReservationDecisionRequest(BaseModel):
    """Request body for applying the catalog's reservation outcome to a loan."""

    decision: Literal["ACTIVE", "REJECTED"]


def _user_payload(user: User) -> dict[str, str]:
    """Serialize a user into the API response body."""
    return {"user_id": user.user_id, "name": user.name, "email": user.email}


def _loan_payload(loan: Loan) -> dict[str, object]:
    """Serialize a loan into the API response body (datetimes as ISO 8601)."""
    return {
        "loan_id": loan.loan_id,
        "user_id": loan.user_id,
        "isbn": loan.isbn,
        "status": loan.status.value,
        "created_at": loan.created_at.isoformat(),
        "due_date": loan.due_date.isoformat() if loan.due_date is not None else None,
    }


def create_app(
    user_repository: UserRepository,
    loan_repository: LoanRepository,
    publisher: EventPublisher | None = None,
    settings: LoanSettings | None = None,
) -> FastAPI:
    """Build the loans FastAPI application around the given ports.

    The due date term is read from ``settings`` at reservation time, so the
    global configuration value can be adjusted (e.g. in tests) without
    rebuilding the application.
    """
    app = FastAPI(title="Loans Service")
    app.state.settings = settings or LoanSettings(
        due_date_term_days=int(
            os.environ.get("LOANS_DUE_DATE_TERM_DAYS", DEFAULT_DUE_DATE_TERM_DAYS)
        )
    )
    event_publisher: EventPublisher = publisher or NullEventPublisher()
    create_user = CreateUser(user_repository)
    borrow_book = BorrowBook(user_repository, loan_repository, event_publisher)

    @app.post("/users", status_code=201)
    def create_user_endpoint(request: CreateUserRequest) -> dict[str, str]:
        """Create a user account (201) or reject a duplicate email (409)."""
        try:
            user = create_user(name=request.name, email=request.email)
        except EmailAlreadyRegistered as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _user_payload(user)

    @app.post("/loans", status_code=202)
    def borrow_endpoint(request: BorrowRequest) -> dict[str, object]:
        """Accept a borrow request immediately as a PENDING loan (unknown user: 404)."""
        try:
            loan = borrow_book(user_email=request.user_email, isbn=request.isbn)
        except UserNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _loan_payload(loan)

    @app.get("/loans/{loan_id}")
    def get_loan_endpoint(loan_id: str) -> dict[str, object]:
        """Return the loan for its id, in any status (404 when unknown)."""
        loan = loan_repository.get_by_id(loan_id)
        if loan is None:
            raise HTTPException(status_code=404, detail=f"No loan exists with id {loan_id}")
        return _loan_payload(loan)

    @app.post("/loans/{loan_id}/reservation")
    def reservation_endpoint(
        loan_id: str, request: ReservationDecisionRequest
    ) -> dict[str, object]:
        """Apply the reservation outcome to the loan (already decided: 409)."""
        decide = DecideReservation(loan_repository, app.state.settings.due_date_term_days)
        try:
            loan = decide(loan_id=loan_id, decision=ReservationDecision(request.decision))
        except LoanNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except LoanNotPending as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _loan_payload(loan)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok"}

    return app


def _default_engine_url() -> str:
    """Return the configured loans database URL."""
    return os.environ.get(
        "LOANS_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/libraryhub_loans",
    )


def init_db(engine_url: str | None = None) -> None:
    """Create loans tables in the configured database."""
    Base.metadata.create_all(create_engine(engine_url or _default_engine_url()))


def _build_default_app() -> FastAPI:
    """Build the production app from LOANS_DATABASE_URL with a null publisher."""
    engine = create_engine(_default_engine_url())
    return create_app(SqlAlchemyUserRepository(engine), SqlAlchemyLoanRepository(engine))


app = _build_default_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
