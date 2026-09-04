Feature: LOAN-5 - View overdue loans (admin)
  As a library administrator
  I want to view all overdue loans
  So I can follow up on loans whose due date has passed

  Note: a loan is overdue exactly when its status is ACTIVE and its due date lies in the
  past (due_date < now). An ACTIVE loan whose due date is still in the future is not
  overdue, and PENDING, REJECTED and RETURNED loans are never overdue. The endpoint is
  unauthenticated — no access control in the MVP. The response is a list whose order is
  not specified; each entry is identified by its loan_id and contains the loan's loan_id,
  the borrowing user, the book's ISBN and the loan's due date. A listing with no overdue
  loans returns status code 200 with an empty list.

  Background:
    Given the loan service is running

  Scenario: Overdue loans are listed
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And the loan for user <name> and book <isbn> is ACTIVE and overdue by <overdue> days
    When the admin requests the overdue loans
    Then the request returns status code 200
    And the listing contains exactly the loan for user <name> and book <isbn>
    And the entry for that loan contains the loan's loan_id, user <name>, book <isbn> and the loan's due date

  Scenarios:
    | name  | email             | isbn              | overdue |
    | Alice | alice@example.com | 978-0-20-163361-0 | 1       |
    | Bob   | bob@example.com   | 978-3-16-148410-0 | 7       |
    | Carol | carol@example.com | 978-0-13-468599-1 | 30      |

  Scenario: Loans that are not overdue are not listed
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And the loan for user <name> and book <isbn> is <loan_state>
    When the admin requests the overdue loans
    Then the request returns status code 200
    And the loan list is empty

  Scenarios:
    | name  | email             | isbn              | loan_state            |
    | Alice | alice@example.com | 978-0-20-163361-0 | PENDING               |
    | Bob   | bob@example.com   | 978-3-16-148410-0 | REJECTED              |
    | Carol | carol@example.com | 978-0-13-468599-1 | ACTIVE and not overdue |

  Scenario: The listing contains exactly the overdue loans
    Given a user <name> with email <email> exists
    And a user <other_name> with email <other_email> exists
    And a book with ISBN <overdue_isbn> is registered in the catalog
    And a book with ISBN <future_isbn> is registered in the catalog
    And the loan for user <name> and book <overdue_isbn> is ACTIVE and overdue by <overdue> days
    And the loan for user <other_name> and book <future_isbn> is ACTIVE and not overdue
    When the admin requests the overdue loans
    Then the request returns status code 200
    And the listing contains the loan for user <name> and book <overdue_isbn>
    And the listing contains no loan for book <future_isbn>

  Scenarios:
    | name  | email             | other_name | other_email     | overdue_isbn        | future_isbn         | overdue |
    | Alice | alice@example.com | Bob        | bob@example.com | 978-0-20-163361-0   | 978-3-16-148410-0   | 3       |
    | Bob   | bob@example.com   | Carol      | carol@example.com | 978-0-13-468599-1 | 978-0-20-163361-0   | 21      |

  Scenario: No overdue loans gives an empty list
    When the admin requests the overdue loans
    Then the request returns status code 200
    And the loan list is empty

  Scenario: The endpoint requires no authentication
    When the overdue loans are requested without any credentials
    Then the request returns status code 200
    And the loan list is empty
