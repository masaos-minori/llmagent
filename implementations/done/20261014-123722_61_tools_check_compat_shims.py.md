## Goal

Removed-pattern checker: Add `COMPAT_PATTERNS` entries for the removed code identifiers and the `/approve` and `/reject` command forms (REQ-007: reintroduction guard).

## Scope

- Add `COMPAT_PATTERNS` entries for the removed code identifiers and the `/approve` and `/reject` command forms; do not register `require_approval`, `approvals`, `pending_approval`, `ApprovalDecisionType`, or "approval gate"

## Assumptions

- Plan `plans/20261014-114443_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Apply only after the repository owner's decision (Plan Step 1) is recorded, together with every other procedure of this plan (Steps 2-11) as one commit unit.
- Line numbers come from the Plan and may shift; locate edits by symbol, test name, or section.

## Design decisions

- Register only identifiers that no file will legitimately keep.
- Apply after every removal procedure so the guard never fires on a half-removed tree.

## Alternatives considered

N/A: the table choice is decided in the Plan Assumptions

## Implementation

### Target file

`tools/check_compat_shims.py`

### Procedure

Add `COMPAT_PATTERNS` entries for the removed code identifiers and the `/approve` and `/reject` command forms; do not register `require_approval`, `approvals`, `pending_approval`, `ApprovalDecisionType`, or "approval gate".

### Method

Evidence recorded in the Plan: `check_compat_shims.py` `COMPAT_PATTERNS` (line 24) holds removed-command entries (`/note`, `/db`, `/mdq` at line 46); `DEFAULT_ALLOWLIST` at line 103; CI runs the default check. Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- Add these COMPAT_PATTERNS entries next to the other removed-command entries, each keyed by a short description. Identifiers use word boundaries: approval_ops, request_approval, _gate_approval, find_latest_pending_approval, _recover_pending_approvals, WorkflowPendingApprovalError, ApprovalRecord, pending_approval_id, pending_approval_task_id, ApprovalRecovery, startup_approval_recovery, approval_requested, approval_pending. Commands: the /approve and /reject forms with the same lookbehind and lookahead as the /mdq entry.
- Do not register require_approval, approvals, pending_approval, ApprovalDecisionType, or the phrase approval gate; they stay legitimately (loader rejection, INV-10, migration SQL, tool-level code, ADR rationale).
- Apply last, after all removals; do not add any DEFAULT_ALLOWLIST entry (allowlisting disables every check for that file).

## Compatibility considerations

Adds a default-on CI check for removed names.

## Security considerations

N/A: the pattern only reads text.

## Rollback considerations

N/A: revert the commit; the whole plan lands as one commit unit.

## Validation plan

- `uv run ruff check tools/check_compat_shims.py` and `uv run mypy tools/check_compat_shims.py` are clean.
- `uv run python tools/check_compat_shims.py` reports no finding.
- `uv run python tools/check_compat_shims.py` reports no finding after all other procedures.

## Completion criteria

- The entries exist, match their names with word boundaries, and the default checker is clean.

## Out of scope

- Tool-level approval (the keep list), the MDQ and eventbus areas, and any file outside this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the edit | Completed | 20261014-142001 | 20261014-142001 |  |
| 2 | Run the tests that cover this file | Completed | 20261014-142001 | 20261014-142001 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-142001 | 20261014-142001 |  |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261014-112913_appr001_remove-the-post-execution-approval-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-114443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-123722
- **Related target files**: tools/check_compat_shims.py