"""Pytest configuration and fixtures."""

import pytest
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_repo_names():
    """Sample valid repository names."""
    return [
        "facebook/react",
        "microsoft/vscode",
        "google/go"
    ]


@pytest.fixture
def sample_issue_numbers():
    """Sample valid issue numbers."""
    return [1, 42, 123, 999]


@pytest.fixture
def sample_sources():
    """Sample valid source lists."""
    return [
        ["github"],
        ["github", "pypi"],
        ["github", "pypi", "npm"]
    ]


@pytest.fixture
def mock_agent_response():
    """Mock successful agent response."""
    return {
        "status": "success",
        "data": "Mock agent output"
    }


@pytest.fixture
def mock_error_response():
    """Mock error response."""
    return {
        "status": "error",
        "error": "Mock error message"
    }
