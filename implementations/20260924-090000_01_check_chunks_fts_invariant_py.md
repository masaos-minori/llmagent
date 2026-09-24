## Goal

Create a custom lint script that detects direct `INSERT INTO chunks_fts` or `UPDATE chunks_fts` SQL string references outside the two sanctioned write paths (`scripts/agent/services/rag_maintenance_service.py::rebuild_fts()` and `scripts/db/schema_sql.py`) and MDQ's out-of-scope access (`scripts/mcp_servers/mdq/`), per REQ-01, REQ-02, REQ-03, REQ-04, REQ-05.

## Scope

- **In-Scope**: Implement the lint script with ripgrep-based scanning, whitelist filtering for sanctioned paths using AST-based function context detection, MDQ exclusion filter, CLI argument support, and project-convention docstring/help text.
- **Out-of-Scope**: Refactoring the FTS wrapper; adding new FTS functionality; changing the `chunks_fts` schema; enforcing read-only `SELECT` statements against `chunks_fts`; adding enforcement for `chunks_fts_docsize` table operations; implementing pre-commit hook integration (CI-only initially).

## Assumptions

- The project uses `ruff` for linting (confirmed: `pyproject.toml` line 65), not pylint. The custom lint script should follow ruff conventions if integrated as a ruff plugin, or run as a standalone tox step.
- `rg` (ripgrep) is available for scanning — confirmed by its use throughout the codebase.
- MDQ's database path `/opt/llm/db/mdq.sqlite` is confirmed separate from the RAG database (verified in `scripts/mcp_servers/mdq/mdq_service.py` line 67).
- Test files under `tests/` are excluded from scanning.

## Design decisions

- Use `rg` (ripgrep) for initial pattern matching rather than Python's `ast` module alone, because `rg` handles multi-line string literals and f-string prefixes (`f"...chunks_fts..."`, `rf"...chunks_fts..."`) more reliably than a simple regex approach.
- Combine `rg` output with AST-based function context detection to distinguish between sanctioned writes inside `rag_maintenance_service.py::rebuild_fts()` and other functions in the same file — file-level filtering alone would produce false positives within the same file.
- Exit code 0 for no violations, exit code 1 for violations found — consistent with existing checker scripts in `tools/`.

## Alternatives considered

- **AST-only approach**: Parse every `.py` file with Python's `ast` module and look for SQL strings in string literals. This would be more precise but significantly slower on large codebases and harder to maintain across Python version boundaries.
- **Integration test with mocked DB**: Would catch violations at runtime but not at development time. Static analysis catches violations earlier.
- **Pre-commit hook**: Provides faster feedback but adds local dependency. Recommend CI-only initially (lower barrier to adoption); add pre-commit integration later if needed.

## Implementation

### Target file

`tools/check_chunks_fts_invariant.py`

### Procedure

1. Scaffold the script skeleton with `uv run python tools/generate_workitem.py --kind implementation-procedure --source-plan plans/20260924-063321_plan.md --target-file-path tools/check_chunks_fts_invariant.py --seq 01`.
2. Verify the scaffolded file exists at `implementations/20260924-090000_01_check_chunks_fts_invariant_py.md` before proceeding.
3. Implement the core logic per Method below.
4. Add CLI argument support (`--path <dir>` for custom scan target).
5. Add docstring and usage help per project conventions.

### Method

The lint script will:

1. Use `rg` (ripgrep) to scan all `.py` files under `scripts/` for patterns matching `INSERT INTO chunks_fts` or `UPDATE chunks_fts`.
2. For each match, determine whether the occurrence is in a sanctioned write path or MDQ out-of-scope directory.
3. Report violations with file path, line number, and the offending SQL statement.

#### Whitelist logic

- **Sanctioned write paths** (must NOT be flagged):
  - `scripts/agent/services/rag_maintenance_service.py::rebuild_fts()` — sanctioned `/session rag-rebuild-fts` command path
  - `scripts/db/schema_sql.py` — schema initialization SQL (executed once during setup, not runtime)
- **Out-of-scope read/write paths** (not flagged):
  - `scripts/mcp_servers/mdq/` — targets a separate database (`/opt/llm/db/mdq.sqlite`)

#### Implementation details

- Use `rg -n "INSERT INTO chunks_fts\|UPDATE chunks_fts" scripts/` to get matches with line numbers.
- Filter results: skip lines within sanctioned paths (check file path + function context via AST parsing).
- Skip `scripts/mcp_servers/mdq/` entirely.
- Skip test files (`tests/`).
- Output format: `{file}:{line}: {sql_statement}` for each violation.
- Exit code: 0 if no violations, 1 if violations found.

### Details

#### Step-by-step implementation

**Step 1: Script header and imports**
- Add shebang `#!/usr/bin/env python3`.
- Add module docstring describing purpose, requirements, and usage.
- Import `argparse`, `subprocess`, `sys`, `pathlib.Path`, `ast`.

**Step 2: Configuration constants**
- Define `REPO_ROOT = Path(__file__).resolve().parent.parent`.
- Define `DOCS_DIR = REPO_ROOT / "docs"`.
- Define `SANCTIONED_PATHS = frozenset({
    "scripts/agent/services/rag_maintenance_service.py",
    "scripts/db/schema_sql.py",
})`.
- Define `EXCLUDED_DIRS = frozenset({"scripts/mcp_servers/mdq/", "tests/"})`.
- Define `SQL_PATTERNS = ["INSERT INTO chunks_fts", "UPDATE chunks_fts"]`.

**Step 3: Core scanning function**
```python
def scan_for_violations(scan_dir: Path) -> list[tuple[str, int, str]]:
    """Scan for direct chunks_fts INSERT/UPDATE outside sanctioned paths."""
    violations = []
    
    # Run rg to find all matching lines
    cmd = ["rg", "-n"]
    for pattern in SQL_PATTERNS:
        cmd.extend(["-e", pattern])
    cmd.append(str(scan_dir))
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # No matches found (exit code 1 means no matches)
        return violations
    
    # Process each match
    for line in result.stdout.strip().split("\n"):
        parts = line.split(":", maxsplit=1)
        if len(parts) != 2:
            continue
        
        file_path, rest = parts
        line_num_str, sql_stmt = rest.split(":", maxsplit=1)
        
        # Check if this is an excluded directory
        if any(excluded in file_path for excluded in EXCLUDED_DIRS):
            continue
        
        # Check if this is a sanctioned path
        if file_path in SANCTIONED_PATHS:
            # Need AST-based function context check for rag_maintenance_service.py
            if "rag_maintenance_service.py" in file_path:
                if _is_in_sanctioned_function(file_path, int(line_num_str)):
                    continue
            else:
                # schema_sql.py is always sanctioned (schema init)
                continue
        
        violations.append((file_path, int(line_num_str), sql_stmt.strip()))
    
    return violations
```

**Step 4: AST-based function context detection**
```python
def _is_in_sanctioned_function(file_path: str, line_num: int) -> bool:
    """Check if a line is inside rebuild_fts() function."""
    try:
        source = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "rebuild_fts":
            # Check if the line is within this function's body
            start_line = getattr(node, "lineno", 0)
            end_line = getattr(node, "end_lineno", 0)
            if start_line <= line_num <= end_line:
                return True
    
    return False
```

**Step 5: Main entry point**
```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect direct chunks_fts INSERT/UPDATE outside sanctioned paths."
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Directory to scan (default: repo root/scripts)",
    )
    args = parser.parse_args(argv)
    
    scan_dir = Path(args.path) if args.path else REPO_ROOT / "scripts"
    violations = scan_for_violations(scan_dir)
    
    if violations:
        for file_path, line_num, stmt in violations:
            print(f"{file_path}:{line_num}: {stmt}")
        return 1
    
    print(f"No violations found.")
    return 0
```

**Step 6: Entry point guard**
```python
if __name__ == "__main__":
    raise SystemExit(main())
```

## Compatibility considerations

- The script requires `rg` (ripgrep) to be installed and available in PATH. This is already confirmed by its use throughout the codebase.
- The AST-based function context detection relies on `ast.parse()` which may fail on syntactically invalid Python files — handled gracefully with try/except returning `False`.
- The script uses `subprocess.run()` with `capture_output=True` which requires Python 3.7+.

## Security considerations

- The script reads source files using `Path.read_text()` which could expose sensitive information if the repository contains secrets in source files — this is acceptable since the script only scans for SQL patterns, not for secret detection.
- The script does not execute any untrusted input — it only reads source files and runs `rg` with fixed patterns.

## Rollback considerations

- If the lint script produces false positives after deployment, the whitelist can be updated by adding new entries to `SANCTIONED_PATHS` or implementing additional AST-based checks.
- If the script causes CI pipeline slowdowns, consider optimizing the `rg` query or adding caching.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_chunks_fts_invariant.py` | Unit: synthetic violation detection | `uv run python tools/check_chunks_fts_invariant.py` | Exit code 1 with violation report |
| `tools/check_chunks_fts_invariant.py` | Unit: zero findings on sanctioned paths | `uv run python tools/check_chunks_fts_invariant.py` | Exit code 0, no output |
| `tools/check_chunks_fts_invariant.py` | Unit: zero findings on MDQ files | `uv run python tools/check_chunks_fts_invariant.py` | Exit code 0, no output |
| `tests/test_chunks_fts_invariant_lint.py` | Regression: lint script passes | `uv run pytest tests/test_chunks_fts_invariant_lint.py -v` | All tests pass |
| `tox.ini` | Integration: CI pipeline | `uv run tox -e lint` | No new failures |
| `docs/adr/ADR-009-rag-ft5-text-separation.md` | Manual: documentation review | Read Known Deviations section | Enforcement documented |
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual: documentation review | Read DESIGN-2 section | Status updated |

## Completion criteria

- AC-01: A lint script exists at `tools/check_chunks_fts_invariant.py` that detects direct `chunks_fts` INSERT/UPDATE references outside the whitelist (REQ-01, REQ-04)
- AC-02: Sanctioned write paths (`rag_maintenance_service.py::rebuild_fts()`, `schema_sql.py`) pass the enforcement check without false positives (REQ-02, REQ-04)
- AC-03: MDQ's `chunks_fts` access is excluded from detection (REQ-03)
- AC-04: A regression test demonstrates that an unsanctioned `chunks_fts` violation fails the enforcement check (REQ-06)
- AC-05: The enforcement runs in CI without false positives on sanctioned paths (REQ-05, REQ-06)
- AC-06: ADR-009's Known Deviations documents the new enforcement mechanism (REQ-07)
- AC-07: DESIGN-2 status reflects resolution (REQ-08)

## Out of scope

- Refactoring the FTS wrapper itself; adding new FTS functionality; changing the `chunks_fts` schema; modifying MDQ's separate database access patterns; enforcing read-only `SELECT` statements against `chunks_fts`; adding enforcement for `chunks_fts_docsize` table operations; implementing pre-commit hook integration (CI-only initially).

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
- **Requirement ID**: REQ-01, REQ-02, REQ-03, REQ-04, REQ-05
- **Source issue**: issues/20260924-054344_design2_no-test-guarantee-chunks_fts-direct-operation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-063321_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-090000
- **Related target files**: tools/check_chunks_fts_invariant.py
