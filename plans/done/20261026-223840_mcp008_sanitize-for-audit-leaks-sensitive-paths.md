## Goal
Fix `_sanitize_for_audit` to redact paths with 2 or fewer components, preventing sensitive system paths from being logged in full.

## Priority
Medium

## Scope
- **In-Scope**: Replace `len(parts) <= 2` condition with a more robust redaction strategy; ensure all absolute paths are redacted regardless of component count; update docstring
- **Out-of-Scope**: Changes to the audit log format itself; changes to how paths are validated before sanitization
- **Dependencies**: N/A: none

## Background
The `_sanitize_for_audit` function at lines 150-157 of `git_server.py`:

```python
def _sanitize_for_audit(value: str) -> str:
    """Redact sensitive portions of a path for audit logging."""
    if not value:
        return ""
    parts = value.split("/")
    if len(parts) <= 2:
        return value
    return "/".join(["***"] + parts[-2:])
```

This function is used in multiple places in `call_tool` (lines 263, 300, 340) to sanitize the `repo_path` before logging.

## Problem
For paths with exactly 2 components (e.g., `/etc`, `/root`, `/`), the function returns the unredacted path because `len(parts) <= 2` evaluates to `True`. This means:
1. Sensitive paths like `/etc` are logged in full in audit logs.
2. Paths like `/root` are logged in full, exposing user credentials.
3. The redaction logic only kicks in for paths with 3+ components (e.g., `/home/user/repo` → `/***/home/user/repo`).

The condition `len(parts) <= 2` is incorrect because:
- A path like `/etc/shadow` has 3 parts after split (`["", "etc", "shadow"]`), so it IS redacted.
- But `/etc` has 2 parts (`["", "etc"]`), which is NOT redacted.
- And `/` has 2 parts (`["", ""]`), which is NOT redacted.

So the bug is specifically for paths that resolve to exactly 2 components after splitting by `/`. Examples:
- `/etc` — 2 components, logged in full
- `/root` — 2 components, logged in full
- `/` — 2 components, logged in full

These are all sensitive system paths that should be redacted.

## Reason for Change
Paths with 2 or fewer components are often sensitive system paths (e.g., `/etc`, `/root`, `/`) that should be redacted in audit logs. The current logic assumes these are safe to log, but they are not.

## Implementation Intent
Replace the `len(parts) <= 2` condition with a check for sensitive paths. Options include:
1. Always redact paths with fewer than 3 components (return `"***/..."` for all paths).
2. Maintain a list of sensitive path prefixes and redact those specifically.
3. Use a heuristic: if the first component is empty (absolute path) and the second component is a known sensitive directory, redact.

## Requirements
- `REQ-001`: Paths with 2 or fewer components are redacted in audit logs
- `REQ-002`: Existing redaction behavior for paths with 3+ components is preserved
- `REQ-003`: No sensitive paths are logged in full

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Replace `len(parts) <= 2` with more robust redaction strategy | REQ-001, REQ-002 | Confirmed: `_sanitize_for_audit` at lines 150-157 returns unredacted paths with ≤2 components (checked in Step 3) | Unit test for path redaction | Needs confirmation |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tests/mcp_servers/git/test_git_server.py | Verify existing path sanitization patterns | REQ-001 |

## Acceptance Criteria
- Paths with 2 or fewer components are redacted in audit logs (REQ-001)
- Existing redaction behavior for paths with 3+ components is preserved (REQ-002)
- No sensitive paths are logged in full (REQ-003)

## Tests
- Unit test: verify `/etc` is redacted (REQ-001)
- Unit test: verify `/root` is redacted (REQ-001)
- Unit test: verify `/home/user/repo` is still redacted as before (REQ-002)
- Regression test: ensure existing redaction behavior is preserved (REQ-003)

## Documentation Impact
Update `_sanitize_for_audit` docstring to document the redaction policy.

## Assumptions
- All absolute paths (starting with `/`) should be redacted regardless of component count
- The `***` prefix convention should be preserved for consistency
- Relative paths (not starting with `/`) should continue to be passed through unchanged

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What is the minimum number of components that should be redacted? | Need to decide on redaction policy | Review security requirements | False |
| UNK-02 | Should relative paths be treated differently? | Need to check if relative paths can contain sensitive information | Review git-mcp usage patterns | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Low | N/A | N/A | No impact |

## Design
- **Approach**: Replace `len(parts) <= 2` with `len(parts) <= 3` to redact paths with 3 or fewer components. This ensures that all absolute paths (which start with `/` and produce an empty first component) are redacted.
- **Rationale**: Absolute paths always have an empty first component after splitting by `/`. Redacting paths with ≤3 components ensures that even short absolute paths like `/etc`, `/root`, and `/` are redacted, while longer paths like `/home/user/repo` continue to be redacted as before.
- **Alternative considered**: Maintaining a list of sensitive path prefixes — this would be more precise but requires maintaining a list and could miss new sensitive paths.

## Implementation steps
1. **Phase 1: Preparation**
   - [ ] Verify test file path exists under `tests/mcp_servers/git/` (Requirement ID: REQ-001; File Path: tests/mcp_servers/git/test_git_server.py)
2. **Phase 2: Core Logic Implementation**
   - [ ] Replace `len(parts) <= 2` with `len(parts) <= 3` in `_sanitize_for_audit` (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
   - [ ] Update `_sanitize_for_audit` docstring to document the redaction policy (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)
3. **Phase 3: Testing & Verification**
   - [ ] Run lint/type checks on modified files (Requirement ID: REQ-001; File Path: scripts/mcp_servers/git/git_server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Unit test | uv run pytest tests/mcp_servers/git/test_git_server.py -v | Test passes; paths with ≤3 components are redacted |
| scripts/mcp_servers/git/git_server.py | Lint check | uv run ruff check scripts/mcp_servers/git/git_server.py | Clean (no findings) |
| scripts/mcp_servers/git/git_server.py | Type check | uv run mypy scripts/mcp_servers/git/git_server.py | Clean (no type errors) |

## Risks
- **Risk**: Changing `len(parts) <= 2` to `len(parts) <= 3` may over-redact some non-sensitive paths → **Mitigation**: Only absolute paths (starting with `/`) are affected; relative paths continue to pass through unchanged
- **Risk**: The `***` prefix may not be appropriate for very short paths → **Mitigation**: The `***` prefix is consistent with the existing redaction convention; short paths like `/etc` should also be fully redacted

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation — verify test file path | Pending | — | — | |
| 2 | Phase 2: Core Logic — fix path redaction | Pending | — | — | |
| 3 | Phase 3: Testing & Verification — add unit test and run checks | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261026-220730_mcp008-sanitize-for-audit-leaks-sensitive-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-223840
- **Related target files**: scripts/mcp_servers/git/git_server.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue Section | Target File | Implementation Step | Acceptance Criterion | Test or Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 2 | Paths with ≤2 components redacted | Unit test for path redaction | Confirmed by repository evidence |
| REQ-002 | Problem, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 2 | Existing redaction preserved | Unit test for long paths | Confirmed by repository evidence |
| REQ-003 | Reason for Change, Acceptance Criteria | scripts/mcp_servers/git/git_server.py | Phase 3 | No sensitive paths leaked | Regression test for redaction | Needs confirmation |
