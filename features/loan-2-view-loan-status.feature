Feature: LOAN-2 - View single loan status
  As a library patron
  I want to look up the status of a single loan by its loan_id
  So I can check where my borrow request stands

  Note: a loan is looked up by its system-generated loan_id alone — no user or book is
  needed for the lookup. The response reports the loan's current status; a loan whose
  reservation has not been decided yet stays viewable as PENDING. The due date is part of
  the loan details only while the loan is ACTIVE. The RETURNED status appears in this view
  once LOAN-4 adds the return transition.

  Background:
    Given the loan service is running

  Scenario: A pending loan is returned with its details when queried by loan_id
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    When user <name> requests to borrow book <isbn>
    Then the loan for user <name> and book <isbn> is returned by its loan_id with status code 200
    And the response contains the loan's loan_id, user <name>, book <isbn> and status PENDING
    And the response contains no due date

  Scenarios:
    | name  | email             | isbn              |
    | Alice | alice@example.com | 978-0-20-163361-0 |
    | Bob   | bob@example.com   | 978-3-16-148410-0 |
    | Carol | carol@example.com | 978-0-13-468599-1 |

  Scenario: A decided loan is returned with its details when queried by loan_id
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    When user <name> requests to borrow book <isbn>
    And the reservation for the loan is decided as <decision>
    Then the loan for user <name> and book <isbn> is returned by its loan_id with status code 200
    And the response contains the loan's loan_id, user <name>, book <isbn> and status <decision>

  Scenarios:
    | name  | email             | isbn              | decision |
    | Alice | alice@example.com | 978-0-20-163361-0 | ACTIVE   |
    | Bob   | bob@example.com   | 978-0-13-468599-1 | ACTIVE   |
    | Carol | carol@example.com | 978-0-13-468599-1 | REJECTED |

  Scenario: An ACTIVE loan's response contains its due date
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And the loan due date term is <term> days
    When user <name> requests to borrow book <isbn>
    And the reservation for the loan is decided as ACTIVE
    Then the loan for user <name> and book <isbn> is returned by its loan_id with status code 200
    And the response contains the due date <term> days after the loan was created

  Scenarios:
    | name  | email             | isbn              | term |
    | Alice | alice@example.com | 978-0-20-163361-0 | 28   |
    | Bob   | bob@example.com   | 978-3-16-148410-0 | 7    |

  Scenario: A REJECTED loan's response contains no due date
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    When user <name> requests to borrow book <isbn>
    And the reservation for the loan is decided as REJECTED
    Then the loan for user <name> and book <isbn> is returned by its loan_id with status code 200
    And the response contains no due date

  Scenarios:
    | name   | email             | isbn              |
    | Alice  | alice@example.com | 978-3-16-148410-0 |
    | O'Neil | oneil@example.org | 978-0-13-468599-1 |

  Scenario: Querying a loan by an unknown loan_id is not found
    When a loan with loan_id <loan_id> is queried
    Then the request returns status code 404
    And no loan data is returned

  Scenarios:
    | loan_id        |
    | no-such-loan-1 |
    | L-999999       |
