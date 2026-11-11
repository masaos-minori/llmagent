## Goal

Align the mdq startup validation statement in `mcp_02_02` to the single fingerprint mechanism
(`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 109 currently states mdq-mcp "verifies the `documents`, `chunks`, `chunks_fts` tables and
  their sync triggers", an existence-only check; this is replaced by fingerprint matching.
- The stale-detection and row-count fields in the same table are unaffected.

## Design decisions
- Replace the table-existence verification with fingerprint matching as the mdq startup validation.

## Alternatives considered
N/A: documentation-only change; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/22_mcp/mcp_02_02_startup-modes-and-health.md`

### Procedure
1. Line 109: replace "verifies the `documents`, `chunks`, `chunks_fts` tables and their sync
   triggers" with "validates `mdq.sqlite` against the current canonical schema by the shared
   fingerprint; a mismatch is refused".

### Method
- Locate the clause with
  `rg -n 'verifies the .documents., .chunks., .chunks_fts. tables' docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
  before editing.

### Details
- The surrounding health-response semantics (lines 44-58) are unaffected.

## Compatibility considerations
Cross-references to `mcp_05_05` (mdq enforcement) remain valid.

## Security considerations
None beyond the existing Fail-Fast refusal narrative.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run python tools/check_docs_consistency.py --domain mcp` passes; no document claims a validation
mechanism other than fingerprint matching.

## Completion criteria
Line 109 describes fingerprint matching as the mdq startup validation; the table-existence wording is
removed.

## Out of Scope
Changing the mdq auth token or health-response semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Align the mdq startup validation statement | Completed | — | 20261111-151259 | mdq row now states fingerprint startup validation; health dependency-report wording kept because the code health diagnostic remains existence-based |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-151259 | check_docs_consistency --domain mcp passes |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-151300 | health-response semantics and stale/row-count fields unchanged |

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
- **Requirement ID**: `REQ-006` — align the mdq startup validation statement
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`