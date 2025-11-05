#!/usr/bin/env python3
"""STDIO bridge : expose les 4 agents ADK comme tools Gemini/Claude

Usage (CLI) :
  python bridge.py watch_collect '{"sources":["github"]}'

Usage (STDIO) :
  echo '{"tool":"watch_collect","params":{}}' | python -u bridge.py

Le script lit une ligne JSON sur stdin, exécute l'agent concerné et
écrit la réponse JSON sur stdout (flush immédiat).
"""

import json
import sys
import signal
import logging
import os
import subprocess
import re
import shlex
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from logging.handlers import RotatingFileHandler

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML not installed. Using default configuration.", file=sys.stderr)

# ---------------------------------------------------------------------------
# 1. Configuration Management -----------------------------------------------
# ---------------------------------------------------------------------------

class Config:
    """Configuration manager with YAML support and environment variables."""

    DEFAULT_CONFIG = {
        "workspace": {
            "path": "~/adk-workspace",
            "global_python": "adk-env/bin/python"
        },
        "logging": {
            "file": "~/.gemini/bridge.log",
            "level": "INFO",
            "rotation": {
                "enabled": True,
                "max_bytes": 10485760,  # 10 MB
                "backup_count": 5
            }
        },
        "agents": {
            "label_github_issue": {
                "path": "github_labeler/main.py",
                "python": "adk-env/bin/python",
                "description": "GitHub Issue Labeler Agent",
                "timeout": 300,
                "defaults": {"dry_run": True}
            },
            "watch_collect": {
                "path": "veille_agent/main.py",
                "python": "veille_agent/.venv/bin/python",
                "description": "Watch/Veille Agent for collecting tech updates",
                "timeout": 600,
                "defaults": {"sources": ["github", "pypi", "npm"], "output_format": "markdown"}
            },
            "analyse_watch_report": {
                "path": "gemini_analysis/main.py",
                "python": "adk-env/bin/python",
                "description": "Gemini Analysis Agent for report analysis",
                "timeout": 300,
                "defaults": {"format": "json"}
            },
            "curate_digest": {
                "path": "curateur_agent/main.py",
                "python": "adk-env/bin/python",
                "description": "Curator Agent for content curation",
                "timeout": 180,
                "defaults": {"format": "newsletter", "output": "markdown"}
            }
        },
        "security": {
            "validate_inputs": True,
            "sanitize_inputs": True,
            "max_param_length": 10000
        },
        "performance": {
            "collect_metrics": True,
            "metrics_retention_days": 30
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from file or defaults."""
        self.config = self.DEFAULT_CONFIG.copy()

        # Try to load from YAML file
        if config_path is None:
            # Look for config.yaml in script directory
            script_dir = Path(__file__).parent
            config_path = script_dir / "config.yaml"

        if YAML_AVAILABLE and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(self.config, user_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}", file=sys.stderr)

        # Override with environment variables
        self._apply_env_overrides()

        # Expand paths
        self._expand_paths()

    def _merge_config(self, base: dict, override: dict):
        """Recursively merge override config into base config."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        if "ADK_WORKSPACE" in os.environ:
            self.config["workspace"]["path"] = os.environ["ADK_WORKSPACE"]

        if "BRIDGE_LOG_LEVEL" in os.environ:
            self.config["logging"]["level"] = os.environ["BRIDGE_LOG_LEVEL"]

        if "BRIDGE_LOG_FILE" in os.environ:
            self.config["logging"]["file"] = os.environ["BRIDGE_LOG_FILE"]

    def _expand_paths(self):
        """Expand ~ and environment variables in paths."""
        self.config["workspace"]["path"] = os.path.expanduser(self.config["workspace"]["path"])
        self.config["logging"]["file"] = os.path.expanduser(self.config["logging"]["file"])

    def get(self, *keys, default=None):
        """Get nested config value."""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    @property
    def workspace_path(self) -> Path:
        """Get workspace path as Path object."""
        return Path(self.config["workspace"]["path"])

    @property
    def agents_config(self) -> Dict[str, Any]:
        """Get agents configuration."""
        return self.config["agents"]

# Global configuration instance
config = Config()

# ---------------------------------------------------------------------------
# 2. Security & Validation --------------------------------------------------
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when parameter validation fails."""
    pass

class Validator:
    """Parameter validation and sanitization."""

    # Regex patterns for validation
    REPO_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$')
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9_./\- ]+$')

    @staticmethod
    def validate_repo_name(repo: str) -> str:
        """Validate GitHub repository name format (owner/repo)."""
        if not isinstance(repo, str):
            raise ValidationError(f"repo_name must be a string, got {type(repo).__name__}")

        if len(repo) > 200:
            raise ValidationError("repo_name is too long (max 200 characters)")

        if not Validator.REPO_NAME_PATTERN.match(repo):
            raise ValidationError(
                f"Invalid repo_name format: '{repo}'. Expected format: 'owner/repo'"
            )

        return repo

    @staticmethod
    def validate_issue_number(issue: Any) -> int:
        """Validate and convert issue number to positive integer."""
        try:
            num = int(issue)
            if num <= 0:
                raise ValidationError("issue_number must be a positive integer")
            if num > 999999999:  # Sanity check
                raise ValidationError("issue_number is too large")
            return num
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid issue_number: {e}")

    @staticmethod
    def validate_sources(sources: Any) -> list:
        """Validate sources list."""
        if not isinstance(sources, list):
            raise ValidationError(f"sources must be a list, got {type(sources).__name__}")

        allowed_sources = {"github", "pypi", "npm", "reddit", "hackernews"}
        for source in sources:
            if not isinstance(source, str):
                raise ValidationError(f"source must be a string, got {type(source).__name__}")
            if source not in allowed_sources:
                raise ValidationError(
                    f"Invalid source '{source}'. Allowed: {allowed_sources}"
                )

        return sources

    @staticmethod
    def validate_string_param(name: str, value: Any, max_length: int = None) -> str:
        """Validate string parameter."""
        if not isinstance(value, str):
            raise ValidationError(f"{name} must be a string, got {type(value).__name__}")

        if max_length and len(value) > max_length:
            raise ValidationError(f"{name} is too long (max {max_length} characters)")

        return value

    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string to prevent injection attacks."""
        # Remove any control characters and potential shell metacharacters
        sanitized = re.sub(r'[;\|&$`\(\)<>]', '', value)
        return shlex.quote(sanitized)

    @staticmethod
    def validate_params(params: dict, max_size: int = 10000) -> dict:
        """Validate overall parameters dictionary."""
        if not isinstance(params, dict):
            raise ValidationError("params must be a dictionary")

        # Check overall size
        params_json = json.dumps(params)
        if len(params_json) > max_size:
            raise ValidationError(f"params payload is too large (max {max_size} bytes)")

        return params

# ---------------------------------------------------------------------------
# 3. Logging Setup ----------------------------------------------------------
# ---------------------------------------------------------------------------

def setup_logging(config: Config) -> logging.Logger:
    """Configure logging with rotation support."""
    log_file = config.get("logging", "file")
    log_level = config.get("logging", "level", default="INFO")
    rotation_enabled = config.get("logging", "rotation", "enabled", default=True)

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logger
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, log_level))

    # Clear any existing handlers
    logger.handlers.clear()

    # Setup file handler with optional rotation
    if rotation_enabled:
        max_bytes = config.get("logging", "rotation", "max_bytes", default=10485760)
        backup_count = config.get("logging", "rotation", "backup_count", default=5)
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
    else:
        handler = logging.FileHandler(log_file)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = setup_logging(config)

# ---------------------------------------------------------------------------
# 4. Metrics Collection -----------------------------------------------------
# ---------------------------------------------------------------------------

class MetricsCollector:
    """Collect and track agent execution metrics."""

    def __init__(self):
        self.metrics = {}
        self.enabled = config.get("performance", "collect_metrics", default=True)

    def record_execution(self, agent: str, duration: float, status: str, error: str = None):
        """Record agent execution metrics."""
        if not self.enabled:
            return

        if agent not in self.metrics:
            self.metrics[agent] = {
                "total_calls": 0,
                "success_count": 0,
                "error_count": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "last_execution": None,
                "errors": []
            }

        m = self.metrics[agent]
        m["total_calls"] += 1
        m["total_duration"] += duration
        m["avg_duration"] = m["total_duration"] / m["total_calls"]
        m["last_execution"] = time.time()

        if status == "success":
            m["success_count"] += 1
        else:
            m["error_count"] += 1
            if error and len(m["errors"]) < 100:  # Keep last 100 errors
                m["errors"].append({
                    "timestamp": time.time(),
                    "error": error[:500]  # Truncate long errors
                })

    def get_stats(self, agent: str = None) -> dict:
        """Get metrics statistics."""
        if agent:
            return self.metrics.get(agent, {})
        return self.metrics

    def get_health_status(self) -> dict:
        """Get overall health status."""
        total_calls = sum(m["total_calls"] for m in self.metrics.values())
        total_errors = sum(m["error_count"] for m in self.metrics.values())

        return {
            "status": "healthy" if total_errors / max(total_calls, 1) < 0.1 else "degraded",
            "total_calls": total_calls,
            "total_errors": total_errors,
            "error_rate": total_errors / max(total_calls, 1),
            "agents": {name: {
                "calls": m["total_calls"],
                "success_rate": m["success_count"] / max(m["total_calls"], 1),
                "avg_duration": m["avg_duration"]
            } for name, m in self.metrics.items()}
        }

metrics = MetricsCollector()

# ---------------------------------------------------------------------------
# 5. Agent Execution Functions ----------------------------------------------
# ---------------------------------------------------------------------------

def get_agent_config(agent_name: str) -> Tuple[Path, Path, int]:
    """Get agent configuration (script path, python path, timeout)."""
    agents_config = config.agents_config

    if agent_name not in agents_config:
        raise ValueError(f"Unknown agent: {agent_name}")

    agent_cfg = agents_config[agent_name]
    workspace = config.workspace_path

    agent_path = workspace / agent_cfg["path"]
    python_path = workspace / agent_cfg["python"]
    timeout = agent_cfg.get("timeout", 300)

    return agent_path, python_path, timeout

def run_agent_script(agent_name: str, params: dict) -> dict:
    """Execute an ADK agent Python script with parameters."""
    start_time = time.time()

    try:
        # Get agent configuration
        agent_path, python_path, timeout = get_agent_config(agent_name)

        # Check if the Python interpreter exists
        if not python_path.exists():
            error_msg = f"Python interpreter not found: {python_path}"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg}

        # Check if agent script exists
        if not agent_path.exists():
            error_msg = f"Agent script not found: {agent_path}"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg}

        # Prepare the environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(config.workspace_path)

        # Build command with validated parameters
        cmd = [str(python_path), str(agent_path)]

        # Add validated command line arguments
        if "issue_number" in params:
            validated_issue = Validator.validate_issue_number(params["issue_number"])
            cmd.extend(["--issue", str(validated_issue)])

        if "repo_name" in params:
            validated_repo = Validator.validate_repo_name(params["repo_name"])
            cmd.extend(["--repo", validated_repo])

        if "dry_run" in params and params["dry_run"]:
            cmd.append("--dry-run")

        logger.info(f"Executing agent {agent_name}: {' '.join(cmd)}")

        # Execute the agent
        result = subprocess.run(
            cmd,
            input=json.dumps(params),
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout) if result.stdout.strip() else {"status": "success", "output": result.stdout}
                logger.info(f"Agent {agent_name} completed successfully in {duration:.2f}s")
                metrics.record_execution(agent_name, duration, "success")
                return output
            except json.JSONDecodeError as e:
                logger.warning(f"Agent {agent_name} returned invalid JSON: {e}")
                # This is actually an error - invalid JSON from agent
                error_msg = f"Agent returned invalid JSON: {e}"
                metrics.record_execution(agent_name, duration, "error", error_msg)
                return {"status": "error", "error": error_msg, "output": result.stdout}
        else:
            error_msg = result.stderr or f"Process failed with code {result.returncode}"
            logger.error(f"Agent {agent_name} failed: {error_msg}")
            metrics.record_execution(agent_name, duration, "error", error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "stdout": result.stdout
            }

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        error_msg = f"Agent execution timed out after {timeout}s"
        logger.error(f"Agent {agent_name} timed out")
        metrics.record_execution(agent_name, duration, "error", error_msg)
        return {"status": "error", "error": error_msg}

    except ValidationError as e:
        duration = time.time() - start_time
        error_msg = f"Validation error: {e}"
        logger.error(f"Agent {agent_name} validation failed: {e}")
        metrics.record_execution(agent_name, duration, "error", error_msg)
        return {"status": "error", "error": error_msg}

    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        logger.exception(f"Error running agent {agent_name}")
        metrics.record_execution(agent_name, duration, "error", error_msg)
        return {"status": "error", "error": error_msg}

# ---------------------------------------------------------------------------
# 6. Dispatch Functions -----------------------------------------------------
# ---------------------------------------------------------------------------

def dispatch_label_github_issue(params: dict) -> dict:
    """Handle GitHub issue labeling."""
    # Validate required parameters
    required_params = ["repo_name", "issue_number"]
    missing = [p for p in required_params if p not in params]
    if missing:
        return {"status": "error", "error": f"Missing required parameters: {missing}"}

    # Apply defaults
    defaults = config.get("agents", "label_github_issue", "defaults", default={})
    merged_params = {**defaults, **params}

    return run_agent_script("label_github_issue", merged_params)

def dispatch_watch_collect(params: dict) -> dict:
    """Handle watch/veille collection."""
    # Validate sources if provided
    if "sources" in params:
        try:
            params["sources"] = Validator.validate_sources(params["sources"])
        except ValidationError as e:
            return {"status": "error", "error": str(e)}

    # Apply defaults
    defaults = config.get("agents", "watch_collect", "defaults", default={})
    merged_params = {**defaults, **params}

    return run_agent_script("watch_collect", merged_params)

def dispatch_analyse_watch_report(params: dict) -> dict:
    """Handle watch report analysis."""
    if "report" not in params and "report_path" not in params:
        return {"status": "error", "error": "Missing 'report' or 'report_path' parameter"}

    # Apply defaults
    defaults = config.get("agents", "analyse_watch_report", "defaults", default={})
    merged_params = {**defaults, **params}

    return run_agent_script("analyse_watch_report", merged_params)

def dispatch_curate_digest(params: dict) -> dict:
    """Handle content curation."""
    # Apply defaults
    defaults = config.get("agents", "curate_digest", "defaults", default={})
    merged_params = {**defaults, **params}

    return run_agent_script("curate_digest", merged_params)

def dispatch_health_check(params: dict) -> dict:
    """Return health status and metrics."""
    return {
        "status": "success",
        "health": metrics.get_health_status()
    }

# ---------------------------------------------------------------------------
# 7. Main Dispatch Function -------------------------------------------------
# ---------------------------------------------------------------------------

def dispatch(tool: str, params: dict = None) -> dict:
    """Main dispatch function for all agents."""
    if params is None:
        params = {}

    logger.info(f"Dispatching tool: {tool} with params: {params}")

    # Validate parameters if security is enabled
    if config.get("security", "validate_inputs", default=True):
        try:
            max_length = config.get("security", "max_param_length", default=10000)
            params = Validator.validate_params(params, max_length)
        except ValidationError as e:
            logger.error(f"Parameter validation failed: {e}")
            return {"status": "error", "error": f"Validation error: {e}"}

    dispatchers = {
        "label_github_issue": dispatch_label_github_issue,
        "watch_collect": dispatch_watch_collect,
        "analyse_watch_report": dispatch_analyse_watch_report,
        "curate_digest": dispatch_curate_digest,
        "health_check": dispatch_health_check,
    }

    if tool not in dispatchers:
        available_tools = list(dispatchers.keys())
        error_msg = f"Unknown tool '{tool}'. Available tools: {available_tools}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }

    try:
        result = dispatchers[tool](params)
        status = result.get('status', 'unknown')
        logger.info(f"Tool {tool} completed with status: {status}")
        return result
    except Exception as e:
        logger.exception(f"Error in dispatch for tool {tool}")
        return {"status": "error", "error": str(e)}

# ---------------------------------------------------------------------------
# 8. Signal Handlers --------------------------------------------------------
# ---------------------------------------------------------------------------

def _signal_handler(_sig, _frm):
    """Handle termination signals gracefully."""
    logger.info("Bridge process terminated by signal")
    sys.exit(0)

signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)

# ---------------------------------------------------------------------------
# 9. Main Execution ---------------------------------------------------------
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the bridge."""
    logger.info("Bridge started")
    logger.info(f"Workspace: {config.workspace_path}")
    logger.info(f"Configuration loaded from: {Path(__file__).parent / 'config.yaml'}")

    # Support direct command line calls: python bridge.py <tool> <json_params>
    if len(sys.argv) >= 2 and sys.argv[1] != "-":
        tool_name = sys.argv[1]
        params_json = sys.argv[2] if len(sys.argv) > 2 else "{}"

        try:
            params = json.loads(params_json)
            result = dispatch(tool_name, params)
            print(json.dumps(result, indent=2), flush=True)
        except json.JSONDecodeError as e:
            error_result = {"status": "error", "error": f"Invalid JSON parameters: {e}"}
            print(json.dumps(error_result, indent=2), flush=True)
            sys.exit(1)
        except Exception as e:
            error_result = {"status": "error", "error": str(e)}
            print(json.dumps(error_result, indent=2), flush=True)
            sys.exit(1)

        return

    # STDIO mode for Gemini CLI / Claude Code
    logger.info("Entering STDIO mode")

    try:
        for line_num, line in enumerate(sys.stdin, 1):
            line = line.strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
                tool = payload.get("tool")
                params = payload.get("params", {})

                if not tool:
                    result = {"status": "error", "error": "Missing 'tool' in payload"}
                else:
                    result = dispatch(tool, params)

                print(json.dumps(result), flush=True)

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error on line {line_num}: {e}")
                error_result = {"status": "error", "error": f"Invalid JSON on line {line_num}: {e}"}
                print(json.dumps(error_result), flush=True)
            except Exception as e:
                logger.exception(f"Unexpected error on line {line_num}")
                error_result = {"status": "error", "error": str(e)}
                print(json.dumps(error_result), flush=True)

    except KeyboardInterrupt:
        logger.info("Bridge interrupted by user")
    except Exception as e:
        logger.exception("Fatal error in STDIO loop")
    finally:
        logger.info("Bridge stopped")

if __name__ == "__main__":
    main()
