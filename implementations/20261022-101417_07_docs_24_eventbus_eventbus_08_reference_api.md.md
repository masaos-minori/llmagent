## Goal
Fix the `offsets.py` responsibility sentence and regenerate the auto-generated reference block so the `offset_migrator` row disappears (REQ-005).

## Scope
- The sentence in "Module Responsibilities" naming the one-time startup migration, and the guarded block "Module Class/Function Reference (auto-generated)".

## Assumptions
- The block is produced by `tools/generate_reference_table.py` for the EventBus domain; hand edits inside the guard are overwritten and `--check` fails on drift (verified in the tool and routing table).
- After the code change `offsets.py` has no production caller; its helpers remain pending a separate decision.

## Design decisions
- New sentence: `offsets.py` is a file-based offset helper not used by the service; live ACK and subscribe paths use the `consumer_offsets` table.
- Regenerate the block with the repository tool; do not edit it by hand.

## Alternatives considered
N/A: generator-driven change.

## Implementation
### Target file
`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure
1. Edit the `offsets.py` sentence as described (after the source changes are applied).
2. Run `uv run python tools/generate_reference_table.py --type eventbus` to refresh the block, then `uv run python tools/generate_reference_table.py --check`.

### Method
- Apply after the code procedures so the generator sees the final source.
- Review the diff: only the `offset_migrator` row (and, if the facade lists it, the `db.py` entry) should disappear.

### Details
- Do not edit lines inside the AUTO-GENERATED guard manually.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The sentence is accurate, the generated block has no `offset_migrator` row, and `--check` passes.

## Out of Scope
- Other sections and the generator itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the responsibility sentence | Pending | — | — | |
| 2 | Regenerate the reference block and run `--check` | Pending | — | — | |
| 3 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (fix the sentence and regenerate the block)
- **Source issue**: `issues/20261021-102244_rmoffimp_remove-the-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101417
- **Related target files**: docs/24_eventbus/eventbus_08_reference_api.md
