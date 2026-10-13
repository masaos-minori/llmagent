## Goal

Provide a single standard-library-only leaf module `scripts/shared/runtime_paths.py` that resolves (a) the config directory and (b) the Sudachi dictionary path so both resolve correctly inside a Nuitka `--onefile` binary while remaining backward compatible with `uv run`. Implements `REQ-001` (config-dir resolver) and `REQ-003` (Sudachi-dict resolver).

## Scope

Creates exactly one new file `scripts/shared/runtime_paths.py` (new) exposing two resolver functions. No existing file is modified here; every call site delegates to this module in its own row (`config_loader.py`, `workflow_loader.py`, `config_builders.py`, `repository.py`, `chunk_splitter.py`, `cmd_config_display.py`, `context.py`).

## Assumptions

- A Nuitka-compiled module exposes a `__compiled__` marker in its globals (confirmed in Phase 0; the resolver tests patch it).
- `sys.argv[0]` points at the original binary path in a onefile binary (Phase 0), so the install root is `Path(sys.argv[0]).resolve().parent.parent` for a binary at `/opt/llm/bin/<binary>` (two levels below the root).
- `shared` is a leaf package; this module may import only the standard library (`os`, `sys`, `pathlib.Path`, `typing`).

## Design decisions

- Config-dir precedence: `LLMAGENT_CONFIG_DIR` (must exist, else explicit error) > compiled-adjacent `config/` (only when `__compiled__` is present) > legacy repository-root `config/`. Gating the adjacent lookup on `__compiled__` prevents an accidental match during a `python -m agent.repl` development run.
- Sudachi precedence: `LLMAGENT_SUDACHI_DICT` set → use that absolute path and require it to exist; unset and compiled → `/opt/llm/dict/system.dic` and require it to exist; unset and not compiled → the string `"core"`. No silent fallback, because `sudachidict_core` is not bundled in the binary and a silent fallback would only delay the failure.
- One module owns both resolvers so every call site shares identical precedence and identical fail-fast error text.

## Alternatives considered

- Per-call-site inline resolution: rejected — six call sites would drift and re-break under onefile independently, reproducing today's bug.
- Reading the dictionary path from a config key: rejected — each MCP process is restricted to its own config file (`server.py` `restrict_to`), so a shared key has no single home (UNK-03); the value travels as an environment variable instead.

## Implementation

### Target file

`scripts/shared/runtime_paths.py` (new)

### Procedure

Define (new) `resolve_config_dir(config_dir: str | None = None) -> Path` and (new) `resolve_sudachi_dict_path(dict_path: str | None = None) -> Path | Literal["core"]`, plus small private helpers, and export both at module level so callers write `from shared.runtime_paths import resolve_config_dir, resolve_sudachi_dict_path`.

### Method

1. Create `scripts/shared/runtime_paths.py`: module docstring, `from __future__ import annotations`, stdlib imports only (`os`, `sys`, `pathlib.Path`, `typing.Literal`).
2. Implement `resolve_config_dir`: if `config_dir is not None` return `Path(config_dir)` (explicit override wins); elif `env := os.environ.get("LLMAGENT_CONFIG_DIR")` is truthy, assert `Path(env).is_dir()` else raise `FileNotFoundError` naming the path; elif `"__compiled__" in globals()` return `Path(sys.argv[0]).resolve().parent.parent / "config"`; else return the legacy `Path(__file__).resolve().parent.parent.parent / "config"`.
3. Implement `resolve_sudachi_dict_path`: if `env := os.environ.get("LLMAGENT_SUDACHI_DICT")` is truthy, assert `Path(env).is_file()` else raise `FileNotFoundError`; elif `"__compiled__" in globals()` assert `Path("/opt/llm/dict/system.dic").is_file()` else raise the same; else return the literal `"core"`.
4. Add `tests/shared/test_runtime_paths.py` (its own row) covering: explicit override wins; env set to an existing dir is used; env set to a missing dir raises naming the path; uncompiled fallback uses the repo-root; compiled-adjacent branch via a patched `__compiled__`; and the Sudachi set/unset/missing/compiled-default cases.

### Details

- Every missing-path branch raises `FileNotFoundError` whose message names the offending path (AC-01, AC-05); no exception is swallowed or converted to a silent default.
- The compiled-adjacent config root is `parent.parent` of `sys.argv[0]` because the binary lives at `/opt/llm/bin/<binary>`; the Sudachi compiled default is the literal `/opt/llm/dict/system.dic` matching the deploy layout in `deploy/deploy.sh`.
- Keep both signatures positional-or-keyword so the existing `ConfigLoader(config_dir=...)` binding and the test call sites stay valid.

## Compatibility considerations

- Under `uv run` (no `__compiled__`) the final repo-root branch runs, so behavior is byte-for-byte identical to today except that a missing `LLMAGENT_CONFIG_DIR` now fails fast instead of being ignored.
- `ConfigLoader(config_dir=...)` keeps its explicit argument as top priority in its own row, so the override contract is unchanged.

## Security considerations

- N/A: path resolution adds no new command execution or privilege surface; the fail-fast on a missing env path rejects a missing path with a clear error rather than a silent fallback.

## Rollback considerations

- N/A: revert the commit; the file is new and is imported only by the call-site rows generated in this pass.

## Validation plan

- `uv run pytest tests/shared/test_runtime_paths.py` — every precedence and failure case passes.
- `uv run lint-imports` — `shared` still satisfies the `shared-is-leaf` contract in `.importlinter` (stdlib-only import).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` clean.

## Completion criteria

- `resolve_config_dir` and `resolve_sudachi_dict_path` exist, are imported by the call-site rows, and pass every case in `tests/shared/test_runtime_paths.py`; `lint-imports` reports no new `shared` violation.

## Out of scope

- Every consuming call site is a separate row: `scripts/shared/config_loader.py`, `scripts/agent/workflow/workflow_loader.py`, `scripts/agent/config_builders.py`, `scripts/rag/repository.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/agent/commands/cmd_config_display.py`, `scripts/agent/context.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/shared/runtime_paths.py` with both resolvers | Completed | 20261012-183345 | 20261013-100326 |  |
| 2 | Add unit tests in `tests/shared/test_runtime_paths.py` | Completed | 20261012-183345 | 20261013-100326 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261012-183345 | 20261013-100326 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261012-183345 | 20261013-100326 | N/A: no doc row in this pass |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: scripts/shared/runtime_paths.py