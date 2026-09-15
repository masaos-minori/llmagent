## Goal
Remove ADR-001's redundant file/class/config/test list from `## Implementation Notes`
once reconciled into `### Implementation References`, per `REQ-001` — including
correcting a nonexistent-method citation found in References during adversarial
verification.

## Scope
- In scope: reconcile `scripts/agent/workflow/idempotency_ops.py` + `begin_stage_if_new()`
  + 4 test files into References; remove the nonexistent `StateStore.request_approval()`
  citation from References; delete the Notes list; insert the one-line pointer.
- Out of scope: any other ADR-001 content (Decision, Rationale, Invariants,
  Verification prose, Review Triggers, Approval).

## Assumptions
- The one-line pointer text ("See Related Documents > Implementation References for
  the current file/symbol list.") is used verbatim, per the Plan's Assumptions.
- `StateStore.recover_stale_attempts()` (already correctly cited) and
  `get_approval_count()` (unrelated, not cited by either copy) are left untouched —
  only the nonexistent `request_approval()` citation is removed.

## Design decisions
- Reconciliation happens before deletion, in that order, so References is complete
  and correct at every intermediate state (never a moment where information exists
  in neither copy).
- The `request_approval()` removal is a References-only correction — Notes' own
  text (line 303) never cited this method, so this is not a cross-copy conflict to
  reconcile, just a pre-existing error in References to fix while it is being
  edited anyway.

## Alternatives considered
- Leave `request_approval()` in References since it's outside this issue's literal
  "duplication" framing — rejected: once Notes' list is deleted, References becomes
  the sole record; leaving a known-wrong citation there would make the ADR strictly
  worse than before this change, not better.

## Implementation
### Target file
`docs/adr/ADR-001-workflow-engine-mandatory.md`

### Procedure
1. Re-verify (idempotent recheck) current line numbers: `grep -n "^## Implementation Notes\|^### Implementation References" docs/adr/ADR-001-workflow-engine-mandatory.md` — confirm the Notes list is still at lines 302-305 and References at 367-371 before editing (content may have shifted since this procedure was generated).
2. In `### Implementation References`, add a new bullet for `scripts/agent/workflow/idempotency_ops.py` — `begin_stage_if_new()`.
3. In `### Implementation References`, add a new bullet listing all 4 test files: `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py` (or fold into the existing test-citation convention this ADR uses, if any — none currently exists here, so add as a new `テスト` — style bullet matching ADR-005/009/010's convention).
4. In `### Implementation References`, remove `StateStore.request_approval()` from the `scripts/agent/workflow/state_store.py` bullet, keeping `StateStore.recover_stale_attempts()`.
5. Delete the 4-item bulleted list from `## Implementation Notes` (実装ファイル / 主要ClassまたはFunction / 設定ファイル・設定Key / 対応するテスト).
6. In its place, insert: "See Related Documents > Implementation References for the current file/symbol list."

### Method
Use `Edit` (exact-string replacement) — one call per step 2-6 above, so each change
is independently reviewable in the diff. Re-`Read` the current section content
immediately before each `Edit` if step 1's recheck found any drift from the line
numbers recorded here.

### Details
- Do not touch the boilerplate lines following the Notes list ("この章は設計判断の
  根拠にしない。..." / "行番号は記載せず...") — these remain, now directly after
  the one-line pointer.
- Confirm `scripts/agent/workflow/idempotency_ops.py` still defines `begin_stage_if_new()`
  before adding the References bullet (re-verify via `grep`, not from memory of this
  document alone — source may have changed since this procedure was generated).

## Compatibility considerations
N/A: documentation-only change; no code, config, or test reads this ADR's Notes/
References sections programmatically.

## Security considerations
N/A: documentation-only change; no credentials or executable content involved.

## Rollback considerations
Single-file, git-tracked Markdown edit — revert via
`git checkout -- docs/adr/ADR-001-workflow-engine-mandatory.md` if validation fails
and cannot be fixed forward within `AGENTS.md` Loop Prevention's attempt bound.

## Validation plan
- Manual diff: confirm `## Implementation Notes` no longer contains the 4-item list and now reads the one-line pointer plus original boilerplate.
- Manual diff: confirm `### Implementation References` includes `idempotency_ops.py`, the 4 test files, and no longer cites `request_approval()`.
- `uv run python tools/check_docs_quality.py docs/adr/ADR-001-workflow-engine-mandatory.md` — expect zero findings.
- `uv run python tools/check_docs_structure.py docs/adr/ADR-001-workflow-engine-mandatory.md` — record the finding count before this edit and confirm no new finding after.
- `uv run python tools/check_adr_reference.py` and `uv run python tools/check_adr_invariant_matrix.py` — expect zero findings (unaffected by this change, targets `docs/adr-index.md`).

## Completion criteria
- `## Implementation Notes` contains no file/class/config/test list, only the
  one-line pointer and original boilerplate.
- `### Implementation References` contains `idempotency_ops.py`/`begin_stage_if_new()`,
  the 4 test files, and does not cite `request_approval()`.
- All Validation plan checks pass (or, for `check_docs_structure.py`, no new
  finding beyond the pre-existing baseline).

## Out of scope
- Any other section of ADR-001.
- Fixing any pre-existing, unrelated `check_docs_structure.py` finding.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-160939 | 20260915-162230 | Reconciled idempotency_ops.py+symbol+4 tests and removed nonexistent request_approval() citation via Edit; deleted Notes list; inserted pointer |
| 2 | Add or update tests per Validation plan | Completed | 20260915-162230 | 20260915-162230 | N/A: documentation-only, Validation plan is grep/tool checks, not pytest N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-162230 | 20260915-162230 | N/A: documentation-only, use this document's own Validation plan instead check_docs_quality: 0 findings; check_docs_structure: 4 pre-existing unrelated findings (missing Keywords, 3 broken links), confirmed via git diff not caused by this edit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-162230 | 20260915-162230 | N/A: this document's own target file IS the documentation being updated N/A: target file IS the documentation; no docs/00_index.md cascading row |

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
- **Requirement ID**: REQ-001 — reconcile idempotency_ops.py + tests, remove nonexistent request_approval() citation, delete Notes list
- **Source issue**: issues/done/20260914-124438_docqa02_adr-implementation-notes-file-list-duplicates-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-154020_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-160939
- **Related target files**: docs/adr/ADR-001-workflow-engine-mandatory.md