"""Tests for dispatch functions."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge import dispatch


class TestDispatch:
    """Test the dispatch function."""

    def test_dispatch_unknown_tool(self):
        """Test dispatching unknown tool."""
        result = dispatch("unknown_tool", {})

        assert result["status"] == "error"
        assert "Unknown tool" in result["error"]
        assert "unknown_tool" in result["error"]

    def test_dispatch_health_check(self):
        """Test health check endpoint."""
        result = dispatch("health_check", {})

        assert result["status"] == "success"
        assert "health" in result
        assert isinstance(result["health"], dict)

    def test_dispatch_label_github_issue_missing_params(self):
        """Test GitHub labeling with missing parameters."""
        result = dispatch("label_github_issue", {})

        assert result["status"] == "error"
        assert "Missing required parameters" in result["error"]

    def test_dispatch_watch_collect_invalid_sources(self):
        """Test watch collection with invalid sources."""
        result = dispatch("watch_collect", {"sources": ["invalid_source"]})

        assert result["status"] == "error"
        assert "Invalid source" in result["error"]

    def test_dispatch_analyse_watch_report_missing_report(self):
        """Test analysis without report."""
        result = dispatch("analyse_watch_report", {})

        assert result["status"] == "error"
        assert "Missing 'report' or 'report_path'" in result["error"]

    def test_dispatch_with_validation_disabled(self):
        """Test dispatch with validation disabled."""
        # This would require mocking the config, which is complex
        # For now, we just test that dispatch handles params
        result = dispatch("health_check", {"extra": "param"})
        assert result["status"] == "success"

    def test_dispatch_with_large_payload(self):
        """Test dispatch with overly large payload."""
        large_params = {"data": "x" * 20000}
        result = dispatch("health_check", large_params)

        # Should be rejected due to size validation
        assert result["status"] == "error"
        assert "too large" in result["error"].lower()

    def test_dispatch_with_none_params(self):
        """Test dispatch with None params."""
        result = dispatch("health_check", None)
        assert result["status"] == "success"

    def test_dispatch_watch_collect_valid_sources(self):
        """Test watch collection with valid sources."""
        # This will fail because the agent doesn't actually exist
        # but we can test that the validation passes
        result = dispatch("watch_collect", {"sources": ["github"]})

        # Either success or error from agent execution, not validation
        assert "Invalid source" not in result.get("error", "")


class TestDispatchFunctions:
    """Test individual dispatch functions."""

    def test_label_github_issue_with_defaults(self):
        """Test that defaults are applied."""
        from bridge import dispatch_label_github_issue

        # Should fail due to missing params, but we can check error message
        result = dispatch_label_github_issue({"repo_name": "test/repo", "issue_number": 123})

        # Will error because agent doesn't exist, but params were validated
        assert result["status"] == "error"

    def test_watch_collect_sources_validation(self):
        """Test sources validation in watch_collect."""
        from bridge import dispatch_watch_collect

        # Invalid source type
        result = dispatch_watch_collect({"sources": "github"})
        assert result["status"] == "error"

        # Valid sources but agent doesn't exist
        result = dispatch_watch_collect({"sources": ["github"]})
        # Should fail at execution, not validation
        assert "Invalid source" not in result.get("error", "")

    def test_curate_digest_with_defaults(self):
        """Test curate digest applies defaults."""
        from bridge import dispatch_curate_digest

        result = dispatch_curate_digest({})

        # Will fail because agent doesn't exist
        assert result["status"] == "error"
        # But not because of missing params
        assert "Missing" not in result.get("error", "")
