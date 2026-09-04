Feature: LOAN-1 - Borrow a book
  As a library patron
  I want to request a book for borrowing
  So the loan service tracks the loan while the catalog decides the reservation

  Note: the loan service answers the borrow request immediately (202, PENDING) and only
  learns the reservation result (ACTIVE/REJECTED) later, asynchronously. The loan due
  date term is a single global configuration value (default 28 days); it is not
  overridable per borrow request.

  Background:
    Given the loan service is running

  Scenario: A borrow request is accepted immediately as pending
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    When user <name> requests to borrow book <isbn>
    Then the borrow request returns status code 202
    And a loan with a system-generated loan_id and status PENDING exists for user <name> and book <isbn>
    And a borrow request event for user <name> and book <isbn> has been published

  Scenarios:
    | name  | email             | isbn              |
    | Alice | alice@example.com | 978-0-20-163361-0 |
    | Bob   | bob@example.com   | 978-3-16-148410-0 |
    | Carol | carol@example.com | 978-0-13-468599-1 |

  Scenario: An ACTIVE reservation result activates the loan with the global due date term
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And the loan due date term is <term> days
    When user <name> requests to borrow book <isbn>
    And the reservation for the loan is decided as ACTIVE
    Then the loan for user <name> and book <isbn> has status ACTIVE
    And the loan's due date is <term> days after the loan was created

  Scenarios:
    | name  | email             | isbn              | term |
    | Alice | alice@example.com | 978-0-20-163361-0 | 28   |
    | Bob   | bob@example.com   | 978-3-16-148410-0 | 28   |
    | Carol | carol@example.com | 978-0-13-468599-1 | 7    |

  Scenario: A REJECTED reservation result keeps the loan queryable as rejected
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    When user <name> requests to borrow book <isbn>
    And the reservation for the loan is decided as REJECTED
    Then the loan for user <name> and book <isbn> has status REJECTED
    And the loan remains queryable with status REJECTED

  Scenarios:
    | name   | email             | isbn              |
    | Alice  | alice@example.com | 978-3-16-148410-0 |
    | O'Neil | oneil@example.org | 978-0-20-163361-0 |

  Scenario: A borrow request is not limited by the user's existing active loans
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And user <name> has an active loan for book <held_isbn>
    When user <name> requests to borrow book <isbn>
    Then the borrow request returns status code 202
    And a new loan with status PENDING exists for user <name> and book <isbn>

  Scenarios:
    | name  | email             | held_isbn         | isbn              |
    | Alice | alice@example.com | 978-0-20-163361-0 | 978-0-20-163361-0 |
    | Bob   | bob@example.com   | 978-0-13-468599-1 | 978-3-16-148410-0 |
