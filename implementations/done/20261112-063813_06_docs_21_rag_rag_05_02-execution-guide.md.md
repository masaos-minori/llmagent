## Goal

Standardize `rag_05_02`'s `orphan_vec_count > 0` remediation on `rebuild_vec`, matching `rag_05_07` (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 72 currently reads: "`orphan_vec_count > 0` indicates a failure in the vec trigger. This can be fixed by re-running `ingester.py --force` for the affected URLs."
- This row was missing from the issue's original target list and was discovered during verification.
- Gate resolved 2026-11-12: the identity-gate removal landed (`b217f999b`); the frozen rmcompat001 Plan (`plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md`) lists `rag_05_07` as a reference file only, not a target; `tools/plan_dependency_order.py` reports this Plan Ready with no gate.

## Design decisions
- Replace "re-running `ingester.py --force`" with `rebuild_vec` (run `/session rag-rebuild-vec`) for the `orphan_vec_count > 0` finding.

## Alternatives considered
- Leaving `ingester.py --force`: rejected by `REQ-002`; `rag_05_02` must agree with the single policy source.

## Implementation
### Target file
`docs/21_rag/rag_05_02-execution-guide.md`

### Procedure
1. Locate the `orphan_vec_count > 0` note (line 72).
2. Replace the `ingester.py --force` remediation with `rebuild_vec`.

### Method
Evidence checked: line 72. Leave the surrounding read-only-function notes intact.

### Details
- No functional or severity change; only the remediation wording.

## Compatibility considerations
- N/A: documentation alignment only.

## Security considerations
- N/A: no behavioral change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain rag` — pass.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- `rag_05_02` gives `rebuild_vec` for `orphan_vec_count > 0` and no longer offers `ingester.py --force` (`AC-2`).

## Out of Scope
- Changing the check's read-only behavior; other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-12 | 2026-11-12 | Gate resolved 2026-11-12 (see Blocker Log) implemented 2026-11-12 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-12 | 2026-11-12 | Gate resolved 2026-11-12 (see Blocker Log) implemented 2026-11-12 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | rmcompat001 phase-all gate (`rag_05_07` startup-paragraph rewrite) | Yes | 2026-11-12 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (`orphan_vec_count > 0` → `rebuild_vec`)
- **Source issue**: issues/20261109-113123_adrrev013_rag-consistency-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-102935_adrrev013_rag-consistency-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-063813
- **Related target files**: `docs/21_rag/rag_05_02-execution-guide.md`
