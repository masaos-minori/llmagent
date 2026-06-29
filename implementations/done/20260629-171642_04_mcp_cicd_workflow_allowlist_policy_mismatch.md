# Implementation: Add cicd workflow_allowlist policy mismatch (MCP-09) to known issues

## Goal

Add the missing cicd workflow_allowlist policy mismatch entry (MCP-09) to `04_mcp_90_inconsistencies_and_known_issues.md` and update `04_mcp_00_document-guide.md` navigation table to reflect all active issues.

## Scope

- **In-Scope**:
  - Add MCP-09 (cicd workflow_allowlist policy mismatch) to `04_mcp_90_inconsistencies_and_known_issues.md`
  - Verify that MCP-01 through MCP-08 already cover the other 7 required items (confirmed: all present)
  - Update `04_mcp_00_document-guide.md` Navigation to Known Issues table to list MCP-09
- **Out-of-Scope**:
  - Fixing the underlying code inconsistency (security_profile / RuntimeError not implemented)
  - Updating any other docs outside the two target files

## Assumptions

- MCP-01 through MCP-08 in `04_mcp_90` already cover: startup mode terminology, routing authority, rag-pipeline tool count, transport error/HealthRegistry, mdq production-ready vs stub marker, audit log format, and health semantics ambiguity (two entries: DEGRADED diagram + HTTP status code watchdog gap).
- The cicd `security_profile = "production"` → `RuntimeError` behavior described in `04_mcp_04:273` does not exist in `scripts/mcp/cicd/service_guards.py` — this is the concrete mismatch for MCP-09.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether `security_profile = "production"` is intended to raise RuntimeError or was a planned-but-unimplemented feature | No TODO/issue tracking comment in service_guards.py — treat as doc mismatch until confirmed |
| UNK-02 | Whether `04_mcp_00` Navigation table should list all 9 active issues or only notable ones | Follow existing pattern (table is selective, not exhaustive); add MCP-09 as a notable entry |

## Implementation

### Target file: `docs/04_mcp_90_inconsistencies_and_known_issues.md`

#### Procedure

Append MCP-09 entry after MCP-08.

#### Method

Direct file edit — append new section.

#### Details

**Add after line 170 (after MCP-08):**
```markdown
### MCP-09: cicd workflow_allowlist policy mismatch — RuntimeError vs warning

**Type:** Document inconsistency
**Impact scope:** `04_mcp_04`, `scripts/mcp/cicd/service_guards.py`

**Statement A:** `04_mcp_04:273` — "in production mode (`security_profile = "production"`), empty `workflow_allowlist` raises `RuntimeError` at agent startup"

**Statement B:** `scripts/mcp/cicd/service_guards.py` — no `security_profile` field exists in cicd config; empty `workflow_allowlist` only emits a warning log, never raises `RuntimeError`. The actual behavior is:
- `cicd-mcp: workflow_allowlist is empty — all workflow triggers will be denied` (warning logged)
- All workflow trigger requests are rejected (fail-closed)

**Impact:** Operators relying on RuntimeError to catch misconfiguration will not see it; the server starts successfully with a warning. AI routing systems that parse `04_mcp_04` may incorrectly assume RuntimeError prevents startup.

**Current safe interpretation:** Empty `workflow_allowlist` is fail-closed (denies all triggers) but does NOT raise RuntimeError. A startup warning is logged. Do not rely on RuntimeError to catch misconfiguration.

**Recommended action:** Either implement the RuntimeError in service_guards.py (when security_profile=="production" and workflow_allowlist is empty), or remove the RuntimeError claim from `04_mcp_04`.

**Notes for AI reference:** Do not assume RuntimeError prevents startup when workflow_allowlist is empty. Only a warning is emitted. Operators must check the warning log proactively.
```

### Target file: `docs/04_mcp_00_document-guide.md`

#### Procedure

Update Navigation to Known Issues table to add MCP-09 row.

#### Method

Direct file edit — add new table row.

#### Details

**Add after line 79 (after the mdq-mcp row):**
```markdown
| cicd workflow_allowlist RuntimeError claim mismatch | [MCP-09](04_mcp_90_inconsistencies_and_known_issues.md#mcp-09) |
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `04_mcp_90_inconsistencies_and_known_issues.md` | Grep for MCP-09 | `grep -n "MCP-09"` | Entry present with all required fields |
| `04_mcp_90_inconsistencies_and_known_issues.md` | Confirm no resolved section mixed in | `grep -n "RESOLVED\|Resolved"` | No resolved entries (or clearly separated section) |
| `04_mcp_00_document-guide.md` | Grep for MCP-09 | `grep -n "MCP-09"` | Navigation row present |
| `scripts/mcp/cicd/service_guards.py` | Confirm no RuntimeError exists (baseline) | `grep -n "RuntimeError\|security_profile"` | No match — confirms the mismatch is real |

## Risks & Mitigations

- **Risk**: MCP-09 entry is added but the underlying code gap (RuntimeError not implemented) causes confusion if a future implementer adds the RuntimeError without reading the known-issues doc → **Mitigation**: The "Recommended action" field explicitly names both options (implement or remove the doc claim); the Notes for AI reference warns not to assume RuntimeError behavior.
- **Risk**: `04_mcp_00` file index description for `04_mcp_90` still references old entry tags (MISSING-01/SPEC-01/02/03) → **Mitigation**: Update the File Index description row for `04_mcp_90` to reflect MCP-01 through MCP-09.
