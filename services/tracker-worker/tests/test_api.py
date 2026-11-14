import base64
import json

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402


def _envelope(event: dict) -> dict:
    return {"message": {"data": base64.b64encode(json.dumps(event).encode()).decode()}}


def test_push_then_read():
    client = TestClient(create_app())
    event = {"tracking_id": "WB0000000042", "status": "PICKED_UP", "hub": "BLR-01",
             "scanned_at": "2026-01-05T10:00:00+00:00"}
    assert client.post("/pubsub/push", json=_envelope(event)).json() == {"outcome": "created"}
    assert client.get("/v1/parcels/wb0000000042").json()["status"] == "PICKED_UP"


def test_malformed_push_returns_400():
    client = TestClient(create_app())
    assert client.post("/pubsub/push", json={"message": {}}).status_code == 400
