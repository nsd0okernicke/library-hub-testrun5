"""FastAPI application for the loans service."""

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine

from loans.application.create_user import CreateUser
from loans.domain.exceptions import EmailAlreadyRegistered
from loans.domain.ports import UserRepository
from loans.domain.user import User
from loans.infrastructure.persistence import Base, SqlAlchemyUserRepository


class CreateUserRequest(BaseModel):
    """Request body for creating a user account."""

    name: str
    email: str


def _user_payload(user: User) -> dict[str, str]:
    """Serialize a user into the API response body."""
    return {"user_id": user.user_id, "name": user.name, "email": user.email}


def create_app(repository: UserRepository) -> FastAPI:
    """Build the loans FastAPI application around the given repository."""
    app = FastAPI(title="Loans Service")
    create_user = CreateUser(repository)

    @app.post("/users", status_code=201)
    def create_user_endpoint(request: CreateUserRequest) -> dict[str, str]:
        """Create a user account (201) or reject a duplicate email (409)."""
        try:
            user = create_user(name=request.name, email=request.email)
        except EmailAlreadyRegistered as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _user_payload(user)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok"}

    return app


def _default_repository() -> SqlAlchemyUserRepository:
    """Build the repository from LOANS_DATABASE_URL."""
    url = os.environ.get(
        "LOANS_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/libraryhub_loans",
    )
    return SqlAlchemyUserRepository(create_engine(url))


def init_db(engine_url: str | None = None) -> None:
    """Create loans tables in the configured database."""
    url = engine_url or os.environ.get(
        "LOANS_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/libraryhub_loans",
    )
    Base.metadata.create_all(create_engine(url))


app = create_app(_default_repository())

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
