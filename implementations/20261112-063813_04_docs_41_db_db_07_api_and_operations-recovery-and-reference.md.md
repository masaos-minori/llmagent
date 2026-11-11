## Goal

Replace `db_07`'s startup-consistency bullet that asserts the check is skippable and does not stop startup with a reference to `rag_05_07` for severity and startup behavior (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 96 currently reads: "At startup, a failed RAG *logical* consistency check (unrelated to physical corruption) is treated as a non-critical, skippable finding and does not stop startup (`agent/startup.py`)."
- This bullet overlaps with ADR-005's startup-check claim, which this Plan also corrects.
- `db_07` is also targeted by `plans/20261111-110144_adrrev017_docs-history-wording.md` and `plans/20261111-112439_adrrev019_docs-stale-statements.md`; this edit changes only the line-96 startup-consistency bullet.
- Gated: `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` phase all — sequence this Plan after it.

## Design decisions
- Reword the line-96 bullet to state what `db_07` owns (physical-corruption versus logical-consistency handling) and reference `rag_05_07` for severity and startup behavior, removing the assertion that the check "does not stop startup".

## Alternatives considered
- Leaving the "skippable ... does not stop startup" wording: rejected by `REQ-003`; it restates startup behavior that `rag_05_07` owns and contradicts the Fatal abort in code.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Locate the startup-consistency bullet (line 96).
2. Reword it to reference `rag_05_07` for severity and startup handling instead of asserting the check is skippable.

### Method
Evidence checked: line 96. Keep the surrounding physical-corruption context intact; only the logical-consistency startup claim changes.

### Details
- The reword states the owned behavior and points to the single policy source; it does not restate or approve the timeout/abort decision (`UNK-01`).

## Compatibility considerations
- N/A: documentation alignment only.

## Security considerations
- N/A: no behavioral change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- `db_07` line 96 no longer states the startup check never aborts or is skipped; it references `rag_05_07` for severity and startup handling (`AC-3`).

## Out of Scope
- Restating startup behavior beyond what `db_07` owns; other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md phase all - edits rag_05_07 wording it rewrites; sequence this Plan after it |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md phase all - sequence after it |

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
- **Requirement ID**: `REQ-003` (startup-consistency bullet references `rag_05_07`, no longer claims it never aborts)
- **Source issue**: issues/20261109-113123_adrrev013_rag-consistency-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-102935_adrrev013_rag-consistency-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-063813
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
