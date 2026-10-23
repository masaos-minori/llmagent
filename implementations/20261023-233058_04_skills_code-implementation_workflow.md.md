## Goal

Reference the new `close-batch` subcommand in `skills/code-implementation/workflow.md`'s final archival step, so the workflow points implementers at the batch entry point for closing a whole batch of procedures instead of one `close-implementation` per file. (`REQ-008`)

## Scope

- **In-Scope**: add a pointer to `close-batch` in the archival step of `skills/code-implementation/workflow.md` only.
- **Out-of-Scope**: implementing the `close-batch` subcommand (seq 01), adding tests (seq 02), or registering the tool in `tools/TOOL_DESCRIPTIONS.md` (seq 03).

## Assumptions

- The archival step currently names `tools/manage_workitem_stage.py close-implementation` per file (lines 24, 33, 141, 397); adding a `close-batch` pointer there is the intended, minimal change.
- `check_skills_references.py` validates that the skill's tool references remain consistent; the added reference must use the same naming convention as the existing `close-implementation` references.

## Design decisions

- **Add one bullet adjacent to the per-file `close-implementation` guidance.** Place it right after the `--stage-only` bullet of the archival step (around line 412), so the batch entry point sits alongside — not replacing — the per-file command it complements.

## Alternatives considered

- Adding a whole new subsection for `close-batch`: rejected — the archival step already has the right home; a single bullet keeps the reference discoverable without restructuring the step.

## Implementation

### Target file

`skills/code-implementation/workflow.md` (modify)

### Procedure

Add a `close-batch` pointer bullet in the final archival step, after the `--stage-only` bullet (line ~412) and before the direct-command fallback (line ~413).

### Method

1. Locate the archival step's `close-implementation` guidance block (the bullet beginning "Prefer `uv run python tools/manage_workitem_stage.py close-implementation`", line 397, through the `--stage-only` bullet at line 405-412).
2. Insert a new bullet after the `--stage-only` bullet stating that when closing an entire batch of procedures that share one plan (a shared timestamp prefix across `implementations/<prefix>_NN_*.md`), prefer `uv run python tools/manage_workitem_stage.py close-batch <batch-id>` over issuing one `close-implementation` per file — it archives every procedure of the batch and marks the owning plan's `### Execution Status` rows `Completed` in one step, refusing if any procedure still has a `Pending` row.
3. Keep the reference to the same detail level as the neighboring bullets and cite `tools/TOOL_DESCRIPTIONS.md` for usage, matching the existing reference style.

### Details

- Use the exact subcommand spelling `close-batch` and the same backtick/code formatting as the surrounding `close-implementation` references so `check_skills_references.py` sees a consistent reference.
- Do not remove or alter the per-file `close-implementation` guidance; the batch command complements it for the multi-file case.
- After editing, run `uv run python tools/check_skills_references.py` to confirm the reference is valid.

## Compatibility considerations

Docs-only, additive bullet. No existing workflow instruction is altered, so the per-file `close-implementation` guidance remains intact.

## Security considerations

N/A: documentation change only.

## Rollback considerations

Revert the commit that adds the bullet, or delete the added lines. Single-bullet, additive change.

## Validation plan

- `uv run python tools/check_skills_references.py` passes after the edit.
- `uv run python tools/check_workitem_structure.py` passes on this generated procedure document.

## Completion criteria

- The archival step references `close-batch` with its batch-archive-and-mark behavior and points to `tools/TOOL_DESCRIPTIONS.md` for usage.
- `check_skills_references.py` passes.

## Out of Scope

Implementing the `close-batch` subcommand, its tests, and the `tools/TOOL_DESCRIPTIONS.md` registration row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-008; skills/code-implementation/workflow.md |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: docs-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | check_skills_references.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this change |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261023-173429_workitem001_single-command-to-close-an-executed-implementation-batch-and-its-plan-status.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-222901_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-233058
- **Related target files**: `skills/code-implementation/workflow.md`
