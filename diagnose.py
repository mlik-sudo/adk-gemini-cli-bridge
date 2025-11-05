#!/usr/bin/env python3
"""Diagnostic script for ADK-Gemini CLI Bridge.

This script verifies the installation and configuration of the bridge,
checking all dependencies, paths, and configurations.

Usage:
    python3 diagnose.py
    python3 diagnose.py --verbose
    python3 diagnose.py --fix  # Attempt to fix common issues
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any

# ANSI colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗{Colors.END} {message}")

def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

class BridgeDiagnostic:
    """Diagnostic tool for the bridge."""

    def __init__(self, verbose: bool = False, fix: bool = False):
        self.verbose = verbose
        self.fix = fix
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_total = 0

    def check(self, name: str, condition: bool, error_msg: str = "", warning: bool = False) -> bool:
        """Run a check and record the result."""
        self.checks_total += 1

        if condition:
            self.checks_passed += 1
            if self.verbose:
                print_success(name)
            return True
        else:
            if warning:
                self.warnings.append(f"{name}: {error_msg}")
                print_warning(f"{name}: {error_msg}")
            else:
                self.errors.append(f"{name}: {error_msg}")
                print_error(f"{name}: {error_msg}")
            return False

    def check_python_version(self) -> bool:
        """Check Python version."""
        print_section("Python Environment")

        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        print_info(f"Python version: {version_str}")

        return self.check(
            "Python version >= 3.8",
            version >= (3, 8),
            f"Python 3.8+ required, got {version_str}"
        )

    def check_dependencies(self) -> bool:
        """Check required Python packages."""
        print_section("Dependencies")

        all_ok = True

        # Check PyYAML (optional)
        try:
            import yaml
            print_success("PyYAML installed")
        except ImportError:
            self.check(
                "PyYAML installed",
                False,
                "PyYAML not found (optional but recommended)",
                warning=True
            )
            all_ok = False

        # Check standard library imports
        required_modules = ['json', 'subprocess', 're', 'pathlib', 'logging']
        for module in required_modules:
            try:
                __import__(module)
                if self.verbose:
                    print_success(f"Module '{module}' available")
            except ImportError:
                self.check(
                    f"Module '{module}' available",
                    False,
                    f"Standard library module '{module}' not found"
                )
                all_ok = False

        return all_ok

    def check_bridge_files(self) -> bool:
        """Check bridge installation files."""
        print_section("Bridge Installation")

        all_ok = True

        # Check bridge.py
        bridge_path = Path(__file__).parent / "bridge.py"
        all_ok &= self.check(
            "bridge.py exists",
            bridge_path.exists(),
            f"bridge.py not found at {bridge_path}"
        )

        if bridge_path.exists() and self.verbose:
            size = bridge_path.stat().st_size
            print_info(f"  Size: {size} bytes (~{size/1024:.1f} KB)")

        # Check config.yaml
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            print_success(f"config.yaml found at {config_path}")

            # Validate YAML syntax
            try:
                import yaml
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    print_success("config.yaml syntax valid")

                    if self.verbose and config:
                        print_info(f"  Workspace: {config.get('workspace', {}).get('path', 'N/A')}")
                        print_info(f"  Log level: {config.get('logging', {}).get('level', 'N/A')}")
            except ImportError:
                print_warning("Cannot validate config.yaml (PyYAML not installed)")
            except Exception as e:
                all_ok &= self.check(
                    "config.yaml syntax",
                    False,
                    f"Invalid YAML: {e}"
                )
        else:
            print_warning(f"config.yaml not found (will use defaults)")

        # Check mcp_servers.json.template
        mcp_template = Path(__file__).parent / "mcp_servers.json.template"
        all_ok &= self.check(
            "mcp_servers.json.template exists",
            mcp_template.exists(),
            f"Template not found at {mcp_template}"
        )

        if mcp_template.exists():
            try:
                with open(mcp_template) as f:
                    mcp_config = json.load(f)
                    agent_count = len(mcp_config)
                    print_success(f"MCP template valid ({agent_count} agents configured)")

                    if self.verbose:
                        for agent in mcp_config.keys():
                            print_info(f"  - {agent}")
            except json.JSONDecodeError as e:
                all_ok &= self.check(
                    "mcp_servers.json.template syntax",
                    False,
                    f"Invalid JSON: {e}"
                )

        return all_ok

    def check_workspace(self) -> bool:
        """Check ADK workspace structure."""
        print_section("ADK Workspace")

        # Try to determine workspace path
        workspace_path = Path.home() / "adk-workspace"

        # Check if custom path in config
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            try:
                import yaml
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    if config and 'workspace' in config:
                        custom_path = config['workspace'].get('path')
                        if custom_path:
                            workspace_path = Path(os.path.expanduser(custom_path))
            except:
                pass

        print_info(f"Workspace path: {workspace_path}")

        all_ok = self.check(
            "Workspace directory exists",
            workspace_path.exists(),
            f"Workspace not found at {workspace_path}"
        )

        if not workspace_path.exists():
            if self.fix:
                print_info(f"Creating workspace directory: {workspace_path}")
                workspace_path.mkdir(parents=True, exist_ok=True)
                print_success("Workspace directory created")
                all_ok = True
            else:
                print_info("Run with --fix to create the workspace directory")
            return all_ok

        # Check expected agents
        expected_agents = {
            "github_labeler": "github_labeler/main.py",
            "veille_agent": "veille_agent/main.py",
            "gemini_analysis": "gemini_analysis/main.py",
            "curateur_agent": "curateur_agent/main.py"
        }

        for agent_name, agent_path in expected_agents.items():
            full_path = workspace_path / agent_path
            exists = full_path.exists()

            if exists:
                print_success(f"Agent '{agent_name}' found")
                if self.verbose:
                    print_info(f"  Path: {full_path}")
            else:
                self.check(
                    f"Agent '{agent_name}' exists",
                    False,
                    f"Script not found at {full_path}",
                    warning=True
                )

        # Check Python environments
        print("\nPython Environments:")

        venvs = [
            ("Global adk-env", workspace_path / "adk-env" / "bin" / "python"),
            ("veille_agent .venv", workspace_path / "veille_agent" / ".venv" / "bin" / "python")
        ]

        for name, venv_path in venvs:
            if venv_path.exists():
                print_success(f"{name} found")
                if self.verbose:
                    print_info(f"  Path: {venv_path}")
            else:
                self.check(
                    f"{name} exists",
                    False,
                    f"Python interpreter not found at {venv_path}",
                    warning=True
                )

        return all_ok

    def check_gemini_integration(self) -> bool:
        """Check Gemini CLI integration."""
        print_section("Gemini CLI Integration")

        gemini_dir = Path.home() / ".gemini"
        all_ok = True

        # Check .gemini directory
        if gemini_dir.exists():
            print_success(f".gemini directory exists at {gemini_dir}")
        else:
            if self.fix:
                print_info(f"Creating .gemini directory: {gemini_dir}")
                gemini_dir.mkdir(parents=True, exist_ok=True)
                print_success(".gemini directory created")
            else:
                self.check(
                    ".gemini directory exists",
                    False,
                    f"Directory not found at {gemini_dir}",
                    warning=True
                )
                print_info("Run with --fix to create the directory")

        # Check bridge.py in .gemini
        bridge_in_gemini = gemini_dir / "bridge.py"
        if bridge_in_gemini.exists():
            print_success(f"bridge.py installed in {gemini_dir}")

            # Check if it's executable
            if os.access(bridge_in_gemini, os.X_OK):
                print_success("bridge.py is executable")
            else:
                print_warning("bridge.py is not executable (may need chmod +x)")
        else:
            print_warning(f"bridge.py not found in {gemini_dir}")
            print_info(f"Copy with: cp bridge.py {gemini_dir}/")

        # Check mcp_servers.json
        mcp_config = gemini_dir / "mcp_servers.json"
        if mcp_config.exists():
            print_success(f"mcp_servers.json exists")

            try:
                with open(mcp_config) as f:
                    config = json.load(f)

                    # Check if our agents are configured
                    our_agents = ["label_github_issue", "watch_collect",
                                "analyse_watch_report", "curate_digest", "health_check"]

                    configured = [a for a in our_agents if a in config]

                    if configured:
                        print_success(f"{len(configured)}/{len(our_agents)} bridge agents configured")
                        if self.verbose:
                            for agent in configured:
                                print_info(f"  - {agent}")
                    else:
                        print_warning("No bridge agents found in mcp_servers.json")
                        print_info("Merge with: cat mcp_servers.json.template into ~/.gemini/mcp_servers.json")

            except json.JSONDecodeError as e:
                self.check(
                    "mcp_servers.json syntax",
                    False,
                    f"Invalid JSON: {e}"
                )
        else:
            print_warning("mcp_servers.json not found")
            print_info("Create from template: cp mcp_servers.json.template ~/.gemini/mcp_servers.json")

        return all_ok

    def check_environment_variables(self) -> bool:
        """Check environment variables."""
        print_section("Environment Variables")

        # Check optional env vars
        env_vars = {
            "ADK_WORKSPACE": "Workspace path override",
            "BRIDGE_LOG_LEVEL": "Log level override",
            "BRIDGE_LOG_FILE": "Log file path override",
            "GITHUB_TOKEN": "GitHub API token (for label_github_issue agent)",
            "GEMINI_API_KEY": "Gemini API key (for analyse_watch_report agent)"
        }

        found = 0
        for var, description in env_vars.items():
            if var in os.environ:
                value = os.environ[var]
                # Mask sensitive values
                if "TOKEN" in var or "KEY" in var:
                    masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "***"
                    print_success(f"{var} set ({masked})")
                else:
                    print_success(f"{var} = {value}")
                found += 1
            else:
                if self.verbose:
                    print_info(f"{var} not set ({description})")

        if found == 0:
            print_info("No environment variables set (using defaults)")
        else:
            print_info(f"{found}/{len(env_vars)} environment variables configured")

        return True

    def smoke_test(self) -> bool:
        """Run smoke tests on the bridge."""
        print_section("Smoke Tests")

        bridge_path = Path(__file__).parent / "bridge.py"

        if not bridge_path.exists():
            print_error("Cannot run smoke tests: bridge.py not found")
            return False

        all_ok = True

        # Test 1: Syntax check
        import subprocess

        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(bridge_path)],
                capture_output=True,
                text=True,
                timeout=5
            )

            self.check(
                "bridge.py syntax check",
                result.returncode == 0,
                f"Syntax error: {result.stderr}"
            )
        except Exception as e:
            self.check("bridge.py syntax check", False, str(e))
            all_ok = False

        # Test 2: Import test
        try:
            sys.path.insert(0, str(bridge_path.parent))
            import bridge
            print_success("bridge module imports successfully")

            # Check for expected classes and functions
            expected_symbols = ['Config', 'Validator', 'MetricsCollector', 'dispatch', 'main']
            for symbol in expected_symbols:
                if hasattr(bridge, symbol):
                    if self.verbose:
                        print_success(f"  {symbol} found")
                else:
                    self.check(f"{symbol} exists", False, f"{symbol} not found in bridge module")
                    all_ok = False

        except Exception as e:
            self.check("bridge module import", False, str(e))
            all_ok = False

        # Test 3: Health check
        try:
            result = subprocess.run(
                [sys.executable, str(bridge_path), "health_check", "{}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    if output.get("status") == "success":
                        print_success("Health check endpoint works")
                        if self.verbose and "health" in output:
                            health = output["health"]
                            print_info(f"  Status: {health.get('status', 'unknown')}")
                            print_info(f"  Total calls: {health.get('total_calls', 0)}")
                    else:
                        self.check("Health check status", False, "Status is not 'success'")
                        all_ok = False
                except json.JSONDecodeError:
                    self.check("Health check output", False, "Invalid JSON output")
                    all_ok = False
            else:
                self.check("Health check execution", False, f"Exit code: {result.returncode}")
                all_ok = False

        except subprocess.TimeoutExpired:
            self.check("Health check execution", False, "Timeout after 10s")
            all_ok = False
        except Exception as e:
            self.check("Health check execution", False, str(e))
            all_ok = False

        return all_ok

    def run_all_diagnostics(self) -> bool:
        """Run all diagnostic checks."""
        print(f"{Colors.BOLD}ADK-Gemini CLI Bridge - Diagnostic Tool{Colors.END}\n")

        all_ok = True
        all_ok &= self.check_python_version()
        all_ok &= self.check_dependencies()
        all_ok &= self.check_bridge_files()
        all_ok &= self.check_workspace()
        all_ok &= self.check_gemini_integration()
        all_ok &= self.check_environment_variables()
        all_ok &= self.smoke_test()

        return all_ok

    def print_summary(self):
        """Print diagnostic summary."""
        print_section("Summary")

        print(f"Checks passed: {Colors.GREEN}{self.checks_passed}{Colors.END}/{self.checks_total}")

        if self.errors:
            print(f"\n{Colors.RED}Errors ({len(self.errors)}):{Colors.END}")
            for error in self.errors:
                print(f"  {Colors.RED}✗{Colors.END} {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings ({len(self.warnings)}):{Colors.END}")
            for warning in self.warnings:
                print(f"  {Colors.YELLOW}⚠{Colors.END} {warning}")

        if not self.errors and not self.warnings:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All checks passed! Bridge is ready.{Colors.END}")
            return 0
        elif self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ Issues found. Please fix errors before using the bridge.{Colors.END}")
            return 1
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Minor issues found. Bridge should work but may have limited functionality.{Colors.END}")
            return 0

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Diagnostic tool for ADK-Gemini CLI Bridge"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix common issues (create directories, etc.)"
    )

    args = parser.parse_args()

    diagnostic = BridgeDiagnostic(verbose=args.verbose, fix=args.fix)
    diagnostic.run_all_diagnostics()
    return diagnostic.print_summary()

if __name__ == "__main__":
    sys.exit(main())
