## Goal

Update `tests/agent/test_config_builders.py` so the resolved config directory comes from the resolver (no stale `scripts/config`), covering the `/config` display path, the config-load error path, and the PyYAML/import check. Implements `REQ-002` / `REQ-005` / AC-03, AC-07.

## Scope

Modifies `tests/agent/test_config_builders.py`: replace any assertion on the stale `_CONFIG_DIR` with the resolver-derived directory, add the PyYAML import-check case, and keep the display/error-path assertions aligned with the new accessor.

## Assumptions

- `config_builders.py` exposes `resolved_config_dir()` (see its row); `cmd_config_display.py` imports it for the `/config` display; `context.py` uses the resolver in its error path.
- `PyYAML` becomes a declared dependency (its row), so `import yaml` resolves.

## Design decisions

- Assert that the displayed/error path equals `resolved_config_dir()` (or `<LLMAGENT_CONFIG_DIR>/...` when the env is set) rather than a hardcoded `scripts/config`.
- Add a case asserting `import yaml` succeeds (REQ-005 import check).

## Alternatives considered

- Rewriting the suite: rejected — only the directory source and one import check change.

## Implementation

### Target file

`tests/agent/test_config_builders.py`

### Procedure

Update the directory-source assertions and add the PyYAML import check.

### Method

1. Replace any reference to the stale `_CONFIG_DIR`/`scripts/config` with `resolved_config_dir()` (or the resolver-derived value under a set `LLMAGENT_CONFIG_DIR`).
2. Add a case asserting `import yaml` resolves (REQ-005).
3. Keep the `/config` display and config-load error-path assertions, pointing them at the resolver-derived directory.

### Details

- If the suite previously imported `_CONFIG_DIR`, remove that import (it no longer exists) and use `resolved_config_dir()` instead.

## Compatibility considerations

- Preserve existing cases that do not depend on the stale path.

## Security considerations

- N/A: directory selection and import check only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py` — resolver-derived display/error paths pass; `import yaml` resolves.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` clean.

## Completion criteria

- `test_config_builders.py` uses `resolved_config_dir()`, has no reference to the stale `_CONFIG_DIR`, asserts `import yaml`, and passes.

## Out of scope

- The resolver (`scripts/shared/runtime_paths.py`), the `config_builders.py` accessor, the `cmd_config_display.py` import, and the `context.py` error path are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace stale `_CONFIG_DIR` assertions with the resolver-derived directory | Pending | — | — | |
| 2 | Add the PyYAML import-check case | Pending | — | — | REQ-005 |
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
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: tests/agent/test_config_builders.py
