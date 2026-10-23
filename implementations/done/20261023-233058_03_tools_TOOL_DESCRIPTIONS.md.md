## Goal

Document the new `close-batch` subcommand in the `### manage_workitem_stage.py subcommands` reference of `tools/TOOL_DESCRIPTIONS.md`, completing the subcommand-level description. (`REQ-008`)

## Scope

- **In-Scope**: add a `close-batch` subcommand reference under the existing `### manage_workitem_stage.py subcommands` section of `tools/TOOL_DESCRIPTIONS.md` only.
- **Out-of-Scope**: implementing the `close-batch` subcommand (seq 01), adding tests (seq 02), or referencing it from `skills/code-implementation/workflow.md` (seq 04).

## Assumptions

- `manage_workitem_stage.py` already has a top-level row in the "Work Items" table (line ~153) that defers to "the subcommand reference below"; the `close-batch` entry belongs in that subcommand reference, not as a new top-level `tools/` row.
- `check_tool_descriptions_sync.py` gates at the file level: it requires each `tools/*.py` file to appear as a backticked `.py` path in `TOOL_DESCRIPTIONS.md`. `manage_workitem_stage.py` is already documented there, so the checker passes whether or not the `close-batch` subcommand is described; this change adds subcommand-level detail for completeness rather than satisfying a gate.

## Design decisions

- **Add one bullet in the "Archive moves:" group.** Place the `close-batch` bullet immediately after the `close-issue`, `close-plan`, `close-implementation` bullet so the archive-move family stays grouped, mirroring how the existing subcommands are described.

## Alternatives considered

- Adding a new top-level `tools/` row for `close-batch`: rejected — it is a subcommand of an already-documented tool, and the tool's own row already defers to the subcommand reference.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md` (modify)

### Procedure

Add a `close-batch` bullet to the "Archive moves:" list under `### manage_workitem_stage.py subcommands`, right after the `close-issue`, `close-plan`, `close-implementation` bullet.

### Method

1. Locate the `### manage_workitem_stage.py subcommands` section and its first bullet listing `close-issue`, `close-plan`, `close-implementation`.
2. Insert a new bullet describing `close-batch`: it archives every procedure of a batch (identified by a plan path or a shared timestamp prefix) and marks the owning plan's `### Execution Status` rows `Completed`, reusing the `close-*` archive move; it carries `--dry-run` and `--stage-only`, refuses when any procedure still has a `Pending` row, and is a no-op/refusal on a second run.
3. Keep the description at the same level of detail as the neighboring bullets (what it does + the key guards/flags), without restating the full `move_to_done()` precondition block already documented above.

### Details

- Reference the atomic `Pending` pre-check and the `YYYYMMDD-HHMMSS` stamping so the description matches the implemented behavior (seq 01).
- Note `--stage-only` is inherited from the `close-*` family rather than re-described.
- After editing, run `uv run python tools/check_tool_descriptions_sync.py` to confirm the tool is fully registered.

## Compatibility considerations

Docs-only, additive bullet. No existing description is altered, so no drift in the documented behavior of the other subcommands.

## Security considerations

N/A: documentation change only.

## Rollback considerations

Revert the commit that adds the bullet, or delete the added line. Single-line, additive change.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` passes after the edit.
- `uv run python tools/check_workitem_structure.py` passes on this generated procedure document.

## Completion criteria

- `close-batch` appears in the `### manage_workitem_stage.py subcommands` reference with its archive-and-mark behavior, `--dry-run`/`--stage-only`, and the `Pending` refusal.
- `check_tool_descriptions_sync.py` passes.

## Out of Scope

Implementing the `close-batch` subcommand, its tests, and the `skills/code-implementation/workflow.md` reference pointer.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261024-014229 | 20261024-014229 | REQ-008; tools/TOOL_DESCRIPTIONS.md |
| 2 | Add or update tests per Validation plan | Completed | 20261024-014229 | 20261024-014229 | N/A: docs-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261024-014229 | 20261024-014229 | check_tool_descriptions_sync.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261024-014229 | 20261024-014229 | this change |

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
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`