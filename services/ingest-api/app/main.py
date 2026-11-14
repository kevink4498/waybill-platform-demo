"""ingest-api: accepts parcel scan events and publishes them for downstream processing."""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .events import ValidationError, parse_scan_event
from .publisher import InMemoryPublisher, Publisher, PubSubPublisher


def build_publisher() -> Publisher:
    project = os.getenv("GCP_PROJECT_ID")
    topic = os.getenv("SCAN_EVENTS_TOPIC")
    if project and topic:
        return PubSubPublisher(project, topic)
    return InMemoryPublisher()


def create_app(publisher: Publisher | None = None) -> FastAPI:
    app = FastAPI(title="waybill ingest-api", version=os.getenv("APP_VERSION", "dev"))
    app.state.publisher = publisher or build_publisher()

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict:
        return {"status": "ready"}

    @app.post("/v1/scans", status_code=202)
    def ingest(payload: dict) -> dict:
        try:
            event = parse_scan_event(payload)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        message_id = app.state.publisher.publish(event)
        return {"accepted": True, "message_id": message_id, "tracking_id": event.tracking_id}

    return app


app = create_app()
