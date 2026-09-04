Feature: LOAN-3 - View all loans for a user
  As a library patron
  I want to see a paginated list of all my loans
  So I can review everything I have borrowed and when each loan was created

  Note: the list is paginated with page (1-based, default 1) and page_size (default 20,
  maximum 100). A requested page_size above 100 is capped to 100. Loans are ordered by
  created_at descending (newest first); loans created at the same instant are broken by
  loan_id ascending. Each loan entry contains the loan's loan_id, the book's ISBN and the
  loan's status; an ACTIVE loan's entry additionally contains its due date, while PENDING
  and REJECTED entries contain no due date. A page beyond the last existing page returns
  an empty loan list with status code 200, not an error.

  Background:
    Given the loan service is running

  Scenario: A user's loans are listed newest first
    Given a user <name> with email <email> exists
    And the catalog has books <oldest> <middle> and <newest> registered
    And user <name> has 3 loans for books <oldest>, <middle> and <newest> created in that order
    When user <name> requests page 1 of their loans with page size 10
    Then the request returns status code 200
    And the loans are returned newest first in this order: <newest>, <middle> and <oldest>

  Scenarios:
    | name  | email             | oldest              | middle              | newest              |
    | Alice | alice@example.com | 978-0-20-163361-0   | 978-3-16-148410-0   | 978-0-13-468599-1   |
    | Bob   | bob@example.com   | 978-3-16-148410-0   | 978-0-13-468599-1   | 978-0-20-163361-0   |
    | Carol | carol@example.com | 978-0-13-468599-1   | 978-0-20-163361-0   | 978-3-16-148410-0   |

  Scenario: Loans are paginated by page and page size
    Given a user <name> with email <email> exists
    And user <name> has 4 loans for books <l1>, <l2>, <l3> and <l4> created in that order
    When user <name> requests page <page> of their loans with page size <page_size>
    Then the request returns status code 200
    And the page contains exactly the loans in newest-first order: <expected>

  Scenarios:
    | name  | email             | l1                | l2                | l3                | l4                | page | page_size | expected            |
    | Alice | alice@example.com | 978-0-20-163361-0 | 978-3-16-148410-0 | 978-0-13-468599-1 | 978-3-16-148411-0 | 1    | 2         | l4, l3              |
    | Alice | alice@example.com | 978-0-20-163361-0 | 978-3-16-148410-0 | 978-0-13-468599-1 | 978-3-16-148411-0 | 2    | 2         | l2, l1              |
    | Bob   | bob@example.com   | 978-3-16-148410-0 | 978-0-13-468599-1 | 978-0-20-163361-0 | 978-3-16-148411-0 | 1    | 4         | l4, l3, l2, l1      |

  Scenario: The default is page 1 with page size 20
    Given a user <name> with email <email> exists
    And user <name> has 3 loans for books <b1>, <b2> and <b3> created in that order
    When user <name> requests their loans without pagination parameters
    Then the request returns status code 200
    And the loans are returned newest first in this order: <b3>, <b2> and <b1>

  Scenarios:
    | name  | email             | b1                | b2                | b3                |
    | Alice | alice@example.com | 978-0-20-163361-0 | 978-3-16-148410-0 | 978-0-13-468599-1 |
    | Bob   | bob@example.com   | 978-0-13-468599-1 | 978-3-16-148410-0 | 978-0-20-163361-0 |

  Scenario: A page size above the maximum is capped to 100
    Given a user <name> with email <email> exists
    And user <name> has 120 loans
    When user <name> requests page 1 of their loans with page size 150
    Then the request returns status code 200
    And the page contains exactly 100 loans
    And the page contains the 100 most recently created loans

  Scenarios:
    | name  | email             |
    | Alice | alice@example.com |
    | Bob   | bob@example.com   |

  Scenario: A page beyond the last page is empty
    Given a user <name> with email <email> exists
    And user <name> has 2 loans
    When user <name> requests page 2 of their loans with page size 2
    Then the request returns status code 200
    And the loan list is empty

  Scenarios:
    | name  | email             |
    | Alice | alice@example.com |
    | Bob   | bob@example.com   |

  Scenario: A user without loans gets an empty list
    Given a user <name> with email <email> exists
    When user <name> requests page 1 of their loans with page size 10
    Then the request returns status code 200
    And the loan list is empty

  Scenarios:
    | name  | email             |
    | Alice | alice@example.com |
    | Carol | carol@example.com |

  Scenario: The listing contains only the requested user's loans
    Given a user <name> with email <email> exists
    And a user <other_name> with email <other_email> exists
    And user <name> has a loan for book <own_isbn>
    And user <other_name> has a loan for book <other_isbn>
    When user <name> requests page 1 of their loans with page size 10
    Then the request returns status code 200
    And the listing contains the loan for book <own_isbn>
    And the listing contains no loan for book <other_isbn>

  Scenarios:
    | name  | email             | other_name | other_email     | own_isbn          | other_isbn        |
    | Alice | alice@example.com | Bob        | bob@example.com | 978-0-20-163361-0 | 978-3-16-148410-0 |
    | Bob   | bob@example.com   | Carol      | carol@example.com | 978-0-13-468599-1 | 978-0-20-163361-0 |

  Scenario: Each loan entry contains the loan's details
    Given a user <name> with email <email> exists
    And a book with ISBN <isbn> is registered in the catalog
    And the loan due date term is <term> days
    When user <name> requests to borrow book <isbn>
    And the reservation for the loan is decided as <status>
    And user <name> requests page 1 of their loans with page size 10
    Then the request returns status code 200
    And the entry for book <isbn> contains the loan's loan_id, book <isbn> and status <status>
    And the entry contains a due date only when the loan is ACTIVE

  Scenarios:
    | name  | email             | isbn              | term | status   |
    | Alice | alice@example.com | 978-0-20-163361-0 | 28   | ACTIVE   |
    | Bob   | bob@example.com   | 978-3-16-148410-0 | 28   | PENDING  |
    | Carol | carol@example.com | 978-0-13-468599-1 | 7    | REJECTED |
