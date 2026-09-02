## Goal
Satisfy `REQ-004`: update ADR-008's Known Deviations entry for this gap to reflect
that `recover_corruption()` now distinguishes `UNKNOWN` from `CORRUPTION` (INV-17
satisfied).

## Scope
Modify exactly the Known Deviations bullet at line 435-439 (the
`recover_corruption()`/`UNKNOWN`-classification entry) in
`docs/adr/ADR-008-sqlite-4db-separation.md`. No other Known Deviations entry or
section is touched.

## Assumptions
- This row lands after seq 01-03 (the code and test changes) so the ADR describes
  actual, landed behavior rather than anticipated behavior.

## Design decisions
Follow the same "**解決済み**" (Resolved) annotation pattern already used elsewhere
in this same Known Deviations section (matching the style confirmed in the sibling
`plans/20260901-102432_plan.md`'s own ADR-004 Known Deviations edit) — cite the
Requirement IDs and the resulting behavior, not implementation-line detail.

## Alternatives considered
N/A: direct, minimal consequence of seq 01 landing — no alternative wording approach
considered.

## Implementation
### Target file
docs/adr/ADR-008-sqlite-4db-separation.md

### Procedure
Append a resolution annotation to the existing Known Deviations bullet.

### Method
1. Locate lines 435-439 (current):
   ```
   - **Known Issue**: `recover_corruption()`（`scripts/db/recovery.py`）は、Unknown分類（`DbCondition.UNKNOWN`）をCorruption分類と同一に扱い、`rag`/`session`に対しては自動的にバックアップからのリストアを試みる。これはINV-17（Unknownまたは分類不能な障害は対象DBを保持し運用者の介入を要求する）を現時点では満たしていない。
     ...
     - **Resolution Target**: `recover_corruption()`のUnknown分類分岐を、リストアを試みずに対象DBを保持し運用者介入を要求する経路へ分離する
   ```
   (read the exact full bullet, including any lines between 435 and 439, before
   editing — the Plan's evidence quotes only the first and last lines).
2. Append, immediately after the existing bullet text (before the next bullet or
   heading):
   ```
   **解決済み**: REQ-001〜REQ-003により、`recover_corruption()`に`DbCondition.UNKNOWN`
   専用の分岐を追加し、`action="unknown_preserved"`を返して対象DBを保持し運用者介入を
   要求するようになった（`_restore_from_backup()`は呼び出されない）。これにより
   INV-17を満たす。**影響**: INV-17 → 解消済み。
   ```

### Details
Do not remove the original problem-description text — per this repository's
established Known Deviations convention (confirmed by the sibling ADR-004 edits
earlier in this same session), a resolved entry keeps its original description and
appends a "解決済み" annotation, rather than deleting the historical record.

## Compatibility considerations
Documentation-only change; no code, schema, or runtime behavior affected.

## Security considerations
N/A: no security-relevant content in a Known Deviations resolution annotation.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file — should be
reverted together with seq 01-03 if those are rolled back, to avoid describing a fix
that no longer exists in code.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/adr/ADR-008-sqlite-4db-separation.md` → no new issues.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-008-sqlite-4db-separation.md` → passes.
- Manual: confirm the bullet's original problem description is still present, only annotated as resolved.

## Completion criteria
The Known Deviations bullet is annotated "解決済み", citing REQ-001 through REQ-003
and confirming INV-17 is now satisfied.

## Out of scope
`scripts/db/recovery.py` (seq 01), `tests/db/test_db_maintenance.py` (seq 02), and
`tests/integration/test_session_recovery.py` (seq 03) — each covered by its own
implementation procedure document for this same Plan.

## Documentation
This file is itself the ADR being updated; no separate `docs/00_index.md`
task-scope mapping applies.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append resolution annotation to Known Deviations bullet | Pending | — | — | Depends on seq 01-03 landing first |
| 2 | N/A: no test to add (doc-only change) | Pending | — | — | N/A |
| 3 | Run validation sequence | Pending | — | — | |
| 4 | Documentation update | Pending | — | — | N/A: this file is the documentation being updated |

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
- **Requirement ID**: REQ-004 (mark ADR-008 Known Deviations entry resolved)
- **Source issue**: `issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-111916_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-141419
- **Related target files**: `docs/adr/ADR-008-sqlite-4db-separation.md`
