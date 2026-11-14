import pytest

from app.events import ValidationError, parse_scan_event
from app.publisher import InMemoryPublisher


def _payload(**overrides):
    base = {"tracking_id": "wb0000000042", "status": "in_transit", "hub": "blr-01",
            "scanned_at": "2026-01-05T10:15:00Z"}
    base.update(overrides)
    return base


def test_normalises_case_and_timezone():
    event = parse_scan_event(_payload())
    assert event.tracking_id == "WB0000000042"
    assert event.status == "IN_TRANSIT"
    assert event.hub == "BLR-01"
    assert event.scanned_at == "2026-01-05T10:15:00+00:00"


def test_defaults_scanned_at_when_absent():
    event = parse_scan_event(_payload(scanned_at=None))
    assert event.scanned_at.endswith("+00:00")


@pytest.mark.parametrize("field", ["tracking_id", "status", "hub"])
def test_rejects_missing_field(field):
    with pytest.raises(ValidationError, match="missing fields"):
        parse_scan_event(_payload(**{field: ""}))


def test_rejects_bad_tracking_id():
    with pytest.raises(ValidationError, match="tracking_id"):
        parse_scan_event(_payload(tracking_id="XX123"))


def test_rejects_unknown_status():
    with pytest.raises(ValidationError, match="status must be"):
        parse_scan_event(_payload(status="TELEPORTED"))


def test_rejects_bad_timestamp():
    with pytest.raises(ValidationError, match="ISO-8601"):
        parse_scan_event(_payload(scanned_at="yesterday"))


def test_in_memory_publisher_records_messages():
    publisher = InMemoryPublisher()
    message_id = publisher.publish(parse_scan_event(_payload()))
    assert message_id == "1"
    assert publisher.messages[0]["tracking_id"] == "WB0000000042"
