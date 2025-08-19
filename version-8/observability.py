"""
Observability configuration for structured logging, metrics, and tracing.
"""
import os
import uuid
import time
import logging
import json
from contextvars import ContextVar
from typing import Optional, Dict, Any

from flask import Flask, request, g, jsonify
from pythonjsonlogger import jsonlogger
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.exceptions import HTTPException

# OpenTelemetry imports
from opentelemetry import trace, baggage
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.propagate import set_global_textmap
# Note: don't import TraceContextTextMapPropagator at module import time because
# some opentelemetry distributions may lack that module. Import it lazily
# inside setup_tracing and fall back to the default propagator if unavailable.

# Context variables for request-scoped data
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar('span_id', default=None)


class ObservabilityConfig:
    """Configuration for observability features."""
    
    def __init__(self):
        self.tracing_enabled = os.getenv('TRACING_ENABLED', 'false').lower() == 'true'
        self.otel_service_name = os.getenv('OTEL_SERVICE_NAME', 'todo-web')
        self.otel_exporter_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://jaeger:4318')
        self.app_env = os.getenv('APP_ENV', 'production')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes observability context."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Always include these base fields
        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['message'] = record.getMessage()
        
        # Add request context if available
        try:
            if hasattr(g, 'request_id'):
                log_record['request_id'] = g.request_id
            elif request_id_var.get():
                log_record['request_id'] = request_id_var.get()
                
            # Add HTTP context if in request context
            if request:
                log_record['http.method'] = request.method
                log_record['http.path'] = request.path
                log_record['client_ip'] = request.environ.get('REMOTE_ADDR')
                log_record['user_agent'] = request.environ.get('HTTP_USER_AGENT')
                
            # Add tracing context if tracing is enabled
            if trace_id_var.get():
                log_record['trace_id'] = trace_id_var.get()
            if span_id_var.get():
                log_record['span_id'] = span_id_var.get()
                
            # Add duration if available
            if hasattr(g, 'start_time'):
                duration_ms = (time.time() - g.start_time) * 1000
                log_record['duration_ms'] = round(duration_ms, 2)
        except RuntimeError:
            # Outside of request context, skip request-specific fields
            pass


def setup_logging(app: Flask, config: ObservabilityConfig) -> None:
    """Configure structured JSON logging."""
    
    # Create JSON formatter
    formatter = CustomJSONFormatter(
        fmt='%(timestamp)s %(level)s %(logger)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add stdout handler with JSON formatting
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Configure Flask app logger
    app.logger.setLevel(getattr(logging, config.log_level))
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    app.logger.addHandler(handler)
    app.logger.propagate = False
    
    # Configure Gunicorn loggers
    gunicorn_logger = logging.getLogger('gunicorn.access')
    gunicorn_logger.setLevel(getattr(logging, config.log_level))
    for handler in gunicorn_logger.handlers[:]:
        gunicorn_logger.removeHandler(handler)
    gunicorn_logger.addHandler(handler)
    
    gunicorn_error_logger = logging.getLogger('gunicorn.error')
    gunicorn_error_logger.setLevel(getattr(logging, config.log_level))
    for handler in gunicorn_error_logger.handlers[:]:
        gunicorn_error_logger.removeHandler(handler)
    gunicorn_error_logger.addHandler(handler)


def setup_tracing(app: Flask, config: ObservabilityConfig) -> None:
    """Configure OpenTelemetry tracing if enabled."""
    
    if not config.tracing_enabled:
        app.logger.info("Tracing is disabled")
        return
        
    try:
        # Set up trace provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        # Set up OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{config.otel_exporter_endpoint}/v1/traces"
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        # Set global propagator (try to import TraceContextTextMapPropagator,
        # otherwise keep whatever default propagator is configured)
        try:
            from opentelemetry.propagators.tracecontext import TraceContextTextMapPropagator
            set_global_textmap(TraceContextTextMapPropagator())
        except Exception:
            app.logger.warning("TraceContextTextMapPropagator not available; using default propagator")

        # Instrument libraries
        FlaskInstrumentor().instrument_app(app)
        RequestsInstrumentor().instrument()
        Psycopg2Instrumentor().instrument()
        RedisInstrumentor().instrument()
        CeleryInstrumentor().instrument()

        app.logger.info(f"Tracing initialized for service '{config.otel_service_name}' to {config.otel_exporter_endpoint}")

    except Exception as e:
        app.logger.error(f"Failed to initialize tracing: {e}")
        # Don't fail the app if tracing setup fails


def setup_metrics(app: Flask, config: ObservabilityConfig) -> PrometheusMetrics:
    """Configure Prometheus metrics."""
    
    # Initialize metrics with custom configuration
    metrics = PrometheusMetrics(app)
    
    # Configure HTTP request histogram with appropriate buckets for web applications
    # Guard against duplicate registration when the module is imported multiple times
    try:
        metrics.info('app_info', 'Application info', version='8.0.0', environment=config.app_env)
    except ValueError:
        # Collector already registered (possible when Celery autodiscovers tasks/imports module multiple times)
        app.logger.debug("Prometheus metric 'app_info' already registered; skipping duplicate registration")
    
    # Custom histogram for request latency (override default)
    histogram_buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]
    
    # Register custom histogram with proper labels (all label values should be callables)
    request_duration_histogram = metrics.histogram(
        'http_request_duration_seconds',
        'HTTP request latency',
        labels={
            'method': lambda: request.method if request else 'unknown',
            'endpoint': lambda: request.endpoint if request else 'unknown',
            'status': lambda: str(getattr(g, 'status_code', 'unknown')),
            'environment': lambda: config.app_env,
        },
        buckets=histogram_buckets
    )

    # Add background job metrics - labels must be a dict of callables according to prometheus_flask_exporter
    try:
        job_counter = metrics.counter(
            'background_jobs_total',
            'Total background jobs',
            labels={
                'status': lambda: str(getattr(g, 'status_code', 'unknown')),
                'job_type': lambda: 'unknown'
            }
        )
    except TypeError:
        # Fallback: register without labels if the exporter version behaves differently
        app.logger.debug("Failed to register job_counter with labels; registering without labels")
        job_counter = metrics.counter('background_jobs_total', 'Total background jobs')

    try:
        job_gauge = metrics.gauge(
            'background_jobs_active',
            'Active background jobs',
            labels={
                'job_type': lambda: 'unknown'
            }
        )
    except TypeError:
        app.logger.debug("Failed to register job_gauge with labels; registering without labels")
        job_gauge = metrics.gauge('background_jobs_active', 'Active background jobs')
    
    app.logger.info("Prometheus metrics initialized")
    
    return metrics


@trace.get_tracer(__name__).start_as_current_span("request_middleware")
def setup_request_middleware(app: Flask, config: ObservabilityConfig) -> None:
    """Set up request middleware for logging and tracing context."""
    
    @app.before_request
    def before_request():
        # Generate request ID
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()
        request_id_var.set(g.request_id)
        
        # Set tracing context if tracing is enabled
        if config.tracing_enabled:
            span = trace.get_current_span()
            if span:
                span_context = span.get_span_context()
                if span_context:
                    trace_id_var.set(format(span_context.trace_id, '032x'))
                    span_id_var.set(format(span_context.span_id, '016x'))
        
        # Log request start
        app.logger.info(f"Request started: {request.method} {request.path}")
    
    @app.after_request
    def after_request(response):
        # Store status code for metrics
        g.status_code = response.status_code
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.request_id
        
        # Add trace parent header if tracing is enabled
        if config.tracing_enabled and trace_id_var.get() and span_id_var.get():
            # Format as W3C traceparent header
            traceparent = f"00-{trace_id_var.get()}-{span_id_var.get()}-01"
            response.headers['traceparent'] = traceparent
        
        # Calculate duration
        duration_ms = (time.time() - g.start_time) * 1000
        
        # Log request completion
        app.logger.info(
            f"Request completed: {request.method} {request.path}",
            extra={
                'status_code': response.status_code,
                'duration_ms': round(duration_ms, 2)
            }
        )
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log errors with full context
        if isinstance(e, HTTPException):
            app.logger.warning(f"HTTP error: {e}")
            return e
        else:
            app.logger.error(f"Unhandled exception: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error', 'request_id': g.get('request_id')}), 500


def init_observability(app: Flask) -> tuple[ObservabilityConfig, PrometheusMetrics]:
    """Initialize all observability features."""
    
    config = ObservabilityConfig()
    
    # Set up logging first
    setup_logging(app, config)
    app.logger.info("Starting observability initialization")
    
    # Set up tracing
    setup_tracing(app, config)
    
    # Set up metrics
    metrics = setup_metrics(app, config)
    
    # Set up request middleware
    setup_request_middleware(app, config)
    
    app.logger.info(f"Observability initialized - tracing: {config.tracing_enabled}, environment: {config.app_env}")
    
    return config, metrics
