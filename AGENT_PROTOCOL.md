# Agent Protocol Documentation

This document describes the communication protocol between the bridge and ADK agents.

## Overview

The bridge communicates with agents using a **hybrid protocol** that combines:
1. **Command-line arguments** for specific parameters
2. **JSON on stdin** for the complete parameter payload

This dual approach ensures compatibility with different agent implementations.

---

## Protocol Details

### Input to Agents

When the bridge executes an agent, it provides data in **two ways simultaneously**:

#### 1. Command-Line Arguments

Specific parameters are passed as CLI arguments:

```bash
python agent/main.py --issue 123 --repo owner/repo --dry-run
```

**Currently supported CLI arguments:**
- `--issue <number>` - GitHub issue number (for label_github_issue)
- `--repo <owner/repo>` - GitHub repository (for label_github_issue)
- `--dry-run` - Dry run mode (for label_github_issue)

#### 2. JSON on stdin

The **complete** parameter dictionary is also sent as JSON to the agent's stdin:

```json
{
  "repo_name": "owner/repo",
  "issue_number": 123,
  "dry_run": true
}
```

### Why Both?

- **CLI arguments**: Quick access to key parameters without parsing JSON
- **JSON stdin**: Complete data structure, extensible, supports complex types
- **Flexibility**: Agents can choose to read from either source

---

## Agent Implementation Guide

### Recommended Implementation

Agents should read from **JSON stdin** as the primary source of parameters:

```python
#!/usr/bin/env python3
"""Example agent implementation."""

import json
import sys

def main():
    # Read parameters from stdin
    params = json.load(sys.stdin)

    # Extract parameters
    repo_name = params.get("repo_name")
    issue_number = params.get("issue_number")
    dry_run = params.get("dry_run", True)

    # Your agent logic here
    result = process(repo_name, issue_number, dry_run)

    # Output JSON response
    output = {
        "status": "success",
        "result": result
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

### Alternative: Using CLI Arguments

If your agent prefers CLI arguments, use argparse:

```python
#!/usr/bin/env python3
"""Example agent using CLI arguments."""

import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    # Your agent logic here
    result = process(args.repo, args.issue, args.dry_run)

    # Output JSON response
    output = {
        "status": "success",
        "result": result
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

### Hybrid Approach

For maximum compatibility, read from both sources:

```python
#!/usr/bin/env python3
"""Hybrid agent reading from both sources."""

import argparse
import json
import sys

def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo")
    parser.add_argument("--issue", type=int)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    # Read JSON from stdin
    params = json.load(sys.stdin)

    # CLI arguments take precedence over JSON
    repo_name = args.repo or params.get("repo_name")
    issue_number = args.issue or params.get("issue_number")
    dry_run = args.dry_run or params.get("dry_run", False)

    # Your agent logic here
    result = process(repo_name, issue_number, dry_run)

    # Output JSON response
    output = {
        "status": "success",
        "result": result
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

---

## Output Protocol

### Success Response

Agents MUST output valid JSON to stdout:

```json
{
  "status": "success",
  "data": {
    "labels": ["bug", "priority-high"],
    "confidence": 0.95
  }
}
```

### Error Response

In case of error:

```json
{
  "status": "error",
  "error": "Descriptive error message",
  "details": "Additional context (optional)"
}
```

### Exit Codes

- `0`: Success
- `1`: Error
- `2+`: Specific error codes (optional)

The bridge checks the exit code first, then parses JSON output.

---

## Environment Variables

The bridge sets these environment variables for all agents:

```bash
PYTHONPATH=/path/to/adk-workspace  # Workspace root
```

Agents may also have access to:
```bash
GITHUB_TOKEN=xxx       # Set by user for GitHub agents
GEMINI_API_KEY=xxx     # Set by user for Gemini agents
```

---

## Execution Context

### Python Interpreter

Each agent uses its configured Python interpreter:

```yaml
# config.yaml
agents:
  my_agent:
    python: adk-env/bin/python  # Relative to workspace
```

### Working Directory

Agents are executed with `cwd` = workspace root.

### Timeout

Default: 300 seconds (5 minutes), configurable per agent:

```yaml
agents:
  my_agent:
    timeout: 600  # 10 minutes
```

---

## Parameter Validation

The bridge validates parameters **before** execution:

### repo_name
- Format: `^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$`
- Example: `facebook/react`
- Max length: 200 characters

### issue_number
- Type: Positive integer
- Range: 1 to 999,999,999

### sources
- Type: Array of strings
- Allowed values: `["github", "pypi", "npm", "reddit", "hackernews"]`

### Generic strings
- Max length: Configurable (default 10,000 characters)
- Sanitized to remove shell metacharacters

Agents can assume parameters are pre-validated if `security.validate_inputs: true` in config.

---

## Error Handling

### Bridge-Side Errors

The bridge returns error responses for:

- **Validation errors**: Parameter validation failed
- **Agent not found**: Script or Python interpreter missing
- **Timeout**: Agent exceeded configured timeout
- **Invalid JSON**: Agent output is not valid JSON
- **Execution error**: Agent returned non-zero exit code

Example:

```json
{
  "status": "error",
  "error": "Validation error: Invalid repo_name format"
}
```

### Agent-Side Errors

Agents should catch exceptions and return error responses:

```python
try:
    result = risky_operation()
    return {"status": "success", "result": result}
except ValueError as e:
    return {"status": "error", "error": f"Invalid input: {e}"}
except Exception as e:
    return {"status": "error", "error": f"Unexpected error: {e}"}
```

---

## Logging

### Bridge Logging

The bridge logs all agent executions:

```
[2025-11-05 10:30:45] INFO: Dispatching tool: watch_collect with params: {...}
[2025-11-05 10:31:12] INFO: Agent watch_collect completed successfully in 27.3s
```

### Agent Logging

Agents should log to **stderr** (not stdout):

```python
import sys
import logging

logging.basicConfig(
    stream=sys.stderr,  # Important: use stderr
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Agent started")
```

Stdout is reserved for JSON output only.

---

## Best Practices

### For Agent Developers

1. **Always output valid JSON** - Even for errors
2. **Log to stderr** - Keep stdout clean for JSON
3. **Handle stdin gracefully** - Read JSON even if using CLI args
4. **Set appropriate timeouts** - Long-running agents should request higher timeout
5. **Validate input** - Double-check parameters even if bridge validates
6. **Return structured data** - Use consistent response format
7. **Document parameters** - List all expected parameters in agent's README

### For Bridge Users

1. **Use config.yaml** - Don't hardcode paths
2. **Set timeouts appropriately** - Match agent execution time
3. **Check logs** - Monitor `~/.gemini/bridge.log`
4. **Use health_check** - Verify system before production use
5. **Test agents individually** - Use CLI mode for testing

---

## Migration Guide

### From CLI-Only Agents

If your agent only reads CLI arguments:

**Before:**
```python
parser.add_argument("--repo", required=True)
args = parser.parse_args()
```

**After (backward compatible):**
```python
parser.add_argument("--repo")  # Make optional
args = parser.parse_args()

# Read from stdin if CLI arg not provided
if not args.repo:
    params = json.load(sys.stdin)
    repo = params.get("repo_name")
else:
    repo = args.repo
```

### From stdin-Only Agents

If your agent only reads stdin:

No changes needed! Your agent already follows the recommended pattern.

---

## Testing Your Agent

### Direct CLI Test

```bash
echo '{"repo_name":"test/repo","issue_number":123}' | \
  python agent/main.py
```

### Via Bridge

```bash
python bridge.py label_github_issue '{"repo_name":"test/repo","issue_number":123}'
```

### Via Gemini CLI

```bash
gemini
run_tool label_github_issue {"repo_name":"test/repo","issue_number":123}
```

---

## Troubleshooting

### Agent not receiving parameters

- Check that agent reads from stdin
- Verify JSON is being sent (check bridge logs)
- Test agent directly with echo + pipe

### Agent output not parsed

- Ensure agent outputs valid JSON to stdout
- Check that agent doesn't print to stdout before JSON output
- Verify no debug print() statements in agent code

### Timeout errors

- Increase timeout in config.yaml
- Check agent isn't stuck in infinite loop
- Monitor agent execution time

### Permission errors

- Verify Python interpreter is executable
- Check agent script has read permission
- Ensure workspace directory is accessible

---

## Future Enhancements

Planned protocol improvements:

- **Streaming output**: Support for progress updates
- **Bidirectional communication**: Agent → Bridge messages
- **Batch requests**: Multiple requests in one call
- **Protocol versioning**: Explicit version negotiation

---

## Reference

### Complete Example

See `examples/sample_agent.py` for a complete reference implementation.

### Protocol Version

Current version: **1.0.0**

### Compatibility

- Bridge version: 1.0.0+
- Python: 3.8+
- JSON: RFC 8259

---

## Questions?

- Check `CONTRIBUTING.md` for development guidelines
- Review `diagnose.py` output for configuration issues
- See `CHANGELOG.md` for protocol changes
- Open an issue for protocol clarifications
