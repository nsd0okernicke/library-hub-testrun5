"""Acceptance step definitions for features/loan-4-return-book.feature.

pytest-bdd 8.x: plain string steps match *exactly*; parameterized steps need an
explicit parser. Step registries are per test module, so the shared Given steps
(create user, register book) live in ``tests/acceptance/conftest.py``; this file
adds the steps specific to returning a loan.
"""

from datetime import timedelta
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from loans.domain.loan import Loan, LoanStatus, utc_now

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "loan-4-return-book.feature"))


def _create_loan(loan_client, scenario_state: dict[str, object], name: str, isbn: str) -> str:
    """Create a PENDING loan for the named user and book; return its loan_id."""
    user = scenario_state["users"][name]  # type: ignore[index]
    response = loan_client.post("/loans", json={"user_email": user["email"], "isbn": isbn})
    assert response.status_code == 202, response.text
    return response.json()["loan_id"]


def _decide_reservation(loan_client, loan_id: str, decision: str) -> None:
    response = loan_client.post(f"/loans/{loan_id}/reservation", json={"decision": decision})
    assert response.status_code == 200, response.text


def _get_loan(loan_client, loan_id: str) -> dict[str, object]:
    response = loan_client.get(f"/loans/{loan_id}")
    assert response.status_code == 200, response.text
    return response.json()


def _remember(scenario_state: dict[str, object], loan_id: str) -> None:
    scenario_state["loan_id"] = loan_id


def _loan_repository(loan_client):
    """The loan repository wired into the TestClient by the conftest fixture."""
    return loan_client.loan_repository  # type: ignore[attr-defined]


@given(parsers.parse("the loan for user {name} and book {isbn} is ACTIVE"))
def loan_is_active(loan_client, scenario_state, name, isbn):
    """Borrow and activate a loan for the named user and book."""
    _remember(scenario_state, _create_loan(loan_client, scenario_state, name, isbn))
    _decide_reservation(loan_client, scenario_state["loan_id"], "ACTIVE")


@given(
    parsers.parse(
        "the loan for user {name} and book {isbn} is ACTIVE and overdue by {overdue:d} days"
    )
)
def loan_is_active_and_overdue(loan_client, scenario_state, name, isbn, overdue):
    """Activate a loan, then age it so its due date lies in the past."""
    _remember(scenario_state, _create_loan(loan_client, scenario_state, name, isbn))
    _decide_reservation(loan_client, scenario_state["loan_id"], "ACTIVE")
    term = int(loan_client.settings.due_date_term_days)  # type: ignore[attr-defined]
    repository = _loan_repository(loan_client)
    loan = repository.get_by_id(scenario_state["loan_id"])
    assert loan is not None
    created_at = utc_now() - timedelta(days=overdue + term)
    aged = Loan(
        loan_id=loan.loan_id,
        user_id=loan.user_id,
        isbn=loan.isbn,
        status=LoanStatus.ACTIVE,
        created_at=created_at,
        due_date=created_at + timedelta(days=term),
    )
    repository.save(aged)
    body = _get_loan(loan_client, scenario_state["loan_id"])
    assert body["status"] == "ACTIVE"


def _loan_in_status(
    loan_client, scenario_state: dict[str, object], name: str, isbn: str, status: str
) -> None:
    """Put a loan for the named user and book into the given non-ACTIVE status."""
    loan_id = _create_loan(loan_client, scenario_state, name, isbn)
    if status == "REJECTED":
        _decide_reservation(loan_client, loan_id, "REJECTED")
    elif status == "RETURNED":
        _decide_reservation(loan_client, loan_id, "ACTIVE")
        returned = loan_client.post(f"/loans/{loan_id}/return")
        assert returned.status_code == 200, returned.text
    # "PENDING" needs no further work: a freshly created loan is PENDING.
    _remember(scenario_state, loan_id)


@given(parsers.parse("the loan for user {name} and book {isbn} is PENDING"))
def loan_is_pending(loan_client, scenario_state, name, isbn):
    _loan_in_status(loan_client, scenario_state, name, isbn, "PENDING")


@given(parsers.parse("the loan for user {name} and book {isbn} is REJECTED"))
def loan_is_rejected(loan_client, scenario_state, name, isbn):
    _loan_in_status(loan_client, scenario_state, name, isbn, "REJECTED")


@given(parsers.parse("the loan for user {name} and book {isbn} is RETURNED"))
def loan_is_returned(loan_client, scenario_state, name, isbn):
    _loan_in_status(loan_client, scenario_state, name, isbn, "RETURNED")


@when(parsers.parse("user {name} returns the loan"))
def user_returns_the_loan(loan_client, scenario_state, name):
    loan_id = scenario_state["loan_id"]
    scenario_state["response"] = loan_client.post(f"/loans/{loan_id}/return")


@then("the return request returns status code 200")
def return_returns_200(scenario_state):
    response = scenario_state["response"]
    assert response.status_code == 200, response.text


@then(parsers.parse("the loan for user {name} and book {isbn} has status RETURNED"))
def loan_has_status_returned(loan_client, scenario_state, name, isbn):
    body = _get_loan(loan_client, scenario_state["loan_id"])
    assert body["status"] == "RETURNED", body
    assert body["isbn"] == isbn
    assert body["user_id"] == scenario_state["users"][name]["user_id"]  # type: ignore[index]


@then(parsers.parse("a book returned event for user {name} and book {isbn} has been published"))
def book_returned_event_published(loan_client, scenario_state, name, isbn):
    user_id = scenario_state["users"][name]["user_id"]  # type: ignore[index]
    matching = [
        event
        for event in loan_client.events  # type: ignore[attr-defined]
        if event.__class__.__name__ == "BookReturned"
        and event.user_id == user_id  # type: ignore[union-attr]
        and event.isbn == isbn  # type: ignore[union-attr]
    ]
    assert matching, "no BookReturned event was published"
    assert any(
        event.loan_id == scenario_state["loan_id"]
        for event in matching  # type: ignore[union-attr]
    )


@then("the return request returns status code 409")
def return_returns_409(scenario_state):
    response = scenario_state["response"]
    assert response.status_code == 409, response.text


@then(parsers.parse("the loan for user {name} and book {isbn} keeps status {status}"))
def loan_keeps_status(loan_client, scenario_state, name, isbn, status):
    body = _get_loan(loan_client, scenario_state["loan_id"])
    assert body["status"] == status, body
    assert body["isbn"] == isbn
    assert body["user_id"] == scenario_state["users"][name]["user_id"]  # type: ignore[index]
