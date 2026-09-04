"""Acceptance step definitions for features/loan-3-view-user-loans.feature.

pytest-bdd 8.x: plain string steps match *exactly*; parameterized steps need an
explicit parser. Shared Given/When steps (running service, user exists, book
registered, due date term, borrow, decide reservation) live in
``tests/acceptance/conftest.py``. Loan fixtures here insert loans directly via
the exposed repository with distinct, ordered created_at values so "created in
that order" is deterministic.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from loans.domain.loan import Loan, LoanStatus, utc_now

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "loan-3-view-user-loans.feature"))


def _make_loan(user_id: str, isbn: str, created_at: datetime) -> Loan:
    return Loan(
        loan_id=str(uuid.uuid4()),
        user_id=user_id,
        isbn=isbn,
        status=LoanStatus.PENDING,
        created_at=created_at,
        due_date=None,
    )


def _user_id(scenario_state: dict, name: str) -> str:
    return scenario_state["users"][name]["user_id"]  # type: ignore[index]


def _add_loans_in_order(loan_client, scenario_state: dict, name: str, isbns: list[str]) -> None:
    """Insert one PENDING loan per ISBN, created one minute apart in order."""
    repository = loan_client.loan_repository  # type: ignore[attr-defined]
    base = utc_now()
    created: list[str] = scenario_state.setdefault("created_isbns", [])
    for index, isbn in enumerate(isbns):
        loan = _make_loan(
            _user_id(scenario_state, name), isbn, base - timedelta(minutes=len(isbns) - index)
        )
        repository.save(loan)
        created.append(isbn)


def _response_body(scenario_state: dict) -> dict:
    return scenario_state["response"].json()


def _isbns(scenario_state: dict) -> list[str]:
    return [entry["isbn"] for entry in _response_body(scenario_state)["loans"]]


@given(parsers.parse("the catalog has books {first} {second} and {third} registered"))
def catalog_books_registered(client, first, second, third):
    """Register the three books referenced by the ordering scenario."""
    for isbn in (first, second, third):
        response = client.post(
            "/books",
            json={
                "isbn": isbn,
                "title": f"Book {isbn}",
                "author": "Some Author",
                "genre": "Fiction",
                "stock": 1,
            },
        )
        assert response.status_code == 201, response.text


@given(
    parsers.parse(
        "user {name} has {count:d} loans for books {book1}, {book2}"
        " and {book3} created in that order"
    )
)
def user_has_three_loans(loan_client, scenario_state, name, count, book1, book2, book3):
    assert count == 3
    _add_loans_in_order(loan_client, scenario_state, name, [book1, book2, book3])


@given(
    parsers.parse(
        "user {name} has {count:d} loans for books {book1}, {book2}, {book3}"
        " and {book4} created in that order"
    )
)
def user_has_four_loans(loan_client, scenario_state, name, count, book1, book2, book3, book4):
    assert count == 4
    # The feature's expected column references these loans by column name.
    scenario_state["loan_columns"] = {"l1": book1, "l2": book2, "l3": book3, "l4": book4}
    _add_loans_in_order(loan_client, scenario_state, name, [book1, book2, book3, book4])


@given(parsers.parse("user {name} has {count:d} loans"))
def user_has_loans(loan_client, scenario_state, name, count):
    """Insert N PENDING loans with distinct created_at, oldest first."""
    repository = loan_client.loan_repository  # type: ignore[attr-defined]
    user_id = _user_id(scenario_state, name)
    base = utc_now()
    created: list[str] = scenario_state.setdefault("created_isbns", [])
    for index in range(count):
        isbn = f"978-0-20-163361-{count}_{index:03d}"
        loan = _make_loan(user_id, isbn, base - timedelta(minutes=count - index))
        repository.save(loan)
        created.append(isbn)


@given(parsers.parse("user {name} has a loan for book {isbn}"))
def user_has_a_loan(loan_client, scenario_state, name, isbn):
    _add_loans_in_order(loan_client, scenario_state, name, [isbn])


@when(
    parsers.parse("user {name} requests page {page:d} of their loans with page size {page_size:d}")
)
def request_loans_page(loan_client, scenario_state, name, page, page_size):
    user_id = _user_id(scenario_state, name)
    scenario_state["response"] = loan_client.get(
        f"/users/{user_id}/loans", params={"page": page, "page_size": page_size}
    )


@when(parsers.parse("user {name} requests their loans without pagination parameters"))
def request_loans_without_pagination(loan_client, scenario_state, name):
    user_id = _user_id(scenario_state, name)
    scenario_state["response"] = loan_client.get(f"/users/{user_id}/loans")


@then("the request returns status code 200")
def request_returns_200(scenario_state):
    response = scenario_state["response"]
    assert response.status_code == 200, response.text


@then(
    parsers.parse(
        "the loans are returned newest first in this order: {first}, {second} and {third}"
    )
)
def loans_newest_first(scenario_state, first, second, third):
    assert _isbns(scenario_state) == [first, second, third]


@then(parsers.parse("the page contains exactly the loans in newest-first order: {expected}"))
def page_contains_expected_order(scenario_state, expected):
    # The table's expected column names the loan columns (l1..l4); resolve each
    # token to the ISBN recorded under that column name (fall back to the token).
    columns: dict[str, str] = scenario_state.get("loan_columns", {})  # type: ignore[assignment]
    wanted = [columns.get(token.strip(), token.strip()) for token in expected.split(",")]
    assert _isbns(scenario_state) == wanted


@then(parsers.parse("the page contains exactly {count:d} loans"))
def page_contains_count(scenario_state, count):
    assert len(_response_body(scenario_state)["loans"]) == count


@then(parsers.parse("the page contains the {count:d} most recently created loans"))
def page_contains_most_recent(scenario_state, count):
    created: list[str] = scenario_state["created_isbns"]  # oldest first
    most_recent = set(created[-count:])
    assert set(_isbns(scenario_state)) == most_recent


@then("the loan list is empty")
def loan_list_empty(scenario_state):
    assert _response_body(scenario_state)["loans"] == []


@then(parsers.parse("the listing contains the loan for book {isbn}"))
def listing_contains_isbn(scenario_state, isbn):
    assert isbn in _isbns(scenario_state)


@then(parsers.parse("the listing contains no loan for book {isbn}"))
def listing_lacks_isbn(scenario_state, isbn):
    assert isbn not in _isbns(scenario_state)


@then(
    parsers.parse(
        "the entry for book {isbn} contains the loan's loan_id, book {isbn} and status {status}"
    )
)
def entry_contains_loan_details(scenario_state, isbn, status):
    entries = _response_body(scenario_state)["loans"]
    entry = next((e for e in entries if e["isbn"] == isbn), None)
    assert entry is not None, f"no entry for {isbn} in {entries}"
    assert entry["loan_id"]
    assert entry["status"] == status
    scenario_state["entry"] = entry


@then("the entry contains a due date only when the loan is ACTIVE")
def entry_due_date_only_when_active(scenario_state):
    entry = scenario_state["entry"]
    if entry["status"] == "ACTIVE":
        assert entry["due_date"] is not None, entry
    else:
        assert entry["due_date"] is None, entry
