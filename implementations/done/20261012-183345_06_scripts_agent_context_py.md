## Goal

Show the resolver-derived config directory in the config-load error message instead of a `__file__`-computed path that is wrong under Nuitka `--onefile`. Implements `REQ-002` / AC-03.

## Scope

Modifies the config-load error branch in `AgentContext.__init__` in `scripts/agent/context.py`.

## Assumptions

- `AgentContext.__init__` builds `config_dir = Path(__file__).resolve().parent.parent.parent / "config"` solely to compose the error text raised at line 323 (`f"Failed to load agent config ({config_dir}): ..."`) (verified by grep at line 321).

## Design decisions

- Compute `config_dir` via `resolve_config_dir()` so the error message names the actual directory the loader will use (and fails fast on a missing env path per AC-01).

## Alternatives considered

- Formatting the raw exception's own path string: rejected — the resolver's precedence (env > compiled-adjacent > repo-root) is what must be surfaced, and the explicit-missing-path error is produced by the resolver itself.

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

Replace the `__file__`-based `config_dir` construction in the error branch with the resolver.

### Method

1. Add `from shared.runtime_paths import resolve_config_dir` to the imports.
2. Replace `config_dir = Path(__file__).resolve().parent.parent.parent / "config"` in the `except` block with `config_dir = resolve_config_dir()`.
3. Remove the `Path` import if it becomes unreferenced elsewhere in the file.

### Details

- Because `resolve_config_dir()` raises `FileNotFoundError` for a missing `LLMAGENT_CONFIG_DIR`, the message at line 323 already names the offending path (AC-01); keep the surrounding f-string intact.

## Compatibility considerations

- The error message format is unchanged; only the resolved value differs (correctly) under a compiled binary.

## Security considerations

- N/A: display/error text only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_config_builders.py` — config-load error path case passes.
- `rg "__file__" scripts/agent/context.py` — no remaining `config/` resolution outside the resolver.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports` clean.

## Completion criteria

- The error branch uses `resolve_config_dir()`; no `__file__`-based `config/` resolution remains; the error-path test passes.

## Out of scope

- The resolver (`runtime_paths.py`) and the other config-site rows are separate documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route the error-path config dir through the resolver | Completed | 20261012-183345 | 20261013-100326 |  |
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
- **Related target files**: scripts/agent/context.py