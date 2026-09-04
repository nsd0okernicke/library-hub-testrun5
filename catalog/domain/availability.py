"""Lightweight availability snapshot for a registered book."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BookAvailability:
    """The availability answer for one ISBN: the ISBN and its available count.

    Carries no other book details (title, author, genre, description).
    """

    isbn: str
    available_count: int
