import pytest

from app.tracker import ParcelStore, apply_scan


def _event(status, at="2026-01-05T10:00:00+00:00", hub="BLR-01"):
    return {"tracking_id": "WB0000000042", "status": status, "hub": hub, "scanned_at": at}


def test_first_scan_creates_parcel():
    store = ParcelStore()
    assert apply_scan(store, _event("PICKED_UP")) == "created"
    assert store.get("WB0000000042").history == ["PICKED_UP"]


def test_forward_scan_updates():
    store = ParcelStore()
    apply_scan(store, _event("PICKED_UP"))
    assert apply_scan(store, _event("IN_TRANSIT", "2026-01-05T12:00:00+00:00", "MAA-02")) == "updated"
    parcel = store.get("WB0000000042")
    assert (parcel.status, parcel.hub) == ("IN_TRANSIT", "MAA-02")


def test_redelivery_is_idempotent():
    store = ParcelStore()
    apply_scan(store, _event("PICKED_UP"))
    assert apply_scan(store, _event("PICKED_UP")) == "duplicate"
    assert store.get("WB0000000042").history == ["PICKED_UP"]


def test_out_of_order_scan_is_ignored():
    store = ParcelStore()
    apply_scan(store, _event("IN_TRANSIT", "2026-01-05T12:00:00+00:00"))
    assert apply_scan(store, _event("PICKED_UP", "2026-01-05T09:00:00+00:00")) == "ignored"
    assert store.get("WB0000000042").status == "IN_TRANSIT"


def test_stale_timestamp_is_ignored():
    store = ParcelStore()
    apply_scan(store, _event("IN_TRANSIT", "2026-01-05T12:00:00+00:00"))
    assert apply_scan(store, _event("OUT_FOR_DELIVERY", "2026-01-05T11:00:00+00:00")) == "ignored"


def test_delivered_is_terminal():
    store = ParcelStore()
    apply_scan(store, _event("DELIVERED"))
    assert apply_scan(store, _event("FAILED_ATTEMPT", "2026-01-06T10:00:00+00:00")) == "ignored"


def test_failed_attempt_can_be_retried():
    store = ParcelStore()
    apply_scan(store, _event("FAILED_ATTEMPT", "2026-01-05T10:00:00+00:00"))
    assert apply_scan(store, _event("OUT_FOR_DELIVERY", "2026-01-06T08:00:00+00:00")) == "updated"


def test_unknown_status_raises():
    with pytest.raises(ValueError):
        apply_scan(ParcelStore(), _event("TELEPORTED"))
