## Goal

Make the `/config` command print the resolver-derived config directory instead of the stale `_CONFIG_DIR` value. Implements `REQ-002` / AC-03.

## Scope

Modifies `scripts/agent/commands/cmd_config_display.py`: update the lazy import and usage inside `_cmd_config`.

## Assumptions

- Inside `_cmd_config`, the module currently does a lazy `from agent.config_builders import _CONFIG_DIR` and interpolates it into the printed output (verified around lines 196-205).
- The `config_builders.py` row exposes `resolved_config_dir()` as the replacement accessor.

## Design decisions

- Change the lazy import to `from agent.config_builders import resolved_config_dir` and call `resolved_config_dir()` when building the `/config` output, so the displayed path reflects the current resolver precedence.

## Alternatives considered

- Importing `resolve_config_dir` directly from `shared.runtime_paths`: rejected — the display logic belongs to the agent layer, and routing through `config_builders.resolved_config_dir()` keeps the import surface consistent with the rest of the agent.

## Implementation

### Target file

`scripts/agent/commands/cmd_config_display.py`

### Procedure

Update the lazy import and its use inside `_cmd_config` to the new accessor.

### Method

1. In `_cmd_config`, replace `from agent.config_builders import _CONFIG_DIR` with `from agent.config_builders import resolved_config_dir`.
2. Replace every `_CONFIG_DIR` reference in the display string with `resolved_config_dir()`.

### Details

- Keep the lazy import inside the function (as it is today) to avoid import-time side effects; the accessor is cheap.

## Compatibility considerations

- The `/config` output format is unchanged except the resolved path now updates correctly under a compiled binary.

## Security considerations

- N/A: display-only; no path is executed.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py` — `/config` path case passes.
- `rg "_CONFIG_DIR" scripts/` — zero references after this row.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports` clean.

## Completion criteria

- `_cmd_config` imports and calls `resolved_config_dir()`; no `_CONFIG_DIR` reference remains; the display test passes.

## Out of scope

- The accessor definition (`config_builders.py`), the resolver (`runtime_paths.py`), and the error-path row (`context.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Point `/config` display at `resolved_config_dir()` | Completed | 20261012-183345 | 20261013-100326 |  |
| 2 | Update `tests/agent/test_config_builders.py` | Completed | 20261012-183345 | 20261013-100326 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261012-183345 | 20261013-100326 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261012-183345 | 20261013-100326 | N/A |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: scripts/agent/commands/cmd_config_display.py