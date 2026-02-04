"""
Basic tests for Prometheus metrics module
"""
from src.core.metrics import (
    HTTP_REQUESTS,
    HTTP_LATENCY,
    TASKS_TOTAL,
    AGENT_REQUESTS,
    AGENT_LATENCY,
    KB_SEARCH_LATENCY,
    INTEGRATION_SYNC_TOTAL,
)


class TestMetricsExist:
    """Test that metrics are properly defined"""

    def test_http_requests_counter_exists(self):
        """Test HTTP requests counter is defined"""
        assert HTTP_REQUESTS is not None
        assert HTTP_REQUESTS._name == "http_requests"

    def test_http_latency_histogram_exists(self):
        """Test HTTP latency histogram is defined"""
        assert HTTP_LATENCY is not None
        assert HTTP_LATENCY._name == "http_request_duration_seconds"

    def test_tasks_counter_exists(self):
        """Test Celery tasks counter is defined"""
        assert TASKS_TOTAL is not None
        assert TASKS_TOTAL._name == "celery_tasks"

    def test_agent_requests_counter_exists(self):
        """Test agent requests counter is defined"""
        assert AGENT_REQUESTS is not None
        assert AGENT_REQUESTS._name == "agent_requests"

    def test_agent_latency_histogram_exists(self):
        """Test agent latency histogram is defined"""
        assert AGENT_LATENCY is not None
        assert AGENT_LATENCY._name == "agent_request_duration_seconds"

    def test_kb_search_latency_histogram_exists(self):
        """Test KB search latency histogram is defined"""
        assert KB_SEARCH_LATENCY is not None
        assert KB_SEARCH_LATENCY._name == "kb_search_duration_seconds"

    def test_integration_sync_counter_exists(self):
        """Test integration sync counter is defined"""
        assert INTEGRATION_SYNC_TOTAL is not None
        assert INTEGRATION_SYNC_TOTAL._name == "integration_sync"


class TestMetricsUsage:
    """Test that metrics can be used"""

    def test_http_requests_increment(self):
        """Test incrementing HTTP requests counter"""
        HTTP_REQUESTS.labels(method="GET", path="/test", status="200").inc()

    def test_http_latency_observe(self):
        """Test recording HTTP latency"""
        HTTP_LATENCY.labels(method="POST", path="/api/test").observe(0.5)

    def test_tasks_total_increment(self):
        """Test incrementing tasks counter"""
        TASKS_TOTAL.labels(name="test_task", status="success").inc()

    def test_agent_requests_increment(self):
        """Test incrementing agent requests"""
        AGENT_REQUESTS.labels(type="respond", status="success").inc()

    def test_agent_latency_observe(self):
        """Test recording agent latency"""
        AGENT_LATENCY.labels(type="respond").observe(2.5)

    def test_kb_search_latency_observe(self):
        """Test recording KB search latency"""
        KB_SEARCH_LATENCY.observe(0.3)
