## Goal

Confirm the dispatch tests survive the widened ledger SELECT and change a fixture only if a test actually fails.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: this file only, contingent. The Plan expected the raw two-column seed to break on the widened SELECT; verification showed otherwise.

## Assumptions

- Verified: the seed at about line 802 creates a bare `dedup_call_state (key, status)` table and expects `configure_dedup` to raise `legacy_or_unverified`; the store refuses it at the identity gate before any SELECT, so the widened `_fetch_locked` cannot reach it (Plan claim disproved; row kept as a contingent verification row).
- If the dispatch suite is green after rows 02-04, record `no change needed` in Step 1 Notes instead of editing the file.

## Design decisions

- Edit only when a dispatch test fails because of the new columns; keep any edit to the failing fixture.

## Alternatives considered

Rejected: removing the row from the Plan (a removed row needs maintainer approval; the verification is cheap and keeps the audit trail).

## Implementation
### Target file
`tests/mcp_servers/test_mcp_dispatch.py`

### Procedure
1. Run `uv run pytest tests/mcp_servers/test_mcp_dispatch.py` after rows 02-04 are implemented.
2. If green, make no edit and note it in the Execution Status. If a fixture fails, update that fixture to include the five nullable columns or use the real DDL, then re-run.

### Method
Prefer building fixtures through `open_dedup_store` over raw DDL.

### Details
- Do not add new tests here; classification tests live in row 26.

## Compatibility considerations

N/A: tests only.

## Security considerations

N/A: tests only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py`

## Completion criteria

- The dispatch suite is green; the Execution Status states whether the file changed.

## Out of Scope

Any production change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (result metadata and result classes at finalization), `REQ-006` (store schema bump and fingerprint refusal)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `tests/mcp_servers/test_mcp_dispatch.py`
