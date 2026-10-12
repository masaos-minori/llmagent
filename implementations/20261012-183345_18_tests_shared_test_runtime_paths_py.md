## Goal

Add unit tests for the new resolver module `scripts/shared/runtime_paths.py`, covering config-dir precedence, the missing-directory error, the non-compiled fallback, and the compiled-adjacent branch via a patched compiled marker, plus the Sudachi-dict set/unset/missing/compiled-default cases. Implements `REQ-001` / `REQ-003` / AC-01, AC-02, AC-04, AC-05.

## Scope

Creates one new test file `tests/shared/test_runtime_paths.py` (new). It tests only the resolver's two functions; the call-site rows add their own integration-style assertions.

## Assumptions

- `resolve_config_dir(config_dir=None)` and `resolve_sudachi_dict_path(dict_path=None)` are defined in `scripts/shared/runtime_paths.py` (its own row).
- A Nuitka-compiled module exposes a `__compiled__` marker; the tests patch it to exercise the compiled-adjacent branch without a real binary.

## Design decisions

- Test each precedence branch explicitly: explicit override wins; env set to an existing dir is used; env set to a missing dir raises `FileNotFoundError` naming the path; uncompiled fallback uses the repo-root; compiled-adjacent branch uses `parent.parent` of a synthetic `sys.argv[0]`.
- For the Sudachi resolver, test: env set to an existing file is used; env set to a missing file raises; unset+uncompiled returns the literal `"core"`; unset+compiled returns the `/opt/llm/dict/system.dic` default (and raises if that path is missing).

## Alternatives considered

- Testing against a real Sudachi dictionary: rejected — a real tiny dictionary is not required; the resolver returns a path or the `"core"` literal, which is fully unit-testable without dictionary contents.

## Implementation

### Target file

`tests/shared/test_runtime_paths.py` (new)

### Procedure

Write pytest cases for both resolver functions.

### Method

1. Create `tests/shared/test_runtime_paths.py`; import `resolve_config_dir` and `resolve_sudachi_dict_path` from `shared.runtime_paths`.
2. Config-dir cases:
   - explicit `config_dir` argument wins over everything.
   - `LLMAGENT_CONFIG_DIR` set to an existing temp dir is returned as a `Path`.
   - `LLMAGENT_CONFIG_DIR` set to a missing dir raises `FileNotFoundError` whose message names the path.
   - with no env and no `__compiled__`, the repo-root `config/` is returned.
   - with a patched `__compiled__` and a synthetic `sys.argv[0]` at `/opt/llm/bin/<binary>`, the adjacent `config/` (`parent.parent / "config"`) is returned.
3. Sudachi cases:
   - `LLMAGENT_SUDACHI_DICT` set to an existing temp file is returned as a `Path`.
   - `LLMAGENT_SUDACHI_DICT` set to a missing file raises `FileNotFoundError` naming the path.
   - unset and uncompiled returns the string `"core"`.
   - unset and compiled returns `/opt/llm/dict/system.dic` when it exists; raises when it does not.
4. Use `monkeypatch` to set/clear env vars and to inject `__compiled__` into the module globals; use `tmp_path` for the temp dirs/files.

### Details

- Patch `__compiled__` by setting it in the module's globals (`import shared.runtime_paths as rp; rp.__dict__["__compiled__"] = True`) and restoring afterward.
- Keep the cases independent; clear env vars between cases so ordering does not matter.

## Compatibility considerations

- The file is new; it does not affect existing tests.

## Security considerations

- N/A: tests for path resolution; the fail-fast cases assert the explicit-error behavior (AC-01, AC-05).

## Rollback considerations

- N/A: revert the commit; the file is new.

## Validation plan

- `uv run pytest tests/shared/test_runtime_paths.py` — every precedence and failure case passes.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` clean.

## Completion criteria

- `tests/shared/test_runtime_paths.py` covers all precedence and failure cases listed above; the suite passes.

## Out of scope

- The resolver implementation (`scripts/shared/runtime_paths.py`) and the call-site test updates are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/shared/test_runtime_paths.py` with config-dir cases | Pending | — | — | |
| 2 | Add Sudachi-dict cases | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: tests/shared/test_runtime_paths.py
