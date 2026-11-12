## Goal
Rewrite the `compatrm001`, `wfaudit010`, and `dbmig001` passages of `db_03_07` as current statements (`REQ-004` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- Four passages: the Bootstrap bullet (`the former migration machinery was removed by the compatrm001 plan`), the `execution_snapshots` retirement (`(wfaudit010)`), the Historical note about `tool_call_state` being added by a removed migration step, and the Adoption Path sentence (`established by dbmig001 was removed by the compatrm001 plan`).

## Design decisions
- State what is true now: no migration registry or version ledger; schema changes land as a new canonical DDL and the file is archived and recreated; `tool_call_state` is created by the canonical create-path DDL.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Procedure
1. Bootstrap: `There is no migration registry: a future schema change to this file lands as a new canonical DDL and the file is archived and recreated.`
2. `execution_snapshots` section: drop `(wfaudit010)`; keep `never written ... and are retired` only as far as it describes current behavior (fresh databases do not create them; a legacy database carrying the table is refused and recreated).
3. Delete the Historical note parenthetical; keep the sentence that the fingerprint compares the canonical DDL shape.
4. Adoption Path: `carries no version ledger or migration step`; drop the dbmig001 and compatrm001 clauses.

### Method
- `rg -n 'compatrm001|dbmig001|wfaudit010|former|Historical' docs/41_db/db_03_07_*.md` before and after.

### Details
- Verify the retirement statement against `scripts/db/schema_sql.py` before keeping it.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` — pass (UNK-05).

## Completion criteria
- No plan ID or `removed/former` history remains in the edited passages; current behavior is stated.

## Out of Scope
- Schema or code changes; other `db_03_*` documents.

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
- **Requirement ID**: `REQ-004` — rewrite migration-history passages as current statements
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
