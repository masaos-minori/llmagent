# Implementation Procedure: Check chunks_fts Invariant Lint Script

## Goal

Create a custom lint script at `tools/check_chunks_fts_invariant.py` that detects direct `INSERT INTO chunks_fts` / `UPDATE chunks_fts` SQL string references in Python source files outside sanctioned write paths, per REQ-01 through REQ-04.

## Scope

- Create `tools/check_chunks_fts_invariant.py` as a new file
- The script scans `.py` files under `scripts/` for direct `INSERT INTO chunks_fts` and `UPDATE chunks_fts` SQL string references
- Excludes sanctioned write paths and out-of-scope directories
- Reports violations with file path, line number, and offending SQL statement
- Exit code 0 if no violations, 1 if violations found

## Assumptions

- `rg` (ripgrep) is available for scanning — confirmed by its use throughout the codebase
- The project uses `ruff` for linting (confirmed: `pyproject.toml` line 65); the custom lint script runs as a standalone tox step
- Sanctioned write paths are exactly: `scripts/agent/services/rag_maintenance_service.py::rebuild_fts()` and `scripts/db/schema_sql.py`
- Out-of-scope directory: `scripts/mcp_servers/mdq/` (targets a separate database `/opt/llm/db/mdq.sqlite`)

## Design decisions

- Use `rg` for pattern scanning rather than AST parsing — faster and simpler for text-based detection
- Whitelist via file-path exclusion + function-context detection (AST-based) for `rag_maintenance_service.py`
- Note: `schema_sql.py` and `mdq/db_schema.py` contain `INSERT INTO chunks_fts` only inside CREATE TRIGGER blocks (trigger definitions), not runtime writes. These are excluded because they are not direct writes — they define SQLite triggers that fire automatically when the `chunks` table is modified.

## Alternatives considered

- **AST-only approach**: Parse all Python files with AST to find SQL string literals. More accurate but slower and more complex; `rg` already handles the text-level detection efficiently.
- **Pre-commit hook**: Would provide faster feedback but adds local dependency burden. CI-only is lower barrier to adoption.
- **Ruff plugin**: Could integrate natively but requires additional dependency (`ast-grep-py` mentioned in REQ-05). Standalone script avoids this.

## Implementation

### Target file

`tools/check_chunks_fts_invariant.py`

### Procedure

1. Create the file with shebang and module docstring following project conventions
2. Implement `main()` entry point with argparse for `--path <dir>` CLI argument
3. Implement scanning logic using `rg` subprocess call
4. Implement whitelist filtering:
   a. Skip `scripts/mcp_servers/mdq/` directory entirely
   b. For `scripts/agent/services/rag_maintenance_service.py`, use AST to detect whether each match is inside `rebuild_fts()` function
   c. For `scripts/db/schema_sql.py`, skip entirely (trigger definitions, not runtime writes)
5. Report violations in format `{file}:{line}: {sql_statement}`
6. Return exit code 1 if violations found, 0 otherwise

### Method

**Step 1: Entry point and CLI**

```python
#!/usr/bin/env python3
"""Check that application code never directly operates on chunks_fts outside sanctioned paths."""

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

SANCTIONED_FILE = "scripts/agent/services/rag_maintenance_service.py"
SANCTIONED_FUNCTION = "rebuild_fts"
EXCLUDED_DIR = "scripts/mcp_servers/mdq/"
DEFAULT_SCAN_PATH = "scripts/"
PATTERNS = ["INSERT INTO chunks_fts", "UPDATE chunks_fts"]
```

**Step 2: rg scanning**

```python
def scan_for_violations(scan_path: str) -> list[dict]:
    """Run rg to find chunks_fts INSERT/UPDATE patterns."""
    cmd = ["rg", "-n"]
    for pattern in PATTERNS:
        cmd.extend(["-e", pattern])
    cmd.append(scan_path)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []  # No matches or error
    
    violations = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split(":", 2)
        if len(parts) == 3:
            filepath, lineno, sql = parts
            violations.append({
                "file": filepath,
                "line": int(lineno),
                "statement": sql.strip(),
            })
    return violations
```

**Step 3: Whitelist filtering**

```python
def is_sanctioned(filepath: str, lineno: int) -> bool:
    """Return True if this occurrence is in a sanctioned write path."""
    # Always exclude schema_sql.py (trigger definitions, not runtime writes)
    if "scripts/db/schema_sql.py" in filepath:
        return True
    
    # Always exclude MDQ directory (separate database)
    if EXCLUDED_DIR in filepath:
        return True
    
    # For rag_maintenance_service.py, check function context via AST
    if SANCTIONED_FILE in filepath:
        return _is_inside_function(filepath, lineno, SANCTIONED_FUNCTION)
    
    return False

def _is_inside_function(filepath: str, lineno: int, func_name: str) -> bool:
    """Use AST to determine if lineno falls within func_name."""
    try:
        with open(filepath, "r") as f:
            tree = ast.parse(f.read())
    except (OSError, SyntaxError):
        return False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                if node.lineno <= lineno <= node.end_lineno:
                    return True
    return False
```

**Step 4: Main entry point**

```python
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect direct chunks_fts operations outside sanctioned paths."
    )
    parser.add_argument("--path", default=DEFAULT_SCAN_PATH, help="Directory to scan")
    args = parser.parse_args()
    
    violations = scan_for_violations(args.path)
    flagged = [v for v in violations if not is_sanctioned(v["file"], v["line"])]
    
    for v in flagged:
        print(f"{v['file']}:{v['line']}: {v['statement']}")
    
    if flagged:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Details

- **REQ-01**: Scans all `.py` files under `scripts/` for `INSERT INTO chunks_fts` and `UPDATE chunks_fts` patterns via `rg`
- **REQ-02**: Excludes `rag_maintenance_service.py::rebuild_fts()` via AST function-context detection, and `schema_sql.py` entirely (trigger definitions)
- **REQ-03**: Excludes `scripts/mcp_servers/adq/` directory entirely (separate database)
- **REQ-04**: Reports violations as `{file}:{line}: {sql_statement}`

## Compatibility considerations

- Requires `rg` (ripgrep) installed on the host system — already used elsewhere in the codebase
- Uses `ast` standard library — no additional dependencies needed
- Compatible with both Python 3.8+ (uses `ast.FunctionDef.end_lineno` which was added in Python 3.8)

## Security considerations

- The script itself does not execute any SQL — it only scans for SQL strings in source code
- Running the script does not modify any files or databases
- Exit code 1 indicates a security concern (unsanctioned direct write detected)

## Rollback considerations

- If the script produces false positives after deployment, the whitelist can be updated by adding the file/function to `is_sanctioned()`
- If the script needs to be removed from CI, simply remove the tox environment configuration (separate change)

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| Synthetic violation test | Unit: detect unsanctioned write | `uv run python tools/check_chunks_fts_invariant.py --path <temp_dir>` | Exit code 1, violation reported |
| Zero findings on sanctioned paths | Unit: no false positives | `uv run python tools/check_chunks_fts_invariant.py` | Exit code 0, no output |
| Zero findings on MDQ files | Unit: no false positives on separate DB | `uv run python tools/check_chunks_fts_invariant.py` | Exit code 0, no output |

## Completion criteria

- [ ] `tools/check_chunks_fts_invariant.py` exists and is executable
- [ ] Script returns exit code 1 when an unsanctioned `INSERT INTO chunks_fts` or `UPDATE chunks_fts` is found in a synthetic test file
- [ ] Script returns exit code 0 with zero findings on `scripts/agent/services/rag_maintenance_service.py::rebuild_fts()`
- [ ] Script returns exit code 0 with zero findings on `scripts/db/schema_sql.py`
- [ ] Script returns exit code 0 with zero findings on `scripts/mcp_servers/mdq/`
- [ ] Script reports violations in `{file}:{line}: {sql_statement}` format

## Out of scope

- Adding enforcement for `chunks_fts_docsize` table operations (not mentioned in ADR-009)
- Enforcing read-only `SELECT` statements against `chunks_fts`
- Pre-commit hook integration (CI-only initially per REQ-05)
- Modifying the FTS wrapper itself
- Changing the `chunks_fts` schema

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-01, REQ-02, REQ-03, REQ-04
- **Source issue**: issues/20260924-054344_design2_no-test-guarantee-chunks_fts-direct-operation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-063321_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121326
- **Related target files**: tools/check_chunks_fts_invariant.py
