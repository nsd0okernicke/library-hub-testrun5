Feature: LOAN-0 - Create a user account to borrow books
  As a prospective library patron
  I want to create a user account with my name and email
  So I can borrow books under a system-issued identifier

  Note: no password or authentication is involved — name and email alone are sufficient.

  Background:
    Given the loan service is running

  Scenario: A user account is created
    When a user is created with name <name> and email <email>
    Then the account is created with status code 201
    And the account has a system-generated user_id
    And the account has name <name> and email <email>

  Scenarios:
    | name        | email               |
    | Alice       | alice@example.com   |
    | Bob Fischer | bob@example.com     |
    | O'Neil      | oneil@example.org   |

  Scenario: Creating a user with an already registered email is rejected
    Given a user with email <email> already exists
    When a user is created with name <name> and email <email>
    Then the creation is rejected with status code 409
    And no second user with email <email> is registered

  Examples:
    | name  | email             |
    | Alice | alice@example.com |
    | Carol | carol@example.com |

  Scenario: A creation request missing a required field is rejected
    When a user is created with name <name> and email <email>
    Then the creation is rejected with status code 422
    And no user is created

  Examples:
    | name  | email             |
    |       | alice@example.com |
    | Carol |                   |
