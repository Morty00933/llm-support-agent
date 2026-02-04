# -*- coding: utf-8 -*-
"""Prometheus metrics definitions."""
from prometheus_client import Counter, Histogram

# HTTP metrics
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

# Celery metrics
TASKS_TOTAL = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["name", "status"],
)

# Integration metrics
INTEGRATION_SYNC_TOTAL = Counter(
    "integration_sync_total",
    "External integration sync results",
    ["system", "status"],
)

# Agent metrics
AGENT_REQUESTS = Counter(
    "agent_requests_total",
    "Total agent requests",
    ["type", "status"],
)

AGENT_LATENCY = Histogram(
    "agent_request_duration_seconds",
    "Agent request latency",
    ["type"],
    buckets=(0.5, 1, 2, 5, 10, 30, 60),
)

# KB metrics
KB_SEARCH_LATENCY = Histogram(
    "kb_search_duration_seconds",
    "Knowledge base search latency",
    buckets=(0.1, 0.25, 0.5, 1, 2, 5),
)

__all__ = [
    "HTTP_REQUESTS",
    "HTTP_LATENCY",
    "TASKS_TOTAL",
    "INTEGRATION_SYNC_TOTAL",
    "AGENT_REQUESTS",
    "AGENT_LATENCY",
    "KB_SEARCH_LATENCY",
]
