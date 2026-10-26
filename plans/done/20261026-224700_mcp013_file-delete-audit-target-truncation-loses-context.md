# Plan: file/delete_server.py audit target truncation loses context

## Goal
Add a `full_path` field to the audit log entry in `delete_server.py` that stores the untruncated path, preserving critical information for forensic analysis while keeping the 80-character truncation for display purposes.

## Priority
Low

## Scope
- **In-Scope**: Add `full_path` field to audit log entry in `scripts/mcp_servers/file/delete_server.py`
- **Out-of-Scope**: Changes to audit log format beyond adding the new field, changes to how paths are validated before auditing, changes to other MCP servers' audit logic
- **Dependencies**: N/A: none

## Background
The `call_tool` endpoint in `delete_server.py` (lines 209-250) truncates the audit target to 80 characters at line 213, which can lose critical path information for long paths.

The `audit_target` is truncated to 80 characters at line 213:

```python
audit_target = cast(str, req.args.get("path", ""))[:80]
```

This same pattern appears in other MCP servers:
- `git_server.py` line 401: `target=target[:80]`
- `mdq_server.py` line 401: `target=target[:80]`

## Problem
Truncating the path to 80 characters can lose critical information:
1. For paths longer than 80 characters, the truncated path may not uniquely identify the file being deleted.
2. Two different files with the same first 80 characters will produce identical audit entries, making it impossible to distinguish between them.
3. The truncation is applied before the audit log entry is created, so the full path is not available for forensic analysis.

For example:
- `/home/user/documents/project-alpha/src/main.py` → `/home/user/documents/project-alpha/src/main.py` (no truncation needed)
- `/home/user/documents/project-alpha/src/main.py.bak` → `/home/user/documents/project-alpha/src/main.py.bak` (no truncation needed)
- `/home/user/documents/project-alpha/src/main.py.backup.20241026` → `/home/user/documents/project-alpha/src/main.py.backu` (truncated, loses `.backup.20241026`)

## Reason for Change
Truncating the path to 80 characters can lose critical information needed for forensic analysis. A more robust approach would either use a hash-based identifier or store the full path in a separate field.

## Implementation Intent
Use the existing `requested_target` parameter of `_audit_log` to store the untruncated path, while keeping the 80-character truncation as `target` for display purposes. This leverages the existing audit log schema without adding new fields.

## Requirements
- `REQ-001`: Full path must be available for forensic analysis via `requested_target` field
- `REQ-002`: Truncated path must still be used for display purposes via `target` field
- `REQ-003`: No breaking changes to the audit log format

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/file/delete_server.py | Modify | Pass untruncated path as `requested_target` to `_audit_log` | REQ-001, REQ-002, REQ-003 | Confirmed by repository evidence (checked in Step 2) | Needs confirmation | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/mcp_servers/audit.py | Verify `_audit_log` signature and `requested_target` parameter handling | delete_server.py |

## Acceptance Criteria
- Full path is available for forensic analysis (REQ-001)
- Truncated path is still used for display purposes (REQ-002)
- No breaking changes to the audit log format (REQ-003)

## Tests
- Unit test: verify full path is stored in audit log (REQ-001)
- Integration test: verify audit log distinguishes between similar paths (REQ-001)
- Regression test: ensure existing audit log format is preserved (REQ-003)

## Documentation Impact
Update the audit log schema documentation to include the new `full_path` field.

## Assumptions
- The `_audit_log` function's `requested_target` parameter is intended for the original user-provided value before normalization
- The audit log format change is backward-compatible (the `requested_target` field already exists in the schema)

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | What is the maximum path length that should be supported? | Need to check filesystem path length limits | Check OS path length limits; if very long, consider truncation strategy | False |
| UNK-02 | Are there other MCP servers with the same pattern? | Need to search other MCP servers for similar truncation | Search other MCP servers; if found, consider cross-server fix | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/file/delete_server.py | Modify | Low | N/A | N/A | None |

## Design
- Use the existing `requested_target` parameter of `_audit_log` to store the untruncated path.
- Keep the existing `target` parameter with the 80-character truncation for display purposes.
- In `delete_server.py`, pass the untruncated path as `requested_target` and the truncated path as `target`.
- If UNK-01 reveals very long paths, consider whether the `requested_target` field should also have a reasonable upper bound (e.g., 4096 characters for Windows MAX_PATH).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Pass untruncated path as requested_target**
   - [ ] In `call_tool` endpoint, keep the untruncated path value before truncation (scripts/mcp_servers/file/delete_server.py)
   - [ ] Pass the untruncated path as `requested_target` keyword argument to `_audit_log` (scripts/mcp_servers/file/delete_server.py)

2. **Phase 2: Deployment & Verification**
   - [ ] Verify the `_audit_log` function includes `requested_target` in the audit record output (scripts/mcp_servers/audit.py)
   - [ ] Run lint/type checks on modified file

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/file/delete_server.py | Unit test for requested_target storage | pytest | Full path is stored in requested_target field |
| scripts/mcp_servers/file/delete_server.py | Integration test for path distinction | pytest | Audit log distinguishes between similar paths via requested_target |

## Risks
- **Risk**: Existing audit log consumers may not expect `requested_target` to contain a file path → **Mitigation**: The `requested_target` field already exists in the schema; this change only populates it with a different value
- **Risk**: Very long paths consuming excessive storage → **Mitigation**: Consider adding an upper bound (e.g., 4096 characters) to the `requested_target` field if UNK-01 reveals this concern

## Execution Status

Table structure, status/type vocabulary, and general guidance: see templates/execution-status.md. Default rows for a freshly generated Plan (replace with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Pass untruncated path as requested_target | Pending | — | — | scripts/mcp_servers/file/delete_server.py |
| 2 | Phase 2: Deployment & Verification | Pending | — | — | scripts/mcp_servers/audit.py |

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
- **Source issue**: issues/20261026-220730_mcp013-file-delete-audit-target-truncation-loses-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261026-224700
- **Related target files**: scripts/mcp_servers/file/delete_server.py

### Requirement Traceability
See templates/requirement-traceability.md for the canonical column format.
