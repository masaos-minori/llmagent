## Goal

Remove the stale `_CONFIG_DIR` (which resolves to a nonexistent `scripts/config`) and expose the resolved config directory from the shared resolver, so the `/config` display path is correct under both `uv run` and a Nuitka binary. Implements `REQ-002` / AC-03.

## Scope

Modifies `scripts/agent/config_builders.py`: delete the `_CONFIG_DIR` definition and add a public accessor that callers import. The consuming import lives in `cmd_config_display.py` (its own row).

## Assumptions

- `_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"` exists at line 59 and resolves to `scripts/config`, which does not exist (`ls scripts/config` fails).
- `scripts/agent/commands/cmd_config_display.py` imports `_CONFIG_DIR` from this module inside `_cmd_config` (a lazy import); that import is updated in the `cmd_config_display.py` row.

## Design decisions

- Replace the module-level `_CONFIG_DIR` constant with a new public function (new) `resolved_config_dir() -> Path` that returns `resolve_config_dir()`. A function (not a module-level value) is used so the env-var and compiled branches are evaluated at call time rather than at import.
- Import `resolve_config_dir` from `shared.runtime_paths`.

## Alternatives considered

- Keeping `_CONFIG_DIR` and just fixing its traversal: rejected — it still hard-codes `__file__` and cannot express the compiled-adjacent branch; the resolver is the single source of truth.

## Implementation

### Target file

`scripts/agent/config_builders.py`

### Procedure

Delete the stale `_CONFIG_DIR` and expose the resolver result via a public accessor.

### Method

1. Add `from shared.runtime_paths import resolve_config_dir` to the imports.
2. Delete the line `_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"`.
3. Add (new) `def resolved_config_dir() -> Path: return resolve_config_dir()` near the removed definition (or alongside other exported config helpers).
4. Remove the `Path` import if it becomes unreferenced elsewhere in the file.

### Details

- The accessor returns the same `Path` the old `_CONFIG_DIR` would have produced under `uv run` (repo-root `config/`), so existing behavior is preserved while the compiled branch now works.
- `resolved_config_dir()` is the symbol the `cmd_config_display.py` row will import; keep the name stable across both rows.

## Compatibility considerations

- Any in-module references to `_CONFIG_DIR` must be rewritten to call `resolved_config_dir()`; grep for `_CONFIG_DIR` in `scripts/` before finishing to confirm none remain.

## Security considerations

- N/A: directory selection only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py` — resolved-dir display and no-stale-`scripts/config` cases pass.
- `rg "_CONFIG_DIR" scripts/` — zero remaining references.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports` clean.

## Completion criteria

- `_CONFIG_DIR` is deleted, `resolved_config_dir()` is exposed and returns the resolver's directory, no `_CONFIG_DIR` reference remains, and `test_config_builders.py` passes.

## Out of scope

- The `cmd_config_display.py` import update (separate row), the resolver (`runtime_paths.py`), and the error-path row (`context.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `_CONFIG_DIR`, expose `resolved_config_dir()` | Pending | — | — | |
| 2 | Update `tests/agent/test_config_builders.py` | Pending | — | — | |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: scripts/agent/config_builders.py
