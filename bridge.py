#!/usr/bin/env python3
"""STDIO bridge : expose les 4 agents ADK comme tools Gemini/Claude
Usage (CLI) :
  echo '{"tool":"watch_collect","params":{}}' | python -u bridge.py
Le script lit **une ligne JSON** sur stdin, exécute l'agent concerné et
écrit la réponse JSON sur stdout (flush immédiat).
"""
import json
import sys
import signal
import logging
import os
import re
import subprocess
from pathlib import Path
from functools import lru_cache

# ---------------------------------------------------------------------------
# 1.  Configuration des chemins vers les agents ADK ----------------------
# ---------------------------------------------------------------------------
ADK_WORKSPACE = Path.home() / "adk-workspace"
AGENTS_CONFIG = {
    "label_github_issue": {
        "path": ADK_WORKSPACE / "github_labeler" / "main.py",
        "python": ADK_WORKSPACE / "adk-env" / "bin" / "python",
        "description": "GitHub Issue Labeler Agent",
        "env_vars": ["GITHUB_TOKEN"],
    },
    "watch_collect": {
        "path": ADK_WORKSPACE / "veille_agent" / "main.py",
        "python": ADK_WORKSPACE / "veille_agent" / ".venv" / "bin" / "python",
        "description": "Watch/Veille Agent for collecting tech updates",
        "env_vars": [],
    },
    "analyse_watch_report": {
        "path": ADK_WORKSPACE / "gemini_analysis" / "main.py",
        "python": ADK_WORKSPACE / "adk-env" / "bin" / "python",
        "description": "Gemini Analysis Agent for report analysis",
        "env_vars": ["GEMINI_API_KEY"],
    },
    "curate_digest": {
        "path": ADK_WORKSPACE / "curateur_agent" / "main.py",
        "python": ADK_WORKSPACE / "adk-env" / "bin" / "python",
        "description": "Curator Agent for content curation",
        "env_vars": [],
    },
}

# ---------------------------------------------------------------------------
# 2.  Setup logging --------------------------------------------------------
# ---------------------------------------------------------------------------
logging.basicConfig(
    filename=os.path.expanduser("~/.gemini/bridge.log"),
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 3.  Agent execution functions --------------------------------------------
# ---------------------------------------------------------------------------


def _get_agent_env(agent_name: str) -> dict:
    """Creates a secure, minimal environment for an agent."""
    agent_config = AGENTS_CONFIG.get(agent_name, {})
    required_vars = agent_config.get("env_vars", [])

    # Start with a minimal environment
    env = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),  # for Windows compatibility
        "PYTHONPATH": str(ADK_WORKSPACE),
    }

    # Add required variables
    for var in required_vars:
        value = os.environ.get(var)
        if value is None:
            logger.error(
                f"Missing required environment variable '{var}' for agent '{agent_name}'"
            )
            raise ValueError(f"Missing required environment variable: {var}")
        env[var] = value

    return env


def run_agent_script(agent_name: str, params: dict) -> dict:
    """Execute an ADK agent Python script with parameters."""
    try:
        agent_config = AGENTS_CONFIG[agent_name]
        agent_path = agent_config["path"]
        python_path = agent_config["python"]

        # --- Path validation ---
        try:
            resolved_workspace = ADK_WORKSPACE.resolve()
            resolved_agent_path = agent_path.resolve()
            resolved_python_path = python_path.resolve()

            if not resolved_agent_path.is_relative_to(resolved_workspace):
                raise PermissionError("Agent path is outside of the ADK workspace.")
            if not resolved_python_path.is_relative_to(resolved_workspace):
                raise PermissionError("Python interpreter is outside of the ADK workspace.")
        except (PermissionError, FileNotFoundError) as e:
            logger.error(f"Path validation failed for agent '{agent_name}': {e}")
            return {"status": "error", "error": f"Security validation failed: {e}"}
        # -------------------------

        # Check if the Python interpreter exists
        if not python_path.exists():
            return {
                "status": "error",
                "error": f"Python interpreter not found: {python_path}",
            }

        # Prepare the environment
        env = _get_agent_env(agent_name)

        # Convert params to command line arguments or JSON input
        cmd = [str(python_path), str(agent_path)]
        
        # Execute the agent
        result = subprocess.run(
            cmd,
            input=json.dumps(params),
            text=True,
            capture_output=True,
            env=env,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout) if result.stdout.strip() else {"status": "success", "output": result.stdout}
            except json.JSONDecodeError:
                return {"status": "success", "output": result.stdout}
        else:
            return {
                "status": "error", 
                "error": result.stderr or f"Process failed with code {result.returncode}",
                "stdout": result.stdout
            }
            
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Agent execution timed out"}
    except FileNotFoundError:
        return {"status": "error", "error": f"Agent script not found: {agent_path}"}
    except Exception as e:
        logger.exception(f"Error running agent {agent_path}")
        return {"status": "error", "error": str(e)}

# ---------------------------------------------------------------------------
# 4.  Dispatch functions ---------------------------------------------------
# ---------------------------------------------------------------------------


def dispatch_label_github_issue(params: dict) -> dict:
    """Handle GitHub issue labeling with input validation."""
    # --- Validation ---
    if "repo_name" not in params or "issue_number" not in params:
        return {
            "status": "error",
            "error": "Missing required parameters: 'repo_name' and 'issue_number'",
        }
    if not isinstance(params["repo_name"], str) or not re.match(
        r"^[a-zA-Z0-9-]+\/[a-zA-Z0-9-.]+$", params["repo_name"]
    ):
        return {"status": "error", "error": "Invalid 'repo_name' format"}
    if not isinstance(params["issue_number"], int):
        return {"status": "error", "error": "'issue_number' must be an integer"}
    if "dry_run" in params and not isinstance(params["dry_run"], bool):
        return {"status": "error", "error": "'dry_run' must be a boolean"}
    # --- End Validation ---

    if "dry_run" not in params:
        params["dry_run"] = True

    return run_agent_script("label_github_issue", params)


def dispatch_watch_collect(params: dict) -> dict:
    """Handle watch/veille collection with input validation."""
    # --- Validation ---
    valid_sources = {"github", "pypi", "npm"}
    if "sources" in params:
        if not isinstance(params["sources"], list) or not all(
            isinstance(s, str) and s in valid_sources for s in params["sources"]
        ):
            return {"status": "error", "error": f"Invalid 'sources'. Must be a list of {list(valid_sources)}"}
    if "output_format" in params and params["output_format"] != "markdown":
        return {"status": "error", "error": "Invalid 'output_format'. Only 'markdown' is supported."}
    # --- End Validation ---

    default_params = {"sources": list(valid_sources), "output_format": "markdown"}
    merged_params = {**default_params, **params}
    return run_agent_script("watch_collect", merged_params)


def dispatch_analyse_watch_report(params: dict) -> dict:
    """Handle watch report analysis with input validation."""
    # --- Validation ---
    if "report" not in params and "report_path" not in params:
        return {"status": "error", "error": "Missing 'report' or 'report_path' parameter"}
    if "report_path" in params:
        try:
            # Security: ensure report_path is within the workspace
            report_path = Path(params["report_path"]).resolve()
            if not report_path.is_relative_to(ADK_WORKSPACE.resolve()):
                raise PermissionError("Access to report path is denied.")
        except (PermissionError, Exception) as e:
            return {"status": "error", "error": f"Invalid 'report_path': {e}"}
    # --- End Validation ---

    return run_agent_script("analyse_watch_report", params)


def dispatch_curate_digest(params: dict) -> dict:
    """Handle content curation with input validation."""
    # --- Validation ---
    if "format" in params and params["format"] != "newsletter":
        return {"status": "error", "error": "Invalid 'format'. Only 'newsletter' is supported."}
    if "output" in params and params["output"] != "markdown":
         return {"status": "error", "error": "Invalid 'output'. Only 'markdown' is supported."}
    # --- End Validation ---

    default_params = {"format": "newsletter", "output": "markdown"}
    merged_params = {**default_params, **params}
    return run_agent_script("curate_digest", merged_params)

# ---------------------------------------------------------------------------
# 5.  Main dispatch function -----------------------------------------------
# ---------------------------------------------------------------------------

def dispatch(tool: str, params: dict = None) -> dict:
    """Main dispatch function for all agents."""
    if params is None:
        params = {}
    
    logger.info(f"Dispatching tool: {tool} with params: {params}")
    
    dispatchers = {
        "label_github_issue": dispatch_label_github_issue,
        "watch_collect": dispatch_watch_collect,
        "analyse_watch_report": dispatch_analyse_watch_report,
        "curate_digest": dispatch_curate_digest,
    }
    
    if tool not in dispatchers:
        available_tools = list(dispatchers.keys())
        return {
            "status": "error",
            "error": f"Unknown tool '{tool}'. Available tools: {available_tools}"
        }
    
    try:
        result = dispatchers[tool](params)
        logger.info(f"Tool {tool} completed with status: {result.get('status', 'unknown')}")
        return result
    except Exception as e:
        logger.exception(f"Error in dispatch for tool {tool}")
        return {"status": "error", "error": str(e)}

# ---------------------------------------------------------------------------
# 6.  Signal handlers ------------------------------------------------------
# ---------------------------------------------------------------------------

def _signal_handler(_sig, _frm):
    logger.info("Bridge process terminated by signal")
    sys.exit(0)

signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)

# ---------------------------------------------------------------------------
# 7.  Main execution -------------------------------------------------------
# ---------------------------------------------------------------------------

def main():
    logger.info("Bridge started")
    
    # Support direct command line calls: python bridge.py <tool> <json_params>
    if len(sys.argv) >= 2 and sys.argv[1] != "-":
        tool_name = sys.argv[1]
        params_json = sys.argv[2] if len(sys.argv) > 2 else "{}"
        
        try:
            params = json.loads(params_json)
            result = dispatch(tool_name, params)
            print(json.dumps(result), flush=True)
        except json.JSONDecodeError as e:
            error_result = {"status": "error", "error": f"Invalid JSON parameters: {e}"}
            print(json.dumps(error_result), flush=True)
        except Exception as e:
            error_result = {"status": "error", "error": str(e)}
            print(json.dumps(error_result), flush=True)
        
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