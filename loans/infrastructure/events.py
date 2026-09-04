"""Event publishing adapters for the loans service."""

from loans.domain.ports import EventPublisher


class NullEventPublisher(EventPublisher):
    """Publisher that drops events, used when no message broker is configured."""

    def publish(self, event: object) -> None:
        """Drop the event (no broker configured)."""
