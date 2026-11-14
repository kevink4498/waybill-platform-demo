"""Parcel state machine: decides whether a scan event may move a parcel forward."""
from __future__ import annotations

from dataclasses import dataclass, field

ORDER = {"PICKED_UP": 0, "IN_TRANSIT": 1, "OUT_FOR_DELIVERY": 2, "FAILED_ATTEMPT": 2, "DELIVERED": 3}
TERMINAL = {"DELIVERED"}


@dataclass
class Parcel:
    tracking_id: str
    status: str
    hub: str
    updated_at: str
    history: list[str] = field(default_factory=list)


class ParcelStore:
    """In-memory store. The cluster deployment swaps this for a BigQuery-backed sink."""

    def __init__(self) -> None:
        self._parcels: dict[str, Parcel] = {}

    def get(self, tracking_id: str) -> Parcel | None:
        return self._parcels.get(tracking_id)

    def save(self, parcel: Parcel) -> None:
        self._parcels[parcel.tracking_id] = parcel


def apply_scan(store: ParcelStore, event: dict) -> str:
    """Apply one scan event. Returns 'created', 'updated', 'duplicate' or 'ignored'.

    Pub/Sub delivers at least once and out of order, so the worker must be idempotent
    and must never move a parcel backwards or out of a terminal state.
    """
    tracking_id, status = event["tracking_id"], event["status"]
    if status not in ORDER:
        raise ValueError(f"unknown status {status}")

    current = store.get(tracking_id)
    if current is None:
        store.save(Parcel(tracking_id, status, event["hub"], event["scanned_at"], [status]))
        return "created"

    if current.status == status and current.updated_at == event["scanned_at"]:
        return "duplicate"
    if current.status in TERMINAL or ORDER[status] < ORDER[current.status]:
        return "ignored"
    if event["scanned_at"] < current.updated_at:
        return "ignored"

    current.status, current.hub, current.updated_at = status, event["hub"], event["scanned_at"]
    current.history.append(status)
    store.save(current)
    return "updated"
