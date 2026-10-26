# Plan: _audit_failure_count mutable global without synchronization

## Goal
Replace the non-thread-safe `_audit_failure_count` counter in `git_server.py` with a thread-safe synchronization mechanism to prevent lost increments under concurrent load.

## Priority
Medium

## Scope
- **In-Scope**: Replace `_audit_failure_count` with a thread-safe counter in `scripts/mcp_servers/git/git_server.py`
- **Out-of-Scope**: Changes to audit log format, changes to how audit failures are detected, changes to other MCP servers' counter logic
- **Dependencies**: N/A: none

## Background
The `_audit_failure_count` variable in `git_server.py` is a mutable global integer that is incremented without thread-safe synchronization, creating a race condition under concurrent requests.

## Problem
The `_audit_failure_count += 1` operation is not atomic in Python. Under concurrent requests, multiple threads can read the same value, increment it, and write back the same result — losing increments. This is a classic TOCTOU (time-of-check-time-of-use) race condition.

For example:
1. Thread A reads `_audit_failure_count = 5`
2. Thread B reads `_audit_failure_count = 5`
3. Thread A writes `_audit_failure_count = 6`
4. Thread B writes `_audit_failure_count = 6` (should be 7)

The health endpoint then reports `6` instead of `7`, making monitoring unreliable.

Additionally, the variable is accessed from both the async handler (via `_audit_log_safe`) and the health endpoint without any synchronization, which means:
1. The health endpoint may see stale values due to Python's GIL not guaranteeing atomicity of compound operations.
2. The variable is not thread-safe even under CPython's GIL because `+=` involves a read-modify-write cycle.

## Reason for Change
A non-thread-safe counter makes monitoring unreliable and can lead to under-reporting of audit failures under concurrent load.

## Implementation Intent
Replace the mutable global integer with a thread-safe counter using `threading.Lock` to protect the increment operation. Document the synchronization strategy in a comment near `_audit_failure_count`.

## Requirements
- `REQ-001`: Counter increments must not be lost under concurrent load
- `REQ-002`: Health endpoint must read the correct counter value
- `REQ-003`: No performance regression from synchronization overhead

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Replace `_audit_failure_count` with thread-safe counter | REQ-001, REQ-002, REQ-003 | Confirmed by repository evidence (checked in Step 2) | Needs confirmation | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/mcp_servers/server.py | Verify `_audit_log` signature used by `_audit_log_safe` | git_server.py |

## Acceptance Criteria
- Counter increments are not lost under concurrent load (REQ-001)
- Health endpoint reads the correct counter value (REQ-002)
- No performance regression from synchronization overhead (REQ-003)

## Tests
- Concurrency test: verify counter increments are not lost under concurrent load (REQ-001)
- Unit test: verify thread-safe increment operation (REQ-001)
- Regression test: ensure existing counter behavior is preserved (REQ-003)

## Documentation Impact
Document the synchronization strategy in a comment near `_audit_failure_count` in `scripts/mcp_servers/git/git_server.py`.

## Assumptions
- uvicorn is running in multi-worker mode (otherwise a single worker would eliminate the need for thread safety)
- The `global _audit_failure_count` declaration in `_audit_log_safe` is intentional and required for the module-level variable

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Is uvicorn running in single-worker mode (which would eliminate the need for thread safety)? | Need to check uvicorn configuration | Check uvicorn config; if single-worker, use asyncio.Lock instead of threading.Lock | False |
| UNK-02 | Are there other MCP servers with the same pattern? | Need to search other MCP servers for similar mutable global counters | Search other MCP servers; if found, consider cross-server fix | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Modify | Low | N/A | N/A | None |

## Design
- Use `threading.Lock` to protect the `_audit_failure_count` increment operation. This is the most straightforward approach and works regardless of whether uvicorn runs in single-worker or multi-worker mode.
- If UNK-01 confirms single-worker mode, `asyncio.Lock` could be used instead, but `threading.Lock` is safer as a default since it works in both modes.
- The lock should be acquired only around the increment operation, not around the entire `_audit_log_safe` function, to minimize contention.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Add thread-safe counter**
   - [ ] Add `import threading` at module level (scripts/mcp_servers/git/git_server.py)
   - [ ] Replace `_audit_failure_count: int = 0` with `_audit_failure_count_lock = threading.Lock()` and `_audit_failure_count: int = 0` (scripts/mcp_servers/git/git_server.py)
   - [ ] Add a comment documenting the synchronization strategy near `_audit_failure_count` (scripts/mcp_servers/git/git_server.py)

2. **Phase 2: Protect increment operation**
   - [ ] Update `_audit_log_safe` to acquire the lock before incrementing `_audit_failure_count` (scripts/mcp_servers/git/git_server.py)
   - [ ] Ensure the lock is released even if an exception occurs (use context manager)

3. **Phase 3: Deployment & Verification**
   - [ ] Verify no other code reads `_audit_failure_count` outside the lock (scripts/mcp_servers/git/git_server.py)
   - [ ] Run lint/type checks on modified file

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/git/git_server.py | Unit test for thread-safe increment | pytest | Counter increments are not lost under concurrent load |
| scripts/mcp_servers/git/git_server.py | Concurrency stress test | pytest + threading | Health endpoint reads correct counter value |

## Risks
- **Risk**: Lock contention under high concurrency → **Mitigation**: Lock is acquired only around the increment operation, not the entire `_audit_log_safe` function
- **Risk**: Lock acquisition failure → **Mitigation**: Use `with` context manager to ensure lock release even on exceptions

## Execution Status

Table structure, status/type vocabulary, and general guidance: see templates/execution-status.md. Default rows for a freshly generated Plan (replace with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Add thread-safe counter | Pending | — | — | scripts/mcp_servers/git/git_server.py |
| 2 | Phase 2: Protect increment operation | Pending | — | — | scripts/mcp_servers/git/git_server.py |
| 3 | Phase 3: Deployment & Verification | Pending | — | — | scripts/mcp_servers/git/git_server.py |

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
- **Source issue**: issues/20261026-220730_mcp012-git-audit-failure-count-mutable-global-no-synchronization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-224641
- **Related target files**: scripts/mcp_servers/git/git_server.py

### Requirement Traceability
See templates/requirement-traceability.md for the canonical column format.
