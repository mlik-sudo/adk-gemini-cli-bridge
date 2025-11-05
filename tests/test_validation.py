"""Tests for parameter validation."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bridge import Validator, ValidationError


class TestValidator:
    """Test the Validator class."""

    def test_validate_repo_name_valid(self):
        """Test valid repository names."""
        valid_repos = [
            "facebook/react",
            "microsoft/vscode",
            "google/go",
            "user_name/repo-name",
            "org-name/repo.name"
        ]
        for repo in valid_repos:
            result = Validator.validate_repo_name(repo)
            assert result == repo

    def test_validate_repo_name_invalid(self):
        """Test invalid repository names."""
        invalid_repos = [
            "../../../etc/passwd",
            "no-slash",
            "too/many/slashes",
            "has space/repo",
            "repo/has space",
            "repo/with@special",
            "",
            "a/" + "x" * 300  # Too long
        ]
        for repo in invalid_repos:
            with pytest.raises(ValidationError):
                Validator.validate_repo_name(repo)

    def test_validate_repo_name_type_error(self):
        """Test non-string repo names."""
        invalid_types = [123, None, [], {}]
        for value in invalid_types:
            with pytest.raises(ValidationError):
                Validator.validate_repo_name(value)

    def test_validate_issue_number_valid(self):
        """Test valid issue numbers."""
        valid_issues = [1, 42, 123, 999999]
        for issue in valid_issues:
            result = Validator.validate_issue_number(issue)
            assert result == issue
            assert isinstance(result, int)

    def test_validate_issue_number_string_conversion(self):
        """Test string to int conversion."""
        assert Validator.validate_issue_number("123") == 123
        assert Validator.validate_issue_number("1") == 1

    def test_validate_issue_number_invalid(self):
        """Test invalid issue numbers."""
        invalid_issues = [0, -1, -100, 1000000000, "abc", None, []]
        for issue in invalid_issues:
            with pytest.raises(ValidationError):
                Validator.validate_issue_number(issue)

    def test_validate_sources_valid(self):
        """Test valid sources list."""
        valid_sources = [
            ["github"],
            ["github", "pypi"],
            ["github", "pypi", "npm"],
            ["hackernews", "reddit"]
        ]
        for sources in valid_sources:
            result = Validator.validate_sources(sources)
            assert result == sources

    def test_validate_sources_invalid_type(self):
        """Test invalid sources type."""
        with pytest.raises(ValidationError):
            Validator.validate_sources("github")
        with pytest.raises(ValidationError):
            Validator.validate_sources({"source": "github"})

    def test_validate_sources_invalid_source(self):
        """Test invalid source names."""
        with pytest.raises(ValidationError):
            Validator.validate_sources(["invalid_source"])
        with pytest.raises(ValidationError):
            Validator.validate_sources(["github", "invalid"])

    def test_validate_string_param(self):
        """Test string parameter validation."""
        result = Validator.validate_string_param("test", "value")
        assert result == "value"

        result = Validator.validate_string_param("test", "value", max_length=10)
        assert result == "value"

        with pytest.raises(ValidationError):
            Validator.validate_string_param("test", "value", max_length=3)

        with pytest.raises(ValidationError):
            Validator.validate_string_param("test", 123)

    def test_sanitize_string(self):
        """Test string sanitization."""
        # Should remove dangerous characters
        dangerous = "test; rm -rf /"
        sanitized = Validator.sanitize_string(dangerous)
        assert ";" not in sanitized
        assert "rm" in sanitized

        # Should handle shell metacharacters
        meta = "test && echo bad || ls"
        sanitized = Validator.sanitize_string(meta)
        assert "&" not in sanitized
        assert "|" not in sanitized

    def test_validate_params_valid(self):
        """Test parameter dictionary validation."""
        valid_params = {"key": "value", "number": 123}
        result = Validator.validate_params(valid_params)
        assert result == valid_params

    def test_validate_params_too_large(self):
        """Test large parameter payload."""
        large_params = {"key": "x" * 20000}
        with pytest.raises(ValidationError):
            Validator.validate_params(large_params, max_size=10000)

    def test_validate_params_invalid_type(self):
        """Test non-dict params."""
        with pytest.raises(ValidationError):
            Validator.validate_params("not a dict")
        with pytest.raises(ValidationError):
            Validator.validate_params([])
