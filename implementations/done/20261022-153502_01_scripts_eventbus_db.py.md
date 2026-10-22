## Goal

Remove "offset migration" from the first-line module docstring of `scripts/eventbus/db.py`, which names a layer that no longer exists, leaving only the connection, event, delivery, and DLQ layers (REQ-001; AC-1, AC-3).

## Scope

- Modify `scripts/eventbus/db.py` line 1 only (docstring text).
- Keep the repository's "path — description" first-line format and the facade's re-export behavior unchanged.

## Assumptions

- The facade still re-exports the connection, event, delivery, and DLQ layers; only the "offset migration" mention is stale.
- The README schema-layer line should mirror the wording `scripts/eventbus/schema.py` already uses for itself.

## Design decisions

- Drop "offset migration" from the parenthetical layer list rather than rewording it to past tense: the layer was removed (commit `31f8c3be9`), so any description would name code that is not there.
- Leave the rest of the docstring and every other line untouched.

## Alternatives considered

- Reword the docstring into a fuller rewrite of the layer description — rejected: out of scope; only the stale token must be removed.

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

1. Edit line 1 to remove "offset migration" from the parenthetical layer list.
2. Run the docstring checker, ruff, mypy, and the EventBus import test.

### Method

Replace line 1:

> `"""scripts/eventbus/db.py — Re-export facade over the eventbus layer modules (connection, event, delivery, DLQ, offset migration)."""`

with:

> `"""scripts/eventbus/db.py — Re-export facade over the eventbus layer modules (connection, event, delivery, DLQ)."""`

### Details

- Evidence in-file: line 1 currently reads "Re-export facade over the eventbus layer modules (connection, event, delivery, DLQ, offset migration)."
- REQ-001 requires the connection, event, delivery, and DLQ layers only.
- The change is text only; the module still imports and re-exports identically.

## Compatibility considerations

N/A: documentation-only change; no runtime contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is described here.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/db.py` | Static + import | `uv run python tools/check_docstrings.py`; `uv run ruff check scripts/`; `uv run mypy --no-namespace-packages scripts/`; `uv run pytest tests/eventbus -q` | No new violation; tests pass |
| AC-1 check | rg | `rg -i "offset migration" scripts/eventbus` | No match |

## Completion criteria

Line 1 lists only the connection, event, delivery, and DLQ layers, `rg -i "offset migration" scripts/eventbus` returns no match, and `check_docstrings.py`, `ruff check scripts/`, `mypy --no-namespace-packages scripts/`, and `pytest tests/eventbus -q` all pass.

## Out of Scope

- Editing any other line of `db.py` or any other module.
- Any README change (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove "offset migration" from the `db.py` first-line docstring | Completed | 2026-10-22 | 2026-10-22 | |
| 3 | Run the validation sequence (`check_docstrings.py`, `ruff`, `mypy`, EventBus tests) | Completed | 2026-10-22 | 2026-10-22 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-22 | 2026-10-22 | |

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
- **Requirement ID**: `REQ-001` — update the `db.py` docstring to name only the layers that exist
- **Source issue**: `issues/20261022-124204_ebdocwording_align-eventbus-facade-wording.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130514_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-153502
- **Related target files**: `scripts/eventbus/db.py`
