## Goal

Correct a self-contradiction in reading-audit-logs.md regarding whether cicd-mcp and git-mcp use the shared audit log.

## Scope

- **In-Scope**:
  - Edit `docs/04_mcp_06_07_reading-audit-logs.md` to fix the misleading blockquote note at lines 50-52.
- **Out-of-Scope**:
  - Modifying `docs/04_mcp_02_03_audit-logging-and-errors.md`.
  - Any changes to source code or other documentation files.

## Assumptions

1. The tables in `docs/04_mcp_06_07_reading-audit-logs.md` (lines ~69-82 and ~84-97) are correct and reflect the actual implementation.
2. The requirement is purely documentation-based.

## Design decisions

- Use targeted replacement of the specific contradictory blockquote rather than rewriting surrounding sections.
- Align the correction with the authoritative tables already present in the document.

## Alternatives considered

- Rewrite the entire section on MCP server audit behavior: rejected because it risks introducing new errors and exceeds scope.
- Delete the contradictory blockquote entirely: rejected because readers lose context; a corrected statement is preferable.

## Compatibility considerations

- Readers who previously assumed cicd-mcp/git-mcp did not use the shared audit log will see the correction.
- No API contract changes — this is purely a documentation correction.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the tables referenced in the validation plan have been modified since the original analysis, re-verify before editing.
- If the source code behavior has changed (e.g., cicd-mcp/git-mcp no longer call `_audit_log()`), update accordingly.

## Implementation

### Target file

`docs/04_mcp_06_07_reading-audit-logs.md`

### Procedure

**Phase 1: Verification**

1. Verify that the file contains the contradictory blockquote at line 50.
2. Confirm that `scripts/mcp_servers/cicd/cicd_server.py` and `scripts/mcp_servers/git/git_server.py` indeed call `_audit_log()`.

### Method

Verification via grep commands.

### Details

```bash
# Verify the contradictory blockquote exists
sed -n '48,54p' docs/04_mcp_06_07_reading-audit-logs.md

# Verify cicd-mcp uses _audit_log()
grep -n "_audit_log(" scripts/mcp_servers/cicd/cicd_server.py

# Verify git-mcp uses _audit_log()
grep -n "_audit_log(" scripts/mcp_servers/git/git_server.py
```

**Phase 2: Documentation Update**

Replace the misleading blockquote at lines 50-52 with a corrected version.

### Method

Direct file edit using sed or manual editing.

### Details

- Find the blockquote at lines 50-52 that claims cicd-mcp/git-mcp do NOT use the shared audit log.
- Replace with prose such as:
  > Note: `cicd-mcp`, `git-mcp`, and `mdq-mcp` all use the shared audit log via `_audit_log()`.

**Phase 3: Validation**

Manually verify the document reads coherently and matches the subsequent tables.

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Contradiction check | `grep` | `docs/04_mcp_06_07_reading-audit-logs.md` | No claim that `cicd-mcp`/`git-mcp` use *only* `logging.getLogger`. |
| Correctness check | `grep` | `docs/04_mcp_06_07_reading-audit-logs.md` | Contains mention of `_audit_log()` for these servers. |

## Out of scope

- Source code modifications (`scripts/`).
- Changes to `docs/04_mcp_02_03_audit-logging-and-errors.md`.
- Modifications to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260802-075026_mcp_audit_logging_contradiction_and_code_example_removal.md
- Source requirement: requires/20260802-145232_require.md
- Source plan: plans/20260804-122650_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-193025
- Related target files: docs/04_mcp_06_07_reading-audit-logs.md
