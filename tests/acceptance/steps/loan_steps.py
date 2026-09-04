"""Acceptance step definitions for features/loan-0-create-user-account.feature.

pytest-bdd 8.x: plain string steps match *exactly*; parameterized steps need an
explicit parser. The When step uses ``parsers.re`` because the Gherkin Examples
table can leave name or email blank.
"""

import uuid
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "loan-0-create-user-account.feature"))


@given(parsers.parse("a user with email {email} already exists"))
def user_with_email_exists(loan_client, email):
    response = loan_client.post("/users", json={"name": "Existing Patron", "email": email})
    assert response.status_code == 201, response.text


@when(parsers.re(r"a user is created with name (?P<name>.*) and email (?P<email>.*)"))
def create_user(loan_client, scenario_state, name, email):
    payload: dict[str, str] = {}
    if name:
        payload["name"] = name
    if email:
        payload["email"] = email
    scenario_state["response"] = loan_client.post("/users", json=payload)


@then(parsers.parse("the account is created with status code {status:d}"))
def account_created_status(scenario_state, status):
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@then("the account has a system-generated user_id")
def account_has_generated_user_id(scenario_state):
    user_id = scenario_state["response"].json()["user_id"]
    assert user_id
    uuid.UUID(user_id)  # raises unless it is a valid system-style identifier


@then(parsers.parse("the account has name {name} and email {email}"))
def account_has_name_and_email(scenario_state, name, email):
    body = scenario_state["response"].json()
    assert body["name"] == name
    assert body["email"] == email


@then(parsers.parse("no second user with email {email} is registered"))
def no_second_user(loan_client, email):
    repository = loan_client.repository  # type: ignore[attr-defined]
    assert repository.count_by_email(email) == 1


@then("no user is created")
def no_user_created(loan_client):
    repository = loan_client.repository  # type: ignore[attr-defined]
    assert repository.count() == 0
