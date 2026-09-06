## Goal
Record `SHARED-001`'s confirmed absence as policy-compliant; add a precise test-name
citation to `SHARED-002`; correct `SHARED-003`'s stale "no runbook" framing and mark
it `resolved`; narrow `NC-021` to the one genuinely open implementation-mapping
question this cycle confirmed (REQ-001, REQ-002, REQ-003, REQ-004, REQ-007).

## Scope
- In scope: the `SHARED-002` entry (currently lines 386-403), `SHARED-003` entry
  (405-422), and `NC-021` entry (783-799) — line numbers re-confirmed this cycle
  (2026-09-06), NC-021's shifted ~40 lines from the Plan's citation (743-761) due to
  unrelated intervening edits this session added (new MCP-001/MCP-002 entries etc.) —
  re-locate by heading (`#### NC-021`) at implementation time, not by these line
  numbers.
- Out of scope: any other entry in this document (CI-001 through CI-015, RAG-003
  through RAG-005, DESIGN-1/2, EVENTBUS-001 through EVENTBUS-008, MCP-001/MCP-002);
  Part 2's structural sections (Purpose, Inventory Entry Fields, Status Values,
  Priority Values, Extraction Process).

## Assumptions
- `SHARED-002`'s `Observed Implementation`/`Recommended Action` text is already
  substantively accurate (confirmed this cycle: it already states backup
  validation/atomic staging "were already implemented" and the post-restore
  re-verification "was added... (Verified by test)") — REQ-002's actual remaining
  work is narrower than a full rewrite: name the specific test
  (`test_recover_restore_verify_failed`) explicitly where the entry currently just
  says "(Verified by test)" without naming which test, and confirm the
  backup-validation/atomic-staging claims (which no dedicated test exercises
  end-to-end per Unknowns UNK-01) use `Explicit in code` instead of implying the same
  "(Verified by test)" label covers them too.

## Design decisions
- For `NC-021`, narrow rather than remove: this cycle's direct read of
  `scripts/db/recovery.py` (lines 18-39, 200-215) found `DbCondition.INVALID_FORMAT`
  is defined (line 25) and dispatched-on in `recover_corruption()`'s condition
  handling (line 209, grouped with `LOCK_CONTENTION`/`PERMISSION_FAILURE`), but
  `_classify_error()` (lines 29-39) never actually returns it — no code path
  produces `INVALID_FORMAT`, making that branch currently unreachable. This is exactly
  the kind of "genuinely unresolved implementation-mapping question" REQ-004 asks to
  preserve if found, rather than closing `NC-021` outright on the assumption that the
  six-state model is already fully realized.
- Keep `SHARED-001` as a documented absence (a short note, not a heading) rather than
  fabricating a `#### SHARED-001` entry — per the Plan's Design section and the
  Current-Specification-Only Policy, its absence IS the correct end state.

## Alternatives considered
- Remove `NC-021` entirely on the grounds that `DbCondition`/`_classify_error()`
  already exist: rejected — Design decisions above found a concrete, still-open gap
  (`INVALID_FORMAT` unreachable) that would be silently lost if the entry were
  deleted rather than narrowed.
- Rewrite `SHARED-002` from scratch: rejected — its existing text is already close to
  accurate (Assumptions above); a full rewrite risks losing accurate detail already
  present, when only the test-name citation and evidence-label precision need
  correcting.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Add a brief note near where `SHARED-001` would alphabetically/numerically fall (or
   at the top of the Known Issues section) stating it was fully resolved and its
   content transferred; its absence from the active list is the correct,
   policy-compliant state — do not create a `#### SHARED-001` heading.
2. In `SHARED-002`'s `Observed Implementation` bullet, replace the generic "(Verified
   by test)" with: backup validation and atomic temp-file staging are `Explicit in
   code` (no dedicated test exercises them end-to-end, per Unknowns UNK-01); the
   post-restore re-verification returning `action="restore_verify_failed"` is
   `Verified by test` — name `test_recover_restore_verify_failed` explicitly.
3. Rewrite `SHARED-003`'s `Current Description`/`Impact`/`Recommended Action` to state
   the operator runbook already exists (`docs/05_agent_10_01_operations-and-observability-startup-and-health.md`
   lines 88-136, per Reference Files) and already uses `rotate_all_dbs()`'s backups;
   change `Status` from `deferred` to `resolved`.
4. Rewrite `NC-021`'s `Evidence`/`Question`/`Resolution Target` to state: the
   structured six-state `DbCondition` classification is implemented
   (`scripts/db/recovery.py`), but `INVALID_FORMAT` is defined and dispatched-on
   without any code path that produces it — narrow the `Question` to "should
   `_classify_error()` be extended to actually classify a case as `INVALID_FORMAT`,
   or should the enum value and its dispatch branch be removed as dead?" Keep
   `Status: open`, update `Last Reviewed` to this cycle's date.
5. Confirm no entry touched by steps 1-4 now has more than one current `Status` value
   (REQ-007) and that every `Verified by test` claim in them names an actual,
   currently-passing test (re-run `uv run pytest tests/db/test_db_recovery.py -v`
   before finalizing, per Tests).

### Method
Confirmed this cycle (2026-09-06) via direct read: `SHARED-002` (lines 386-403),
`SHARED-003` (405-422), `NC-021` (783-799, re-located from the Plan's stale 743-761
citation). `DbCondition` enum (`scripts/db/recovery.py:18-26`) has exactly 6 values;
`_classify_error()` (lines 29-39) returns only `LOCK_CONTENTION`,
`PERMISSION_FAILURE`, `CORRUPTION`, or `UNKNOWN` — never `HEALTHY` (returned
elsewhere, by `_run_integrity_check()`'s own success path) or `INVALID_FORMAT`;
`recover_corruption()` (line 209) dispatches on `INVALID_FORMAT` as if it could occur.

### Details
No change to any other entry in this document.

## Compatibility considerations
N/A: documentation-only.

## Security considerations
N/A.

## Rollback considerations
Revert via `git checkout` on this file alone if
`check_docs_quality.py`/`check_needs_confirmation_inventory.py` flag an issue after
the edit.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md`
- `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md`
- `uv run python tools/check_needs_confirmation_inventory.py` — confirm `NC-021`'s
  narrowed text does not introduce a new inventory warning.
- `uv run pytest tests/db/test_db_recovery.py -v` — confirm
  `test_recover_restore_verify_failed` (and the full 13-test file) still passes
  before citing it by name.

## Completion criteria
- `SHARED-001` is documented as intentionally absent, no new heading created.
- `SHARED-002` names `test_recover_restore_verify_failed` explicitly and uses
  `Explicit in code` for the untested claims.
- `SHARED-003`'s `Status` is `resolved` and its text states the runbook exists.
- `NC-021` is narrowed to the `INVALID_FORMAT`-unreachable question, `Status`
  remains `open`.
- No touched entry has conflicting `Status` values.

## Out of scope
- `docs/90_shared_05_04_db_api_and_operations-recovery-and-reference.md` — tracked
  in seq 02.
- `docs/adr/ADR-008-sqlite-4db-separation.md` — tracked in seq 03.
- Any other entry in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | SHARED-001 absence note added; SHARED-002 Observed Implementation updated with explicit test name and evidence labels; SHARED-003 status changed to resolved with runbook citation; NC-021 narrowed to INVALID_FORMAT-unreachable question |
| 2 | Add or update tests per Validation plan | Done | — | — | No new tests needed; existing `test_recover_restore_verify_failed` passes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | check_docs_quality.py passed; check_docs_structure.py reports pre-existing file-size warning; all 17 db_recovery tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | All four entries updated as specified |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-007
- **Source issue**: issues/20260903-110307_h0709_reconcile-shared-001-002-003-and-nc-021.md
- **Source plan**: plans/20260905-164204_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-145042
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
