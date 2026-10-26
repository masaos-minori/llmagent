## Goal

Use `tools/generate_reference_table.py` read-only to regenerate the EventBus reference block
(see seq 07); do not modify the tool unless a genuine defect is found that blocks
regeneration.

## Scope

- Inspect `tools/generate_reference_table.py` as the tool that produces the guarded block. No
  modification is required.

## Assumptions

- The generator is a `tools/` script, not a source/target file; this row records that it is
  used read-only.
- `--check` currently reports "No drift found" (verified this pass), so no generator defect
  blocks regeneration.

## Design decisions

- **Do not modify the tool.** It is the mechanism seq 07 uses to refresh the guarded block.
  If `--check` reported drift the generator could not reconcile, that would be a generator
  defect to fix here; none was found.

## Alternatives considered

- None; the tool is not a modification target.

## Implementation

### Target file

`tools/generate_reference_table.py` (read-only; not modified)

### Procedure

1. Confirm the generator runs cleanly:
   `uv run python tools/generate_reference_table.py --check` — exits 0 ("No drift found").
2. If a genuine defect is found that blocks regeneration (seq 07), fix it here per
   `routing.md` "Adding a new tool" and re-run `--check`; otherwise leave the tool unchanged.

### Method

Read-only use; no edits.

### Details

- If the tool were modified, it would require `ruff format`/`check`, `mypy` (explicit path),
  `bandit`, a live smoke-test, and a `TOOL_DESCRIPTIONS.md` sync per `routing.md`. None is
  needed this pass.

## Compatibility considerations

- No change; behavior unchanged.

## Security considerations

- No security impact; no change.

## Rollback considerations

- N/A: no change.

## Validation plan

- `uv run python tools/generate_reference_table.py --check` — exits 0.
- `uv run ruff format tools/generate_reference_table.py`; `uv run ruff check
  tools/generate_reference_table.py`; `uv run mypy tools/generate_reference_table.py`;
  `uv run bandit tools/generate_reference_table.py`.

## Completion criteria

- The generator runs cleanly (`--check` exits 0); no defect found; tool unchanged.

## Out of Scope

- Modifying the tool beyond confirming it runs cleanly.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Use generator read-only; confirm no defect | Pending | — | — | --check = No drift; no edit required |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus008_documentation-comment-drift-cleanup.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124800_eventbus008_documentation-comment-drift-cleanup.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-100803
- **Related target files**: `tools/generate_reference_table.py`
