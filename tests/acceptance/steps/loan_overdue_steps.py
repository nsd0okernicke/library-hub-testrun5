"""Acceptance step definitions for features/loan-5-view-overdue-loans.feature.

pytest-bdd 8.x: plain string steps match *exactly*; parameterized steps need an
explicit parser. Step registries are per test module, so the shared Given steps
(create user, register book) live in ``tests/acceptance/conftest.py``; this file
adds the steps specific to viewing the overdue loan listing.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from loans.domain.loan import Loan, LoanStatus, utc_now

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "loan-5-view-overdue-loans.feature"))


def _save_loan(loan_client, scenario_state, name, isbn, status, due_date):
    """Persist a loan in the given state directly through the repository port."""
    user = scenario_state["users"][name]  # type: ignore[index]
    loan = Loan(
        loan_id=str(uuid.uuid4()),
        user_id=user["user_id"],
        isbn=isbn,
        status=status,
        created_at=(due_date - timedelta(days=28)) if status is LoanStatus.ACTIVE else utc_now(),
        due_date=due_date,
    )
    loan_client.loan_repository.save(loan)  # type: ignore[attr-defined]
    return loan


@given(
    parsers.parse("the loan for user {name} and book {isbn} is ACTIVE and overdue by {days:d} days")
)
def loan_is_active_and_overdue(loan_client, scenario_state, name, isbn, days):
    """Shared step: an ACTIVE loan whose due date lies in the past."""
    _save_loan(
        loan_client,
        scenario_state,
        name,
        isbn,
        LoanStatus.ACTIVE,
        utc_now() - timedelta(days=int(days)),
    )


@given(parsers.parse("the loan for user {name} and book {isbn} is ACTIVE and not overdue"))
def loan_is_active_and_not_overdue(loan_client, scenario_state, name, isbn):
    """Shared step: an ACTIVE loan whose due date still lies in the future."""
    _save_loan(
        loan_client, scenario_state, name, isbn, LoanStatus.ACTIVE, utc_now() + timedelta(days=14)
    )


@given(parsers.parse("the loan for user {name} and book {isbn} is PENDING"))
def loan_is_pending(loan_client, scenario_state, name, isbn):
    """Shared step: a pending borrow request that can never be overdue."""
    _save_loan(loan_client, scenario_state, name, isbn, LoanStatus.PENDING, None)


@given(parsers.parse("the loan for user {name} and book {isbn} is REJECTED"))
def loan_is_rejected(loan_client, scenario_state, name, isbn):
    """Shared step: a rejected borrow request that can never be overdue."""
    _save_loan(loan_client, scenario_state, name, isbn, LoanStatus.REJECTED, None)


@when("the admin requests the overdue loans")
@when("the overdue loans are requested without any credentials")
def request_overdue_loans(loan_client, scenario_state):
    """Shared step: request the overdue loan listing (the MVP endpoint is unauthenticated)."""
    scenario_state["response"] = loan_client.get("/loans/overdue")


@then("the request returns status code 200")
def request_returns_200(scenario_state):
    response = scenario_state["response"]
    assert response.status_code == 200, response.text


def _entries(scenario_state) -> list[dict[str, object]]:
    return scenario_state["response"].json()


def _entry_for(scenario_state, name: str, isbn: str) -> dict[str, object] | None:
    user_id = scenario_state["users"][name]["user_id"]  # type: ignore[index]
    for entry in _entries(scenario_state):
        if entry["user_id"] == user_id and entry["isbn"] == isbn:
            return entry
    return None


@then(parsers.parse("the listing contains exactly the loan for user {name} and book {isbn}"))
def listing_contains_exactly(scenario_state, name, isbn):
    entries = _entries(scenario_state)
    expected = _entry_for(scenario_state, name, isbn)
    assert expected is not None, entries
    assert entries == [expected], entries
    scenario_state["overdue_entry"] = expected


@then(
    parsers.parse(
        "the entry for that loan contains the loan's loan_id, user {name}, book {isbn} "
        "and the loan's due date"
    )
)
def entry_contains_loan_details(scenario_state, name, isbn):
    entry = scenario_state["overdue_entry"]
    loan_id = entry["loan_id"]
    assert loan_id
    uuid.UUID(str(loan_id))  # raises unless it is a valid system-style identifier
    assert entry["user_id"] == scenario_state["users"][name]["user_id"]  # type: ignore[index]
    assert entry["isbn"] == isbn
    due_date = datetime.fromisoformat(str(entry["due_date"]))
    assert due_date < utc_now(), entry


@then("the loan list is empty")
def loan_list_is_empty(scenario_state):
    assert _entries(scenario_state) == []


@then(parsers.parse("the listing contains the loan for user {name} and book {isbn}"))
def listing_contains(scenario_state, name, isbn):
    assert _entry_for(scenario_state, name, isbn) is not None, _entries(scenario_state)


@then(parsers.parse("the listing contains no loan for book {isbn}"))
def listing_contains_no_loan_for_book(scenario_state, isbn):
    entries = _entries(scenario_state)
    assert all(entry["isbn"] != isbn for entry in entries), entries
