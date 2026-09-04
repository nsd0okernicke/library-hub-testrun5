"""Acceptance step definitions for features/loan-2-view-loan-status.feature.

pytest-bdd 8.x: plain string steps match *exactly*; parameterized steps need an
explicit parser. Step registries are per test module, so the shared Given/When
steps (create user, register book, set due date term, request borrow, decide
reservation) live in ``tests/acceptance/conftest.py``; this file only adds the
steps specific to viewing a single loan by its loan_id.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path

from pytest_bdd import parsers, scenarios, then, when

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "loan-2-view-loan-status.feature"))


@when(parsers.parse("a loan with loan_id {loan_id} is queried"))
def query_loan_by_id(loan_client, scenario_state, loan_id):
    scenario_state["response"] = loan_client.get(f"/loans/{loan_id}")


@then(
    parsers.parse(
        "the loan for user {name} and book {isbn} is returned by its loan_id with status code 200"
    )
)
def loan_returned_by_its_loan_id(loan_client, scenario_state, name, isbn):
    created = scenario_state["response"].json()
    loan_id = created["loan_id"]
    response = loan_client.get(f"/loans/{loan_id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["loan_id"] == loan_id
    assert body["isbn"] == isbn
    assert body["user_id"] == scenario_state["users"][name]["user_id"]  # type: ignore[index]
    scenario_state["loan_response"] = body


@then(
    parsers.parse(
        "the response contains the loan's loan_id, user {name}, book {isbn} and status {status}"
    )
)
def response_contains_loan_details(scenario_state, name, isbn, status):
    body = scenario_state["loan_response"]
    loan_id = body["loan_id"]
    assert loan_id
    uuid.UUID(loan_id)  # raises unless it is a valid system-style identifier
    assert body["user_id"] == scenario_state["users"][name]["user_id"]  # type: ignore[index]
    assert body["isbn"] == isbn
    assert body["status"] == status


@then("the response contains no due date")
def response_has_no_due_date(scenario_state):
    body = scenario_state["loan_response"]
    assert body.get("due_date") is None, body


@then(parsers.parse("the response contains the due date {term:d} days after the loan was created"))
def response_due_date_is_term_after_creation(scenario_state, term):
    body = scenario_state["loan_response"]
    created = datetime.fromisoformat(body["created_at"])
    due = datetime.fromisoformat(body["due_date"])
    assert due - created == timedelta(days=int(term))


@then(parsers.parse("the request returns status code 404"))
def request_returns_404(scenario_state):
    response = scenario_state["response"]
    assert response.status_code == 404, response.text


@then("no loan data is returned")
def no_loan_data_returned(scenario_state):
    body = scenario_state["response"].json()
    assert "loan_id" not in body
    assert "status" not in body
    assert "due_date" not in body
