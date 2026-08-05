# Reduce implementation-derived detail in docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`: keep the STRICT/BEST_EFFORT operational judgment and WAL-checkpoint/VACUUM/purge/prune cautions; remove full function signatures and dataclass definitions.

## Reason for Change
This chapter is the canonical source for maintenance/rotation/consistency operations (per `memo-doc-shared-review.md` §「章間の正本ルール」: maintenance / rotation / consistency = `90_shared_05_03_db_api_and_operations-maintenance-and-rotation`). The requirement to always check `result.success` under BEST_EFFORT is a correctness-critical operational rule that silent-failure risk depends on, and must not be diluted.

## Implementation Intent
Keep this chapter focused on the operational purpose of maintenance functions, the STRICT/BEST_EFFORT distinction, WAL-checkpoint/VACUUM/purge/prune cautions, and that RAG consistency check is read-only (does not repair).

## Target Files or Areas
`docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`

## Required Changes
- Keep: the operational purpose of maintenance functions, the meaning of STRICT vs. BEST_EFFORT, that `result.success` must always be checked under BEST_EFFORT, operational cautions for WAL checkpoint/VACUUM/purge/prune, that DB rotation is for backup/archival purposes, that the SQLite online backup API preserves WAL consistency, that RAG consistency check is read-only and does not repair, operational judgment when FTS/vec inconsistency is found, that `embed_failed` is caller-supplied information rather than auto-detected.
- Remove or compress: full maintenance-function signatures, the `MaintenanceResult` dataclass definition, verbatim processing descriptions of purge/prune, a rotation-function list, the full field list of `RagConsistencyReport`, usage code examples.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No full function signature or dataclass definition remains.
- The BEST_EFFORT-must-check-result.success rule and the RAG-consistency-check-is-read-only fact remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the BEST_EFFORT result-checking requirement was not weakened — silent failure risk if dropped. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches operational-safety-relevant documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/db/` (including `maintenance.py`, `rotation.py`, `rag_consistency.py`).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_05_03_db_api_and_operations-maintenance-and-rotation」. Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_05_03_db_api_and_operations-maintenance-and-rotation」
- Generated at: 2026-08-05
