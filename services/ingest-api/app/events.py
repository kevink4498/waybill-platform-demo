"""Scan-event model and validation. Pure Python so it is testable without a web stack."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

VALID_STATUSES = ("PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "FAILED_ATTEMPT")
_TRACKING_ID = re.compile(r"^WB[0-9]{10}$")


class ValidationError(ValueError):
    """Raised when a scan event is malformed."""


@dataclass(frozen=True)
class ScanEvent:
    tracking_id: str
    status: str
    hub: str
    scanned_at: str  # ISO-8601, UTC

    def to_dict(self) -> dict:
        return asdict(self)


def parse_scan_event(payload: dict) -> ScanEvent:
    """Validate an incoming payload and return a normalised ScanEvent."""
    missing = [k for k in ("tracking_id", "status", "hub") if not payload.get(k)]
    if missing:
        raise ValidationError(f"missing fields: {', '.join(missing)}")

    tracking_id = str(payload["tracking_id"]).strip().upper()
    if not _TRACKING_ID.match(tracking_id):
        raise ValidationError("tracking_id must look like WB followed by 10 digits")

    status = str(payload["status"]).strip().upper()
    if status not in VALID_STATUSES:
        raise ValidationError(f"status must be one of {', '.join(VALID_STATUSES)}")

    scanned_at = payload.get("scanned_at")
    if scanned_at:
        try:
            parsed = datetime.fromisoformat(str(scanned_at).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("scanned_at must be ISO-8601") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
    else:
        parsed = datetime.now(UTC)

    return ScanEvent(
        tracking_id=tracking_id,
        status=status,
        hub=str(payload["hub"]).strip().upper(),
        scanned_at=parsed.astimezone(UTC).isoformat(),
    )
