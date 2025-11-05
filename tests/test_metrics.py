"""Tests for metrics collection."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge import MetricsCollector


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_record_execution_success(self):
        """Test recording successful execution."""
        collector = MetricsCollector()
        collector.metrics = {}  # Reset metrics

        collector.record_execution("test_agent", 1.5, "success")

        assert "test_agent" in collector.metrics
        metrics = collector.metrics["test_agent"]
        assert metrics["total_calls"] == 1
        assert metrics["success_count"] == 1
        assert metrics["error_count"] == 0
        assert metrics["avg_duration"] == 1.5

    def test_record_execution_error(self):
        """Test recording failed execution."""
        collector = MetricsCollector()
        collector.metrics = {}

        collector.record_execution("test_agent", 0.5, "error", "Test error")

        assert "test_agent" in collector.metrics
        metrics = collector.metrics["test_agent"]
        assert metrics["total_calls"] == 1
        assert metrics["success_count"] == 0
        assert metrics["error_count"] == 1
        assert len(metrics["errors"]) == 1
        assert "Test error" in metrics["errors"][0]["error"]

    def test_record_multiple_executions(self):
        """Test recording multiple executions."""
        collector = MetricsCollector()
        collector.metrics = {}

        collector.record_execution("test_agent", 1.0, "success")
        collector.record_execution("test_agent", 2.0, "success")
        collector.record_execution("test_agent", 1.5, "error", "Error")

        metrics = collector.metrics["test_agent"]
        assert metrics["total_calls"] == 3
        assert metrics["success_count"] == 2
        assert metrics["error_count"] == 1
        assert metrics["avg_duration"] == 1.5  # (1.0 + 2.0 + 1.5) / 3

    def test_get_stats_existing_agent(self):
        """Test getting stats for existing agent."""
        collector = MetricsCollector()
        collector.metrics = {}

        collector.record_execution("test_agent", 1.0, "success")

        stats = collector.get_stats("test_agent")
        assert stats["total_calls"] == 1

    def test_get_stats_nonexistent_agent(self):
        """Test getting stats for non-existent agent."""
        collector = MetricsCollector()
        collector.metrics = {}

        stats = collector.get_stats("nonexistent")
        assert stats == {}

    def test_get_stats_all_agents(self):
        """Test getting stats for all agents."""
        collector = MetricsCollector()
        collector.metrics = {}

        collector.record_execution("agent1", 1.0, "success")
        collector.record_execution("agent2", 2.0, "error", "Error")

        stats = collector.get_stats()
        assert "agent1" in stats
        assert "agent2" in stats

    def test_get_health_status_healthy(self):
        """Test health status when mostly successful."""
        collector = MetricsCollector()
        collector.metrics = {}

        # 9 successes, 1 error = 10% error rate (threshold)
        for _ in range(9):
            collector.record_execution("test_agent", 1.0, "success")
        collector.record_execution("test_agent", 1.0, "error", "Error")

        health = collector.get_health_status()
        assert health["total_calls"] == 10
        assert health["total_errors"] == 1
        assert health["error_rate"] == 0.1

    def test_get_health_status_degraded(self):
        """Test health status when error rate is high."""
        collector = MetricsCollector()
        collector.metrics = {}

        # 2 errors out of 5 = 40% error rate
        collector.record_execution("test_agent", 1.0, "success")
        collector.record_execution("test_agent", 1.0, "success")
        collector.record_execution("test_agent", 1.0, "success")
        collector.record_execution("test_agent", 1.0, "error", "Error 1")
        collector.record_execution("test_agent", 1.0, "error", "Error 2")

        health = collector.get_health_status()
        assert health["status"] == "degraded"
        assert health["error_rate"] == 0.4

    def test_get_health_status_empty(self):
        """Test health status with no metrics."""
        collector = MetricsCollector()
        collector.metrics = {}

        health = collector.get_health_status()
        assert health["total_calls"] == 0
        assert health["total_errors"] == 0
        assert health["error_rate"] == 0.0
        assert health["status"] == "healthy"

    def test_error_truncation(self):
        """Test that errors are truncated."""
        collector = MetricsCollector()
        collector.metrics = {}

        long_error = "x" * 1000
        collector.record_execution("test_agent", 1.0, "error", long_error)

        errors = collector.metrics["test_agent"]["errors"]
        assert len(errors[0]["error"]) == 500  # Truncated to 500 chars

    def test_error_list_limit(self):
        """Test that error list is limited to 100 entries."""
        collector = MetricsCollector()
        collector.metrics = {}

        # Record 150 errors
        for i in range(150):
            collector.record_execution("test_agent", 1.0, "error", f"Error {i}")

        errors = collector.metrics["test_agent"]["errors"]
        assert len(errors) == 100  # Limited to 100

    def test_metrics_disabled(self):
        """Test that metrics can be disabled."""
        collector = MetricsCollector()
        collector.enabled = False
        collector.metrics = {}

        collector.record_execution("test_agent", 1.0, "success")

        # Should not record anything
        assert len(collector.metrics) == 0
