## Goal
Remove `This replaces the previous per-call random key: before this change ...` from `mcp_03_03`, keeping the current key derivation (`REQ-004` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- The retained fact: an identical logical call re-derives the byte-identical key across retries, processes, and restarts (derived from the call content and a caller-stable `uid`).
- Overlap: adrrev019 edits another passage (compatible).

## Design decisions
- Delete the two history sentences; keep the derivation and the re-derivation guarantee.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/22_mcp/mcp_03_03_transport-and-health.md`

### Procedure
1. Delete from `This replaces the previous per-call random key` through the end of that narrative sentence (`... carried a fresh key.`).

### Method
- Re-read the paragraph after the edit to confirm it still explains why a retried call is deduplicated.

### Details
- No `before this change` wording remains.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain mcp` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- The paragraph describes only the current key derivation.

## Out of Scope
- Dispatch code; other `mcp_03_*` documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — remove the `replaces the previous` narrative
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/22_mcp/mcp_03_03_transport-and-health.md`
