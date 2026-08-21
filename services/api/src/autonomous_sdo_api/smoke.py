"""Local smoke checks for the Phase 0D API foundation."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .app import create_app
from .config import Environment, Settings


def main() -> None:
    app = create_app(Settings(service_name="api-smoke", environment=Environment.LOCAL))
    with TestClient(app) as client:
        health = client.get(
            "/api/v1/health/live",
            headers={"X-Correlation-ID": "smoke-run-0001"},
        )
        if health.status_code != 200:
            raise SystemExit(f"health smoke failed: {health.status_code}")
        if health.headers.get("X-Correlation-ID") != "smoke-run-0001":
            raise SystemExit("correlation header smoke failed")
        metrics = client.get("/metrics")
        if metrics.status_code != 200:
            raise SystemExit(f"metrics smoke failed: {metrics.status_code}")
        if "asdo_api_http_requests_total" not in metrics.text:
            raise SystemExit("request metrics smoke failed")


if __name__ == "__main__":
    main()
