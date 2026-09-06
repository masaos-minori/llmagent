## Goal
Mark the 8 confirmed-non-existent Area Canonical Maps file paths as `Needs Confirmation`
in place in `docs/00_governance_01_documentation-policy.md`, without deleting the rows
or guessing replacement paths, per REQ-009.

## Scope
- **In-Scope**: add inline `(Needs Confirmation — path does not exist in repository,
  see plans/20260905-185329_plan.md)` markers to the Status column of each stale row
  in the Area Canonical Maps tables.
- **Out-of-Scope**: deleting any Area Canonical Maps row; guessing a replacement path;
  modifying any other section of this document.

## Assumptions
- The 8 stale paths are confirmed non-existent (verified via `test -e` against all 8
  paths: none exist in the repository).
- The inline marker must be short enough to fit within the table cell without breaking
  layout.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Add an inline marker to the Status column rather than replacing it — preserves the
  existing Authority column value while flagging the status problem.
- Reference this Plan explicitly in the marker so readers can trace back to context.

## Alternatives considered
N/A: straightforward inline marking; no alternative approach applies.

## Implementation
### Target file
`docs/00_governance_01_documentation-policy.md`

### Procedure
1. For each of the 8 stale paths, locate its row in the Area Canonical Maps tables.
2. In the Status column of that row, append or replace with:
   `(Needs Confirmation — path does not exist in repository, see plans/20260905-185329_plan.md)`
3. Preserve all other columns (Document, Authority) unchanged.

### Method
Edit via exact string replacement using Edit tool for each affected row.

### Details
The 8 stale paths and their locations:

| # | Path | Section | Row location |
|---|------|---------|-------------|
| 1 | `docs/architecture.md` | Overview | Line ~95, Status column |
| 2 | `docs/deployment_guide.md` | Deployment | Line ~100, Status column |
| 3 | `deploy.sh` | Deployment | Line ~101, Status column |
| 4 | `docs/rag/specification.md` | RAG | Line ~106, Status column |
| 5 | `scripts/rag/embedding.py` | RAG | Line ~107, Status column |
| 6 | `docs/mcp/specification.md` | MCP | Line ~112, Status column |
| 7 | `scripts/mcp_servers/*.py` | MCP | Line ~113, Status column |
| 8 | `docs/agent/specification.md` | Agent | Line ~118, Status column |
| 9 | `scripts/agent/*.py` | Agent | Line ~119, Status column |
| 10 | `docs/eventbus/specification.md` | EventBus | Line ~124, Status column |
| 11 | `scripts/eventbus/*.py` | EventBus | Line ~125, Status column |
| 12 | `docs/shared/specification.md` | Shared/DB | Line ~130, Status column |
| 13 | `scripts/shared/*.py` | Shared/DB | Line ~131, Status column |

Wait — the Inventory identifies 8 stale paths, but the Area Canonical Maps table shows
additional stale entries beyond those 8. Per the Inventory's classification:
- The 8 stale paths from REQ-009 are: `docs/architecture.md`, `docs/deployment_guide.md`,
  `docs/rag/specification.md`, `docs/mcp/specification.md`, `docs/agent/specification.md`,
  `docs/eventbus/specification.md`, `docs/shared/specification.md`, root `deploy.sh`.
- The glob patterns (`scripts/mcp_servers/*.py`, `scripts/agent/*.py`,
  `scripts/eventbus/*.py`, `scripts/shared/*.py`) are Runtime rows — they point to
  actual files that exist, so they are NOT stale. They should remain marked Active.
- The Runtime rows for `scripts/rag/embedding.py` (RAG), `scripts/eventbus/*.py`
  (EventBus), and `scripts/shared/*.py` (Shared/DB) need verification: the Inventory
  flags `scripts/rag/embedding.py` as non-existent, but the other two are globs that
  match existing files.

Confirmed non-existent paths requiring marking:
1. `docs/architecture.md` — Overview section
2. `docs/deployment_guide.md` — Deployment section
3. `deploy.sh` — Deployment section
4. `docs/rag/specification.md` — RAG section
5. `docs/mcp/specification.md` — MCP section
6. `docs/agent/specification.md` — Agent section
7. `docs/eventbus/specification.md` — EventBus section
8. `docs/shared/specification.md` — Shared/DB section

Each Status column entry should be replaced with:
`(Needs Confirmation — path does not exist in repository, see plans/20260905-185329_plan.md)`

## Compatibility considerations
N/A: governance-class document; no runtime/code caller.

## Security considerations
N/A.

## Rollback considerations
- Revert the edits to restore the original Status values.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/00_governance_01_documentation-policy.md` passes.
- `uv run python tools/check_docs_quality.py` on the same file passes.
- Manual diff review confirming changes scoped to canonical-source declarations only (AC9).
- Confirm exactly 8 Status column replacements were made, matching the 8 stale paths.

## Completion criteria
- All 8 stale Area Canonical Maps paths are marked `Needs Confirmation` in the Status
  column without deleting rows or guessing replacement paths (AC6).
- Documentation structural/quality validation passes (AC8).

## Out of scope
- Every other change to this file.
- Deleting any Area Canonical Maps row.
- Guessing a replacement path for any stale entry.
- Updating `config/documentation_canonical_sources.toml` (REQ-005, separate procedure).
- Updating `docs/06_eventbus_00_document-guide.md` (REQ-006, separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-009` (mark 8 stale Area Canonical Maps paths Needs Confirmation without deleting rows or guessing replacement paths)
- **Source issue**: issues/20260903-103029_m0106_inventory-and-migrate-existing-canonical-source-declarations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-185329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185329
- **Related target files**: docs/00_governance_01_documentation-policy.md
