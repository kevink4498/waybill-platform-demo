"""Publisher abstraction: Pub/Sub in the cluster, in-memory in tests and local runs."""
from __future__ import annotations

import json
from typing import Protocol

from .events import ScanEvent


class Publisher(Protocol):
    def publish(self, event: ScanEvent) -> str: ...


class InMemoryPublisher:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def publish(self, event: ScanEvent) -> str:
        self.messages.append(event.to_dict())
        return str(len(self.messages))


class PubSubPublisher:
    """Publishes to Google Pub/Sub. Auth comes from Workload Identity, never a key file."""

    def __init__(self, project_id: str, topic: str) -> None:
        from google.cloud import pubsub_v1  # imported lazily so tests need no GCP libs

        self._client = pubsub_v1.PublisherClient()
        self._topic_path = self._client.topic_path(project_id, topic)

    def publish(self, event: ScanEvent) -> str:
        data = json.dumps(event.to_dict()).encode("utf-8")
        future = self._client.publish(self._topic_path, data, tracking_id=event.tracking_id)
        return future.result(timeout=10)
