# Reduce implementation-derived detail in docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`: keep `recover_corruption`'s scope limitation and known limitations; remove code examples and dataclass definitions.

## Reason for Change
This chapter is the canonical source for recovery/recreation/verification (per `memo-doc-shared-review.md` §「章間の正本ルール」: recovery / recreation / verification = `90_shared_05_04_db_api_and_operations-recovery-and-reference`). The scope limitation (`recover_corruption` for rag/session only) and known limitations (workflow/eventbus path mismatch, physical-corruption exception propagation) are operationally critical during an actual incident and must remain explicit and precise.

## Implementation Intent
Keep this chapter focused on `recover_corruption`'s intended scope, the known limitation when workflow/eventbus is passed, the known issue of `DatabaseError` propagating on physical corruption, and that DB recreation does not migrate existing data.

## Target Files or Areas
`docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md`

## Required Changes
- Keep: that `recover_corruption`'s target should be limited to rag/session, the known limitation that passing workflow/eventbus causes a mismatch between the displayed path and the actual connection, the known issue that a `DatabaseError` propagates on physical corruption, that DB recreation does not migrate data, that archival is required before recreation, that schema initialization is idempotent but does not convert existing data, that the verification plan is kept as a high-level quality gate.
- Remove or compress: `recover_corruption`'s call-site code example, the `RecoveryResult` dataclass definition, a full error-behavior correspondence table, shell-command detail for the DB-recreation procedure, a test-command list, an AI-reference table.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No call-site code example, dataclass definition, or shell-command detail remains.
- The `recover_corruption` scope limitation and the physical-corruption-exception-propagation known issue remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the scope-limitation and known-issue statements were not weakened — an operator following this during an actual incident depends on them being accurate. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but is incident-recovery-relevant documentation — treat removal decisions conservatively. Coordinate with `docs/90_shared_90_inconsistencies_and_known_issues.md`'s cleanup issue (SHARED-001) to avoid duplicating the same known issue in both places.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/db/` (including `recovery.py`).
- `deploy/init_db.sh` / `deploy/setup_services.sh` themselves (code/scripts, not documentation).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_05_04_db_api_and_operations-recovery-and-reference」. Do not edit code. Cross-reference `docs/90_shared_90_inconsistencies_and_known_issues.md` (SHARED-001) rather than duplicating the corruption-exception known issue. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_05_04_db_api_and_operations-recovery-and-reference」
- Generated at: 2026-08-05
