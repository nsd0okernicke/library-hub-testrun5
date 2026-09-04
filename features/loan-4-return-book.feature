Feature: LOAN-4 - Return a book
  As a library patron
  I want to return a book I borrowed
  So my loan is closed and the catalog knows the book is back

  Note: only an ACTIVE loan can be returned; returning a PENDING, REJECTED or already
  RETURNED loan is a conflict (409) and leaves the loan unchanged. Returning never checks
  overdue status — the MVP has no penalty, so an ACTIVE loan past its due date returns
  just like one before its due date.

  Background:
    Given the loan service is running

  Scenario: An ACTIVE loan is returned and a book returned event is published
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And the loan for user <name> and book <isbn> is ACTIVE
    When user <name> returns the loan
    Then the return request returns status code 200
    And the loan for user <name> and book <isbn> has status RETURNED
    And a book returned event for user <name> and book <isbn> has been published

  Scenarios:
    | name  | email             | isbn              |
    | Alice | alice@example.com | 978-0-20-163361-0 |
    | Bob   | bob@example.com   | 978-3-16-148410-0 |
    | Carol | carol@example.com | 978-0-13-468599-1 |

  Scenario: An ACTIVE loan past its due date is still returned without penalty
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And the loan for user <name> and book <isbn> is ACTIVE and overdue by <overdue> days
    When user <name> returns the loan
    Then the return request returns status code 200
    And the loan for user <name> and book <isbn> has status RETURNED
    And a book returned event for user <name> and book <isbn> has been published

  Scenarios:
    | name  | email             | isbn              | overdue |
    | Alice | alice@example.com | 978-0-20-163361-0 | 1     |
    | Bob   | bob@example.com   | 978-3-16-148410-0 | 15    |

  Scenario: Returning a loan that is not ACTIVE is a conflict and leaves the loan unchanged
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And the loan for user <name> and book <isbn> is <status>
    When user <name> returns the loan
    Then the return request returns status code 409
    And the loan for user <name> and book <isbn> keeps status <status>

  Scenarios:
    | name  | email             | isbn              | status   |
    | Alice | alice@example.com | 978-0-20-163361-0 | PENDING  |
    | Bob   | bob@example.com   | 978-3-16-148410-0 | REJECTED |
    | Carol | carol@example.com | 978-0-13-468599-1 | RETURNED |
