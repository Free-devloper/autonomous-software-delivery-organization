from __future__ import annotations

import json
import logging
import sys

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.smoke import main as smoke_main
from autonomous_sdo_api.telemetry import JsonFormatter

pytestmark = pytest.mark.unit


def test_metrics_endpoint_records_bounded_route_label_and_correlation_header() -> None:
    app = create_app(Settings(service_name="api-test"))

    with TestClient(app) as client:
        health = client.get(
            "/api/v1/health/live?token=must-not-be-a-label",
            headers={"X-Correlation-ID": "test-correlation-0001"},
        )
        metrics = client.get("/metrics")

    assert health.status_code == 200
    assert health.headers["X-Correlation-ID"] == "test-correlation-0001"
    assert 'route="/api/v1/health/live"' in metrics.text
    assert "must-not-be-a-label" not in metrics.text


def test_invalid_correlation_header_is_replaced() -> None:
    app = create_app(Settings(service_name="api-test"))

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/health/live",
            headers={"X-Correlation-ID": "bad\r\nheader"},
        )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"].startswith("req-")


def test_json_formatter_escapes_control_characters() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="line one\nline two",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "correlation-1"

    rendered = JsonFormatter().format(record)
    parsed = json.loads(rendered)

    assert parsed["message"] == "line one\\nline two"
    assert parsed["correlation_id"] == "correlation-1"


def test_json_formatter_preserves_sanitized_exception_metadata() -> None:
    try:
        raise RuntimeError("failed\nwith forged line")
    except RuntimeError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="request failed",
            args=(),
            exc_info=sys.exc_info(),
        )

    rendered = JsonFormatter().format(record)
    parsed = json.loads(rendered)

    assert parsed["exception_type"] == "RuntimeError"
    assert parsed["exception_message"] == "failed\\nwith forged line"
    assert "RuntimeError: failed\\nwith forged line" in parsed["exception_stack"]
    assert "\n" not in rendered


def test_json_formatter_redacts_common_secret_shapes() -> None:
    try:
        raise RuntimeError(
            "postgresql://user:secret-password@db.example/asdo token=abc123 "
            "Authorization: Bearer eyJhbGciOi"
        )
    except RuntimeError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="password=plain-text-secret",
            args=(),
            exc_info=sys.exc_info(),
        )

    rendered = JsonFormatter().format(record)

    assert "secret-password" not in rendered
    assert "abc123" not in rendered
    assert "eyJhbGciOi" not in rendered
    assert "plain-text-secret" not in rendered
    assert "[REDACTED]" in rendered


def test_otlp_endpoint_rejects_credentials_and_non_http_schemes() -> None:
    with pytest.raises(ValidationError):
        Settings(otlp_endpoint="https://user:password@collector.example.test/v1/traces")
    with pytest.raises(ValidationError):
        Settings(otlp_endpoint="grpc://collector.example.test")


def test_smoke_entrypoint_exercises_health_correlation_and_metrics() -> None:
    smoke_main()
