## Goal
Rewrite `the db.store re-export facade was deleted (2026-11-07) and must not be reintroduced` as a current rule (`REQ-004` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers have drifted from the Plan (other Plans edited these files); locate each passage by its quoted text.
- The Import Boundaries paragraph (about line 38) is the passage; verify with `ls scripts/db/` that no `store.py` facade exists before writing the rule.

## Design decisions
- State the rule: callers import contracts and helpers from `db.store_protocols` and SQLite implementations from `db.store_impl`; there is no `db.store` re-export module.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Procedure
1. Replace the sentence with `there is no db.store re-export module; do not add one.`
2. Step 3a finding: line 30 (the `db/` layout sentence) still says the store protocols and implementations are `re-exported through `store.py``, which contradicts the rule and `scripts/db/` (no `store.py`); remove that clause in the same edit.

### Method
- Keep the link to `db_04` section 1a unchanged.

### Details
- No date or `deleted` wording remains.

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
- The passage states only the current import rule; the db consistency check passes.

## Out of Scope
- `db_04` import rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-175840 | 20261112-175840 | docs/41_db/db_01_architecture_and_schema-overview-and-config.md (3b: also removed stale store.py re-export clause, line 30) |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-175840 | 20261112-175840 | checkers and check_docs_consistency --domain db pass |

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
- **Requirement ID**: `REQ-004` — rewrite the facade-deletion note as a current rule
- **Source issue**: issues/20261109-113318_adrrev017_docs-history-wording.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-110144_adrrev017_docs-history-wording.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123928
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
