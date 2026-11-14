"""tracker-worker: receives Pub/Sub push deliveries and keeps parcel state current."""
from __future__ import annotations

import base64
import json
import os

from fastapi import FastAPI, HTTPException

from .tracker import ParcelStore, apply_scan


def create_app(store: ParcelStore | None = None) -> FastAPI:
    app = FastAPI(title="waybill tracker-worker", version=os.getenv("APP_VERSION", "dev"))
    app.state.store = store or ParcelStore()

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.post("/pubsub/push")
    def push(envelope: dict) -> dict:
        try:
            raw = base64.b64decode(envelope["message"]["data"])
            event = json.loads(raw)
            outcome = apply_scan(app.state.store, event)
        except (KeyError, ValueError) as exc:
            # 400 tells Pub/Sub not to retry; the message goes to the dead-letter topic.
            raise HTTPException(status_code=400, detail=f"bad message: {exc}") from exc
        return {"outcome": outcome}

    @app.get("/v1/parcels/{tracking_id}")
    def get_parcel(tracking_id: str) -> dict:
        parcel = app.state.store.get(tracking_id.upper())
        if parcel is None:
            raise HTTPException(status_code=404, detail="unknown tracking id")
        return parcel.__dict__

    return app


app = create_app()
