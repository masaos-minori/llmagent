## Goal

Update the dedup design document for version 2 and the result metadata: the stamp, the stored result shape, and the replay classification.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the lines that state `PRAGMA user_version = 1` (about lines 56 and 204), the truncated-sentinel description (about line 98), and the replay table row for truncated payloads.

## Assumptions

- Verified: the document states version 1 in two places and describes the truncated sentinel `{truncated, sha256, preview}`; the sentinel itself is unchanged by this work.

## Design decisions

- Keep the sentinel description and add the stored columns and result classes next to it.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Procedure
1. Change both version statements to 2.
2. Add the five metadata columns and the four result classes after the sentinel paragraph, stating that previews are redacted before truncation and that replay behavior for truncated payloads is unchanged.
3. Add a short pointer to the control endpoints document for how classes are exposed.

### Method
Prose edits only.

### Details
- Do not change the replay decision table semantics.

## Compatibility considerations

N/A: no behavior change in this row.

## Security considerations

N/A: documentation only; no secret value, approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`

## Completion criteria

- No remaining statement says the stamp is 1; the metadata and classes are documented; the gates pass.

## Out of Scope

The active-databases document (row 33).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (store schema bump and fingerprint refusal), `REQ-007` (documentation of the control contract)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
