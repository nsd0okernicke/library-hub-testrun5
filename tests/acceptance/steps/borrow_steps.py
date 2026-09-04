"""Acceptance step definitions for features/loan-1-borrow-book.feature.

pytest-bdd 8.x: plain string steps match *exactly*; parameterized steps need an
explicit parser.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "loan-1-borrow-book.feature"))


@then("the borrow request returns status code 202")
def borrow_accepted(scenario_state):
    response = scenario_state["response"]
    assert response.status_code == 202, response.text


@then(
    parsers.parse(
        "a loan with a system-generated loan_id and status PENDING exists"
        " for user {name} and book {isbn}"
    )
)
def pending_loan_exists(loan_client, scenario_state, name, isbn):
    body = scenario_state["response"].json()
    uuid.UUID(body["loan_id"])  # raises unless it is a valid system-style identifier
    assert body["status"] == "PENDING"
    assert _get_loan(loan_client, body["loan_id"])["status"] == "PENDING"
    assert _get_loan(loan_client, body["loan_id"])["isbn"] == isbn
    assert (
        _get_loan(loan_client, body["loan_id"])["user_id"]
        == scenario_state["users"][name]["user_id"]
    )


@then(parsers.parse("a borrow request event for user {name} and book {isbn} has been published"))
def borrow_event_published(loan_client, scenario_state, name, isbn):
    user = scenario_state["users"][name]  # type: ignore[index]
    matching = [
        event
        for event in loan_client.events  # type: ignore[attr-defined]
        if event.user_id == user["user_id"] and event.isbn == isbn
    ]
    assert matching, "no BorrowRequested event was published"
    loan_id = scenario_state["response"].json()["loan_id"]
    assert any(event.loan_id == loan_id for event in matching)


@then(parsers.parse("the loan for user {name} and book {isbn} has status {status}"))
def loan_has_status(loan_client, scenario_state, name, isbn, status):
    loan_id = scenario_state["response"].json()["loan_id"]
    body = _get_loan(loan_client, loan_id)
    assert body["status"] == status
    assert body["isbn"] == isbn
    assert body["user_id"] == scenario_state["users"][name]["user_id"]  # type: ignore[index]


@then(parsers.parse("the loan's due date is {term:d} days after the loan was created"))
def due_date_is_term_after_creation(loan_client, scenario_state, term):
    body = _get_loan(loan_client, scenario_state["response"].json()["loan_id"])
    created = datetime.fromisoformat(body["created_at"])
    due = datetime.fromisoformat(body["due_date"])
    assert due - created == timedelta(days=int(term))


@then("the loan remains queryable with status REJECTED")
def rejected_loan_queryable(loan_client, scenario_state):
    loan_id = scenario_state["response"].json()["loan_id"]
    assert _get_loan(loan_client, loan_id)["status"] == "REJECTED"


@given(parsers.parse("user {name} has an active loan for book {held_isbn}"))
def user_has_active_loan(loan_client, scenario_state, name, held_isbn):
    user = scenario_state["users"][name]  # type: ignore[index]
    response = loan_client.post("/loans", json={"user_email": user["email"], "isbn": held_isbn})
    assert response.status_code == 202, response.text
    loan_id = response.json()["loan_id"]
    decided = loan_client.post(f"/loans/{loan_id}/reservation", json={"decision": "ACTIVE"})
    assert decided.status_code == 200, decided.text
    scenario_state.setdefault("existing_loan_ids", set()).add(loan_id)  # type: ignore[assignment]


@then(parsers.parse("a new loan with status PENDING exists for user {name} and book {isbn}"))
def new_pending_loan_exists(loan_client, scenario_state, name, isbn):
    body = scenario_state["response"].json()
    assert body["status"] == "PENDING"
    uuid.UUID(body["loan_id"])
    existing = scenario_state.get("existing_loan_ids")
    if existing:
        assert body["loan_id"] not in existing
    loan = _get_loan(loan_client, body["loan_id"])
    assert loan["status"] == "PENDING"
    assert loan["isbn"] == isbn
    assert loan["user_id"] == scenario_state["users"][name]["user_id"]  # type: ignore[index]


def _get_loan(loan_client, loan_id: str) -> dict[str, object]:
    response = loan_client.get(f"/loans/{loan_id}")
    assert response.status_code == 200, response.text
    return response.json()
