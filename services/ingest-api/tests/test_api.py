import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402
from app.publisher import InMemoryPublisher  # noqa: E402


@pytest.fixture()
def client_and_publisher():
    publisher = InMemoryPublisher()
    return TestClient(create_app(publisher)), publisher


def test_health(client_and_publisher):
    client, _ = client_and_publisher
    assert client.get("/healthz").json() == {"status": "ok"}


def test_accepts_valid_scan(client_and_publisher):
    client, publisher = client_and_publisher
    body = {"tracking_id": "WB0000000001", "status": "PICKED_UP", "hub": "BLR-01"}
    response = client.post("/v1/scans", json=body)
    assert response.status_code == 202
    assert len(publisher.messages) == 1


def test_rejects_invalid_scan(client_and_publisher):
    client, publisher = client_and_publisher
    response = client.post("/v1/scans", json={"tracking_id": "nope", "status": "PICKED_UP", "hub": "BLR-01"})
    assert response.status_code == 422
    assert publisher.messages == []
