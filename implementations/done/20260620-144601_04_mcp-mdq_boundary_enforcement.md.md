# Implementation: docs/04_mcp-mdq.md (update — add Boundary Enforcement section)

## Goal

Add a "Boundary Enforcement" section to `docs/04_mcp-mdq.md` documenting the automated
check (`test_mdq_rag_boundary.py`), the allowed vs forbidden access paths table, and
guidance on handling false positives.

## Scope

**In:**
- Add a new `## Boundary Enforcement` section after `## Agent Access Patterns` (line 55)
  and before `## Known Issues` (line 91)

**Out:**
- Changes to existing sections
- Changes to other documentation files

## Assumptions

- `## Agent Access Patterns` ends before `## Known Issues` at line 91
- A new `## Boundary Enforcement` section fits between these two sections without
  disrupting the document flow
- The allowed/forbidden tables in the plan are the canonical source

## Implementation

### Target file

`docs/04_mcp-mdq.md`

### Procedure

1. Locate the line immediately before `## Known Issues` (line 91)
2. Insert the following new section above it:

```markdown
## Boundary Enforcement

An automated pytest check (`tests/test_mdq_rag_boundary.py`) verifies the MDQ/RAG
boundary on every CI run. It scans source files for forbidden cross-DB references
and disallowed direct SQLite access in the agent layer.

### Allowed access paths

| Layer | DB | Mechanism | Context |
|---|---|---|---|
| `mcp/mdq/` | `mdq.sqlite` | Own service | Normal operation |
| `mcp/rag_pipeline/` | `rag.sqlite` | Own service | Normal operation |
| Agent layer | `session.sqlite` | `SQLiteHelper("session")` | Normal operation |
| Agent layer | `workflow.sqlite` | `SQLiteHelper("workflow")` | Normal operation |
| Agent layer | `rag.sqlite` | `SQLiteHelper("rag")` via `DbMaintenanceService` | Admin-only `/db` commands |

### Forbidden access paths

| Layer | DB | Reason |
|---|---|---|
| `mcp/mdq/` | `rag.sqlite` | Cross-DB dependency |
| `mcp/rag_pipeline/` | `mdq.sqlite` | Cross-DB dependency |
| Agent layer (normal) | `mdq.sqlite` or `rag.sqlite` | Use MCP tools, not direct DB access |

### Handling false positives

If a new admin maintenance file requires direct `rag.sqlite` access, add its filename
to the `ALLOWED` set in `tests/test_mdq_rag_boundary.py` and document the exception
in the allowed-paths table above. Changes to `ALLOWED` require a design review comment
in the PR.
```

### Details

- Insert before `## Known Issues`, not after it — keeps logical flow:
  normal operation → access patterns → enforcement → known issues
- The table format matches existing tables in the file
- No changes to `## Agent Access Patterns` content above

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Section present | `grep -n "Boundary Enforcement" docs/04_mcp-mdq.md` | 1 match |
| Allowed table present | `grep -n "Allowed access paths" docs/04_mcp-mdq.md` | 1 match |
| Forbidden table present | `grep -n "Forbidden access paths" docs/04_mcp-mdq.md` | 1 match |
| test file referenced | `grep -n "test_mdq_rag_boundary" docs/04_mcp-mdq.md` | 1 match |
| Markdown lint | `markdownlint docs/04_mcp-mdq.md` | 0 errors |
