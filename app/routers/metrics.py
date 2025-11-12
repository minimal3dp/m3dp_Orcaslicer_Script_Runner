"""Metrics endpoint for Prometheus scraping."""

from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """Expose Prometheus metrics for scraping.

    Returns metrics in Prometheus text format for collection by
    Prometheus server or compatible monitoring systems.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
