"""Tests for configuration management."""

import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge import Config


class TestConfig:
    """Test the Config class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config(config_path="/nonexistent/config.yaml")

        assert config.get("workspace", "path") is not None
        assert config.get("logging", "level") == "INFO"
        assert config.get("logging", "rotation", "enabled") is True
        assert config.get("security", "validate_inputs") is True

    def test_workspace_path_property(self):
        """Test workspace_path property."""
        config = Config(config_path="/nonexistent/config.yaml")
        assert isinstance(config.workspace_path, Path)

    def test_agents_config_property(self):
        """Test agents_config property."""
        config = Config(config_path="/nonexistent/config.yaml")
        agents = config.agents_config

        assert "label_github_issue" in agents
        assert "watch_collect" in agents
        assert "analyse_watch_report" in agents
        assert "curate_digest" in agents

        # Check agent structure
        assert "path" in agents["label_github_issue"]
        assert "python" in agents["label_github_issue"]
        assert "timeout" in agents["label_github_issue"]

    def test_get_nested_value(self):
        """Test get method with nested keys."""
        config = Config(config_path="/nonexistent/config.yaml")

        # Existing nested value
        value = config.get("logging", "rotation", "max_bytes")
        assert value == 10485760

        # Non-existing nested value with default
        value = config.get("nonexistent", "key", default="default_value")
        assert value == "default_value"

        # Non-existing without default
        value = config.get("nonexistent", "key")
        assert value is None

    def test_yaml_config_loading(self):
        """Test loading from YAML file."""
        # Create temporary YAML config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
workspace:
  path: /custom/workspace

logging:
  level: DEBUG
  file: /custom/log.log

agents:
  label_github_issue:
    timeout: 600
""")
            temp_path = f.name

        try:
            # Try to load (may fail if PyYAML not installed, which is ok)
            config = Config(config_path=temp_path)

            # If YAML loaded successfully, check custom values
            try:
                import yaml
                assert config.get("workspace", "path") == "/custom/workspace"
                assert config.get("logging", "level") == "DEBUG"
                assert config.get("agents", "label_github_issue", "timeout") == 600
            except ImportError:
                # PyYAML not installed, should use defaults
                pass
        finally:
            Path(temp_path).unlink()

    def test_config_merge(self):
        """Test configuration merging."""
        config = Config(config_path="/nonexistent/config.yaml")

        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 10}, "e": 4}

        config._merge_config(base, override)

        assert base["a"]["b"] == 10  # Overridden
        assert base["a"]["c"] == 2   # Preserved
        assert base["d"] == 3         # Preserved
        assert base["e"] == 4         # Added

    def test_path_expansion(self):
        """Test path expansion."""
        config = Config(config_path="/nonexistent/config.yaml")

        # Paths should be expanded
        workspace = config.get("workspace", "path")
        log_file = config.get("logging", "file")

        assert "~" not in str(workspace)
        assert "~" not in str(log_file)
