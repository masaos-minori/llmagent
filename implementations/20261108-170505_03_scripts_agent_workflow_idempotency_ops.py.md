## Goal
Replace the obsolete near-duplicate warning comment in `begin_stage_if_new` (L57-59) with a single-source statement: the `begin_immediate()` transaction is now the only attempts-insert path (`REQ-005`).

## Scope
**Release unit**: wfaudit009-full

- Covers Plan `plans/20261108-084010_wfaudit009_test-only-state-helpers.md` row 3 only: `scripts/agent/workflow/idempotency_ops.py` (comment-only edit).
- This is a Phase 2 (plan step 2) document: the comment becomes obsolete exactly when `start_attempt` disappears (document 01), so the two land in the same step.

## Assumptions
- The comment verified verbatim at HEAD `ad48bfa28` (L57-59): "# Not attempt_ops.start_attempt: this insert stays in the same / # begin_immediate() transaction as the processed_events check/insert, / # whereas start_attempt commits on its own. Same columns — change together."
- The semantics comment block above it (L42-46, ending with the false "removes their event IDs" bullet) is owned by `wfaudit001` (`implementations/20261108-134201_02_scripts_agent_workflow_idempotency_ops.py.md`) and lands before this document; the two regions are disjoint (L42-46 vs L57-59) and this document does not rewrite that block. After that edit the line numbers here shift; the edit is anchored by the comment's first line, not by line number.
- No caller-side changes: all `begin_stage_if_new` behavior (including the `lease_duration_sec` stamping branch, docstring paragraph L36-40 and stamping body L47-53) is untouched by this plan.

## Design decisions
- Comment replacement, not deletion (plan `REQ-005`): the transaction-scoping information (insert shares the `begin_immediate()` transaction with the `processed_events` check/insert) is still true and worth keeping; only the comparison to the deleted helper goes away.
- The replacement text deliberately never names the deleted helper, so the `REQ-001` grep (`start_attempt|count_attempts` in `scripts/` and `tests/`) stays clean after Phase 2.

## Alternatives considered
- Deleting the three comment lines outright: rejected — the begin_immediate scoping ("Same columns — change together" rationale) is the durable part of the note; the plan wording is "replace by a single-source statement".

## Implementation
### Target file
`scripts/agent/workflow/idempotency_ops.py`

### Procedure
Replace the three comment lines inside `begin_stage_if_new` with a two-line single-source statement.

### Method
Find the comment block immediately above the attempts `db.execute` INSERT (HEAD L57-59) and replace it with:

- Line 1: `# Single-source attempts insert: this begin_immediate() transaction is the`
- Line 2: `# only path that writes running attempts rows, stamped with lease columns here.`

No other lines change: the docstring, the processed_events semantics block (owned by `wfaudit001`), both INSERTs, and the returned `AttemptRecord` stay byte-identical.

### Details
- The new text must not contain the tokens `start_attempt` or `count_attempts` (acceptance grep `REQ-001`/`REQ-005`).
- `get_owner_id` and `lease_expires_from` stay imported from `agent.workflow.attempt_ops` (L9); document 01 keeps both functions.

## Compatibility considerations
- Comment-only change: no runtime, API, or test impact; existing tests touching `begin_stage_if_new` (documents 04, 07) must not assert the old comment text (none do).

## Security considerations
- None.

## Rollback considerations
- Revert restores the old comment; only meaningful together with a rollback of document 01, since the old comment references a helper that no longer exists.

## Validation plan
- Review check (plan `REQ-005` acceptance: "comment accurate"): the replacement accurately describes the surviving insert path.
- `uv run pytest tests/agent/workflow/ -q` green; REQ-001 grep shows no `start_attempt`/`count_attempts` matches in `scripts/`; lint gates per `rules/toolchain.md`.

## Completion criteria
- The obsolete comparison comment is gone; the single-source statement is present; the function body and docstring are otherwise unchanged.

## Out of Scope
- The processed_events semantics comment block (L42-46) owned by `wfaudit001`.
- Any behavior change to `begin_stage_if_new` (explicitly out of scope per the plan Reference Files row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | lands with document 01 (plan step 2) |
| 2 | Add or update tests per Validation plan | Pending | — | — | no tests for a comment-only edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | includes the REQ-001 grep |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | docs grep verified zero matches; verification-only |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261107-203222_wfaudit009_test-only-state-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084010_wfaudit009_test-only-state-helpers.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-170505
- **Related target files**: `scripts/agent/workflow/idempotency_ops.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-170505 -->
