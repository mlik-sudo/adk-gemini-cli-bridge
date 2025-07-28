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
        "description": "GitHub Issue Labeler Agent"
    },
    "watch_collect": {
        "path": ADK_WORKSPACE / "veille_agent" / "main.py",
        "python": ADK_WORKSPACE / "veille_agent" / ".venv" / "bin" / "python", 
        "description": "Watch/Veille Agent for collecting tech updates"
    },
    "analyse_watch_report": {
        "path": ADK_WORKSPACE / "gemini_analysis" / "main.py",
        "python": ADK_WORKSPACE / "adk-env" / "bin" / "python",
        "description": "Gemini Analysis Agent for report analysis"
    },
    "curate_digest": {
        "path": ADK_WORKSPACE / "curateur_agent" / "main.py",
        "python": ADK_WORKSPACE / "adk-env" / "bin" / "python",
        "description": "Curator Agent for content curation"
    }
}

# ---------------------------------------------------------------------------
# 1.1  Catalogue MCP des outils disponibles --------------------------------
# ---------------------------------------------------------------------------
AVAILABLE_TOOLS = {
    "watch_collect": {"description": "Surveillance GitHub/PyPI/NPM pour collecter les nouveautés tech"},
    "analyse_watch_report": {"description": "Analyse Gemini du rapport de veille markdown"},
    "curate_digest": {"description": "Génération newsletter + threads sociaux à partir de l'analyse"},
    "label_github_issue": {"description": "Étiquetage automatique d'issues GitHub"}
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

def run_agent_script(agent_name: str, params: dict) -> dict:
    """Execute an ADK agent Python script with parameters."""
    try:
        agent_config = AGENTS_CONFIG[agent_name]
        agent_path = agent_config["path"]
        python_path = agent_config["python"]
        
        # Check if the Python interpreter exists
        if not python_path.exists():
            return {"status": "error", "error": f"Python interpreter not found: {python_path}"}
        
        # Prepare the environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ADK_WORKSPACE)
        
        # Convert params to command line arguments or JSON input
        cmd = [str(python_path), str(agent_path)]
        
        # If params contain specific keys, pass them as arguments
        if "issue_number" in params:
            cmd.extend(["--issue", str(params["issue_number"])])
        if "repo_name" in params:
            cmd.extend(["--repo", params["repo_name"]])
        if "dry_run" in params and params["dry_run"]:
            cmd.append("--dry-run")
        
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
    """Handle GitHub issue labeling."""
    required_params = ["repo_name", "issue_number"]
    missing = [p for p in required_params if p not in params]
    if missing:
        return {"status": "error", "error": f"Missing required parameters: {missing}"}
    
    # The GitHub labeler automatically determines labels based on content
    # Add dry_run by default to avoid making actual changes unless explicitly requested
    if "dry_run" not in params:
        params["dry_run"] = True
    
    return run_agent_script("label_github_issue", params)

def dispatch_watch_collect(params: dict) -> dict:
    """Handle watch/veille collection."""
    # Default parameters for watch collection
    default_params = {
        "sources": ["github", "pypi", "npm"],
        "output_format": "markdown"
    }
    merged_params = {**default_params, **params}
    return run_agent_script("watch_collect", merged_params)

def dispatch_analyse_watch_report(params: dict) -> dict:
    """Handle watch report analysis."""
    if "report" not in params and "report_path" not in params:
        return {"status": "error", "error": "Missing 'report' or 'report_path' parameter"}
    
    return run_agent_script("analyse_watch_report", params)

def dispatch_curate_digest(params: dict) -> dict:
    """Handle content curation."""
    default_params = {
        "format": "newsletter",
        "output": "markdown"
    }
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
# 5.1  Dispatch JSON-RPC pour protocole MCP --------------------------------
# ---------------------------------------------------------------------------

def dispatch_rpc(request: dict):
    """Répond aux appels JSON-RPC du protocole MCP."""
    method = request.get("method")
    
    logger.info(f"Received JSON-RPC method: {method}")
    
    # 1️⃣ Hand-shake
    if method == "initialize":
        logger.info("MCP initialize handshake")
        return {
            "jsonrpc": "2.0", 
            "id": request.get("id"), 
            "result": {
                "protocolVersion": "2025-02-01",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "adk-gemini-bridge",
                    "version": "1.0.0",
                    "description": "ADK Agents Bridge - 4 tools for tech watch, analysis, curation, and GitHub labeling"
                }
            }
        }

    # 2️⃣ Catalogue des outils
    if method == "tools/list":
        logger.info("MCP tools/list request")
        # Schemas complets pour chaque tool
        tool_schemas = {
            "watch_collect": {
                "type": "object",
                "properties": {
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Sources à surveiller (github, pypi, npm)",
                        "default": ["github", "pypi", "npm"]
                    },
                    "output_format": {
                        "type": "string", 
                        "description": "Format de sortie",
                        "default": "markdown"
                    }
                },
                "required": []
            },
            "analyse_watch_report": {
                "type": "object",
                "properties": {
                    "report": {
                        "type": "string",
                        "description": "Contenu du rapport markdown à analyser"
                    },
                    "report_path": {
                        "type": "string",
                        "description": "Chemin vers le fichier rapport"
                    }
                },
                "anyOf": [{"required": ["report"]}, {"required": ["report_path"]}]
            },
            "curate_digest": {
                "type": "object", 
                "properties": {
                    "analysis_json": {
                        "type": "object",
                        "description": "Résultat de l'analyse au format JSON"
                    },
                    "format": {
                        "type": "string",
                        "description": "Format de sortie (newsletter, social)",
                        "default": "newsletter"
                    },
                    "output": {
                        "type": "string",
                        "description": "Type de sortie (markdown, html)",
                        "default": "markdown"
                    }
                },
                "required": ["analysis_json"]
            },
            "label_github_issue": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Nom du repository (owner/repo)"
                    },
                    "issue_number": {
                        "type": "integer",
                        "description": "Numéro de l'issue à étiqueter"
                    },
                    "dry_run": {
                        "type": "boolean", 
                        "description": "Mode simulation (pas de modifications réelles)",
                        "default": True
                    }
                },
                "required": ["repo_name", "issue_number"]
            }
        }
        
        tools = [
            {
                "name": name,
                "description": meta["description"],
                "inputSchema": tool_schemas.get(name, {"type": "object", "properties": {}, "required": []}),
            }
            for name, meta in AVAILABLE_TOOLS.items()
        ]
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {"tools": tools}}

    # 3️⃣ Appels réels envoyés par run_tool
    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        logger.info(f"MCP tools/call for {tool_name}")
        result = dispatch(tool_name, tool_args)
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "content": [{"type": "text", "text": json.dumps(result)}]
            }
        }

    # Fallback : inconnu
    logger.warning(f"Unknown JSON-RPC method: {method}")
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "error": {"code": -32601, "message": f"Unknown method {method}"}
    }

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
                
                # Check if it's JSON-RPC (MCP) or legacy format
                if "method" in payload:
                    # JSON-RPC format (MCP protocol)
                    result = dispatch_rpc(payload)
                else:
                    # Legacy format for backward compatibility
                    tool = payload.get("tool")
                    params = payload.get("params", {})
                    
                    if not tool:
                        result = {"status": "error", "error": "Missing 'tool' in payload"}
                    else:
                        result = dispatch(tool, params)
                
                try:
                    print(json.dumps(result), flush=True)
                except BrokenPipeError:
                    logger.info("Client disconnected during response (broken pipe)")
                    sys.exit(0)  # Sortie propre
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error on line {line_num}: {e}")
                error_result = {"status": "error", "error": f"Invalid JSON on line {line_num}: {e}"}
                try:
                    print(json.dumps(error_result), flush=True)
                except BrokenPipeError:
                    logger.info("Client disconnected during error response")
                    sys.exit(0)
            except BrokenPipeError:
                logger.info("Client disconnected (broken pipe)")
                sys.exit(0)
            except Exception as e:
                logger.exception(f"Unexpected error on line {line_num}")
                error_result = {"status": "error", "error": str(e)}
                try:
                    print(json.dumps(error_result), flush=True)
                except BrokenPipeError:
                    logger.info("Client disconnected during exception response")
                    sys.exit(0)
                
    except KeyboardInterrupt:
        logger.info("Bridge interrupted by user")
    except Exception as e:
        logger.exception("Fatal error in STDIO loop")
    finally:
        logger.info("Bridge stopped")

if __name__ == "__main__":
    main()