## Goal

Make `ConfigLoader.__init__` obtain its default config directory from the shared resolver instead of a `__file__`-based computation that breaks under Nuitka `--onefile`. Implements `REQ-001` / AC-01.

## Scope

Modifies one method (`ConfigLoader.__init__`) in `scripts/shared/config_loader.py`. The ~23 `ConfigLoader()` call sites across `scripts/` are unaffected in their call syntax; they inherit the resolver via the default branch.

## Assumptions

- `ConfigLoader.__init__` currently computes `repo_root = Path(__file__).resolve().parent.parent.parent` and sets `self._config_dir = config_dir or repo_root / "config"` (verified at lines 74-75).
- The explicit `config_dir` argument must remain the highest-priority source (AC-01).

## Design decisions

- Replace the inline `repo_root / "config"` with `resolve_config_dir(config_dir)` so the explicit argument, the `LLMAGENT_CONFIG_DIR` env var, the compiled-adjacent branch, and the legacy fallback all flow through one function.
- Keep the `config_dir` parameter first and truthy-checked so `ConfigLoader(config_dir=...)` still wins.

## Alternatives considered

- Leaving the inline computation and only special-casing the compiled case here: rejected — the same `__file__` bug exists in five other modules, and the resolver must be the single source of truth (see `runtime_paths.py`).

## Implementation

### Target file

`scripts/shared/config_loader.py`

### Procedure

In `ConfigLoader.__init__`, replace the `__file__`-based default-directory computation with a delegation to the resolver.

### Method

1. Import the resolver at the top: `from shared.runtime_paths import resolve_config_dir`.
2. In `ConfigLoader.__init__`, replace the two lines computing `repo_root` and `self._config_dir` with a single assignment: `self._config_dir = resolve_config_dir(config_dir)`.
3. Remove any now-unused `Path` import usage that becomes unreferenced (keep `Path` if still needed elsewhere in the file).

### Details

- `resolve_config_dir(None)` returns the legacy repo-root `config/` when uncompiled, so `uv run` behavior is unchanged.
- The explicit `config_dir` argument is passed straight through, preserving the override contract tested in `tests/shared/test_config_loader.py`.

## Compatibility considerations

- All ~23 call sites keep working unchanged; under `uv run` the resolved path equals the previous `__file__`-derived path.

## Security considerations

- N/A: no new privilege or command-execution surface; the change only selects a directory that existing code already reads from.

## Rollback considerations

- N/A: revert the commit; the change is a one-line delegation.

## Validation plan

- `uv run pytest tests/shared/test_config_loader.py` — default-via-resolver and explicit-override cases pass.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports` clean.
- `rg -c 'ConfigLoader\(\)' scripts/` — confirm the ~23 call sites still construct without arguments where expected.

## Completion criteria

- `ConfigLoader.__init__` no longer contains a `Path(__file__)` config computation; the explicit override still wins and the full `test_config_loader.py` suite passes.

## Out of scope

- The resolver itself (`runtime_paths.py`) and the other call-site rows are separate documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make `ConfigLoader` delegate the default dir to the resolver | Pending | — | — | |
| 2 | Update `tests/shared/test_config_loader.py` | Pending | — | — | |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: scripts/shared/config_loader.py
