"""In-process stand-in for the shared message broker (RabbitMQ in production).

Publishing an event synchronously delivers it to every subscriber in the
order they subscribed, mirroring the per-topic delivery the catalog relies
on. The RabbitMQ adapter plugs into the same subscribe/publish boundary.
"""

from collections.abc import Callable

Subscriber = Callable[[object], None]


class InMemoryBroker:
    """In-process message broker: publish(event) fans out to all subscribers."""

    def __init__(self) -> None:
        """Start with no subscribers."""
        self._subscribers: list[Subscriber] = []

    def subscribe(self, handler: Subscriber) -> None:
        """Register a handler that will receive every published event."""
        self._subscribers.append(handler)

    def publish(self, event: object) -> None:
        """Deliver the event to all subscribers, in subscription order."""
        for handler in list(self._subscribers):
            handler(event)
