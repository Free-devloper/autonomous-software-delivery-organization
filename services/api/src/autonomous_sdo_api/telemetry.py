"""Structured request telemetry, Prometheus metrics and OpenTelemetry traces."""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager, nullcontext
from typing import Any, cast

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

from .config import Settings

_CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:/=-]{8,128}$")
_BEARER_TOKEN_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_CREDENTIAL_URL_PATTERN = re.compile(r"([a-z][a-z0-9+.-]*://)([^/\s:@]+):([^/\s@]+)@")
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key)=([^\s,;]+)"
)


class JsonFormatter(logging.Formatter):
    """Emit machine-readable logs without accepting caller-controlled newlines."""

    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, int | str] = {
            "level": record.levelname,
            "logger": record.name,
            "message": _safe_log_text(record.getMessage()),
        }
        for field in ("correlation_id", "method", "path", "status_code"):
            value = getattr(record, field, None)
            if value is not None:
                event[field] = value if isinstance(value, int) else _safe_log_text(str(value))
        if record.exc_info is not None:
            exception_type = record.exc_info[0]
            exception_value = record.exc_info[1]
            event["exception_type"] = getattr(exception_type, "__name__", "Exception")
            event["exception_message"] = _safe_log_text(str(exception_value))
            event["exception_stack"] = _safe_log_text(self.formatException(record.exc_info))
        return json.dumps(event, sort_keys=True, separators=(",", ":"))


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.handlers = [handler]


class Telemetry:
    def __init__(self, settings: Settings) -> None:
        self.registry = CollectorRegistry()
        self.request_counter = Counter(
            "asdo_api_http_requests_total",
            "HTTP requests handled by the ASDO API.",
            ("method", "route", "status"),
            registry=self.registry,
        )
        self.request_duration = Histogram(
            "asdo_api_http_request_duration_seconds",
            "HTTP request duration by route.",
            ("method", "route"),
            registry=self.registry,
        )
        self.tracer_provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": settings.service_name,
                    "service.version": settings.service_version,
                    "deployment.environment": settings.environment.value,
                }
            )
        )
        if settings.otlp_endpoint is not None:
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint))
            )
        self.tracer = self.tracer_provider.get_tracer("autonomous_sdo_api")
        self.enabled = settings.telemetry_enabled

    def span(self, name: str) -> AbstractContextManager[object]:
        if not self.enabled:
            return nullcontext()
        return self.tracer.start_as_current_span(name)

    def metrics_response(self) -> Response:
        return Response(generate_latest(self.registry), media_type=CONTENT_TYPE_LATEST)


class TelemetryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, telemetry: Telemetry) -> None:
        super().__init__(app)
        self._telemetry = telemetry
        self._logger = logging.getLogger("autonomous_sdo_api.http")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        correlation_id = _correlation_id(request.headers.get("X-Correlation-ID"))
        start = time.perf_counter()
        status_code = 500
        route = "unmatched"
        with self._telemetry.span(f"HTTP {request.method}") as span:
            try:
                response = await call_next(request)
                status_code = response.status_code
                route = _route_label(request)
            except Exception:
                route = _route_label(request)
                self._record_metrics(request.method, route, status_code, start)
                self._logger.exception(
                    "request failed",
                    extra={
                        "correlation_id": correlation_id,
                        "method": request.method,
                        "path": route,
                        "status_code": status_code,
                    },
                )
                raise
            finally:
                if span is not None:
                    active_span = trace.get_current_span()
                    active_span.set_attribute("http.request.method", request.method)
                    active_span.set_attribute("http.route", route)
                    active_span.set_attribute("http.response.status_code", status_code)
                    active_span.set_attribute("asdo.correlation_id", correlation_id)
        self._record_metrics(request.method, route, status_code, start)
        response.headers["X-Correlation-ID"] = correlation_id
        self._logger.info(
            "request completed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": route,
                "status_code": status_code,
            },
        )
        return response

    def _record_metrics(self, method: str, route: str, status_code: int, start: float) -> None:
        duration = time.perf_counter() - start
        self._telemetry.request_counter.labels(
            method,
            route,
            str(status_code),
        ).inc()
        self._telemetry.request_duration.labels(method, route).observe(duration)


def _correlation_id(candidate: str | None) -> str:
    if candidate is not None and _CORRELATION_ID_PATTERN.fullmatch(candidate):
        return candidate
    return f"req-{time.time_ns()}"


def _safe_log_text(value: str) -> str:
    redacted = _CREDENTIAL_URL_PATTERN.sub(r"\1[REDACTED]@", value)
    redacted = _BEARER_TOKEN_PATTERN.sub("Bearer [REDACTED]", redacted)
    redacted = _SECRET_ASSIGNMENT_PATTERN.sub(r"\1=[REDACTED]", redacted)
    return redacted.replace("\r", "\\r").replace("\n", "\\n")


def _route_label(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return "unmatched"


def install_telemetry(app: FastAPI, settings: Settings) -> Telemetry:
    configure_logging(settings.log_level)
    telemetry = Telemetry(settings)
    app.state.telemetry = telemetry
    app.add_middleware(cast(Any, TelemetryMiddleware), telemetry=telemetry)

    if settings.metrics_enabled:

        @app.get("/metrics", include_in_schema=False)
        def metrics() -> Response:
            return telemetry.metrics_response()

    return telemetry
