# Implementation Procedure: Strip loader/interpreter denylisted env vars in `filter_env()`

## Goal

Apply the canonical `_ENV_KEY_DENYLIST` from `shared.mcp_config` inside
`CommandValidator.filter_env()` so inherited loader/interpreter variables
(`LD_PRELOAD`, `LD_LIBRARY_PATH`, `PYTHONPATH`) are removed from the seeded parent
environment before config overrides merge. This closes the runtime env-passing gap the
config-layer denylist never covered and eliminates drift between the config and runtime
layers. Implements `REQ-005` (strip denylisted inherited keys) and `REQ-006`
(centralize the denylist via import).

Part 1 of this Plan (bounded `python3` interpreter match in `validate()`) is **already
implemented and validated** — see the sibling document
`implementations/done/20261004-110940_01_scripts_agent_http_lifecycle_command_validator.py.md`
(committed as `2637dbe5f`). This document covers **only** the not-yet-implemented remainder
(Part 2). Do not re-implement Part 1.

## Scope

Modify `scripts/agent/http_lifecycle_command_validator.py` only, specifically
`CommandValidator.filter_env()`:

- Add `import fnmatch` and an import of `_ENV_KEY_DENYLIST` from `shared.mcp_config`.
- After `result = dict(os.environ)`, delete every key matching `_ENV_KEY_DENYLIST`
  (via `fnmatch`) **before** the config-override loop.

No other file is a modification target. Part 1 (`validate()` bounded-interpreter change),
the primary allowlist contents, and subprocess launch logic are out of scope.

## Assumptions

- `_ENV_KEY_DENYLIST` holds literal keys with no `fnmatch` wildcards, so membership and
  `fnmatch` matching are equivalent for these entries (Plan assumption).
- Importing `shared.mcp_config` into the agent-layer validator is permitted by the
  import contract (`agent → shared`, `shared` is a leaf). Multiple agent modules already
  import `shared.mcp_config` (e.g. `scripts/agent/http_lifecycle.py:36`); the transitive
  cost is already paid wherever the agent layer loads MCP config, so `lint-imports` passes
  (UNK-03 resolved).
- `filter_env()` keeps its signature and return contract (`dict[str, str] | None`);
  `None` input still returns `None`.
- Benign inherited vars remain present; config-provided non-protected vars still merge.

## Design decisions

- Import `_ENV_KEY_DENYLIST` at top-of-module (absolute import), not inline, to satisfy
  ruff `I` rules and avoid `PLC0415` (import-outside-top-level).
- Strip denylisted keys immediately after seeding `result = dict(os.environ)` and before
  the `for key, value in env.items()` override loop, so an inherited denylisted key that is
  absent from `cfg.env` cannot survive into the returned dict.
- Use `fnmatch.fnmatch(key, pattern)` semantics identical to
  `shared.mcp_config._validate_env`, eliminating semantic drift between layers.
- Preserve the existing protected-override warning log for `_protected_env_vars` unchanged.

## Alternatives considered

- Local duplicate denylist tuple: rejected — reintroduces config/runtime drift that
  `REQ-006` centralizes away.
- Filtering only inside the config-override loop: rejected — inherited denylisted keys
  absent from `cfg.env` are never visited by that loop and would leak through.
- Adding keys to `_protected_env_vars`: rejected — protected vars block *config* overrides
  and emit a warning; the denylist must *strip inherited values* silently. Different
  mechanism and different failure mode.

## Implementation

### Target file

`scripts/agent/http_lifecycle_command_validator.py`

### Procedure

1. Add `import fnmatch` to the stdlib import group (alphabetically before `logging`).
2. Add an absolute import of the canonical denylist next to the existing local import:
   ```python
   from shared.mcp_config import _ENV_KEY_DENYLIST
   ```
   Place it in the absolute/import-first-party group; run `uv run ruff check` to confirm
   isort ordering (mirror how `scripts/agent/http_lifecycle.py` orders its
   `shared.mcp_config` import).
3. In `CommandValidator.filter_env()`, insert the stripping loop directly after
   `result = dict(os.environ)` and before the config-override loop:
   ```python
   result = dict(os.environ)
   for key in list(result):
       if any(fnmatch.fnmatch(key, p) for p in _ENV_KEY_DENYLIST):
           del result[key]
   for key, value in env.items():
       ...
   ```
4. Leave everything else in `filter_env()` unchanged: the `None` early-return, the
   protected-override warning, and the `return result` contract.

### Method

- Locate `filter_env()` with
  `rg -n 'def filter_env' scripts/agent/http_lifecycle_command_validator.py`
  (currently lines 101-116).
- Edit the import block (lines 10-17): add `import fnmatch` to the stdlib group and the
  `from shared.mcp_config import _ENV_KEY_DENYLIST` absolute import.
- Insert the stripping loop after `result = dict(os.environ)` (line 110).
- Confirm the `if env is None: return None` guard (lines 107-108) sits above the seeding
  so `None` input is unaffected.

### Details

- Iterate `list(result)` (a snapshot) because the dict is mutated during iteration.
- `_ENV_KEY_DENYLIST` items are literal keys; `fnmatch` equals membership for them.
- Do **not** touch `validate()`, the allowlist branch, checks 1-3, or the
  `PROTECTED_ENV_VARS` class attribute.
- Reference dependency (read-only): `scripts/agent/http_lifecycle.py:_create_and_validate_proc`
  (line 272) calls `filter_env(cfg.env)`; the return contract is unchanged, so the caller
  is unaffected.

## Compatibility considerations

- Public signature `filter_env(env: dict[str, str] | None) -> dict[str, str] | None` is
  unchanged.
- Benign inherited vars (`PATH`, `HOME`, `USER`, etc.) remain; config-provided
  non-protected vars still merge; the protected-override warning is preserved.
- Stripping `PYTHONPATH` mirrors the existing config-layer policy (`_ENV_KEY_DENYLIST`
  already excludes `PYTHONPATH`) and fails closed. Whether `PYTHONPATH` should remain
  acceptable for venv-based admin-launched Python subprocesses is flagged to the reviewer
  (`UNK-02`); changing the denylist contents is explicitly out of scope for this Plan.

## Security considerations

- The launched subprocess is an arbitrary-code-execution sink. Inheriting
  `LD_PRELOAD`/`LD_LIBRARY_PATH` enables ELF/preload library hijacking and
  `PYTHONPATH` enables module injection. Stripping these at runtime closes the gap the
  config-layer denylist never reached.
- Centralizing on `_ENV_KEY_DENYLIST` removes the config/runtime drift that let the two
  layers diverge (`REQ-006`).

## Rollback considerations

- Revert the three edits (remove `import fnmatch`, remove the `_ENV_KEY_DENYLIST` import,
  remove the stripping loop) to restore prior behavior. Risk of revert: denylisted keys
  are inherited again, re-opening the gap. Blast radius is a single caller. No schema,
  config, or `deploy.sh` impact (stdlib + one established `shared` import).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/http_lifecycle_command_validator.py` | Static: format, lint, type, security | `uv run ruff format scripts/agent/http_lifecycle_command_validator.py`; `uv run ruff check scripts/agent/http_lifecycle_command_validator.py`; `uv run mypy scripts/agent/http_lifecycle_command_validator.py`; `uv run bandit scripts/agent/http_lifecycle_command_validator.py` | Clean; no new errors/findings |
| Import contract | Architecture | `PYTHONPATH=scripts uv run lint-imports` | Pass (no `agent → shared` violation) |
| `tests/agent/test_http_lifecycle_command_validator.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_command_validator.py -v` | New `TestCommandValidatorFilterEnv` cases pass; regression suite passes |
| Full suite | Regression | `uv run pytest tests/` | No new failures |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |

## Completion criteria

- With `os.environ` containing `LD_PRELOAD`/`LD_LIBRARY_PATH`/`PYTHONPATH` and
  `cfg.env=None`, `filter_env()` returns a dict without those keys; benign inherited vars
  remain; config-provided non-protected vars still merge (`AC4`). ↔ `REQ-005`, `REQ-006`,
  `REQ-007`
- The denylist is imported from `shared.mcp_config`, not duplicated locally (`REQ-006`).
- Signature and `None`-input handling unchanged (`REQ-005`).
- `ruff format`, `ruff check`, `mypy`, `bandit`, `lint-imports` clean; full suite has no
  new failures.

## Out of scope

- Part 1 bounded-interpreter match in `validate()` (already implemented; sibling document).
- Adding other env vars (`TZ`, `PYTHONHASHSEED`, `PYTHONHOME`, `PYTHONSTARTUP`) to the
  denylist — evaluate separately.
- Changing the primary allowlist contents (`node`, `uvx`, `python`, etc.).
- Any change to subprocess launch logic beyond validation/env filtering.
- Documentation updates (`docs/*.md`): N/A unless an agent-security/env-policy doc is
  found documenting env filtering, in which case add a one-line note referencing
  `_ENV_KEY_DENYLIST`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement filter_env denylist stripping (Part 2) | Completed | 20261005-111005 | 20261005-111005 | |
| 2 | Add TestCommandValidatorFilterEnv per Validation plan | Completed | 20261005-111005 | 20261005-111005 | Part 1 tests already exist (sibling doc / commit 2637dbe5f) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261005-111005 | 20261005-111005 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-111005 | 20261005-111005 | N/A: env filtering not documented in docs/*.md |

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
- **Requirement ID**: `REQ-005` (strip denylisted inherited env vars), `REQ-006` (centralize denylist via import)
- **Source issue**: issues/20261004-065422_mcp002_filter_env-inherits-dangerous-loader-env-vars-from-parent-process-into-mcp-subprocess.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-123553_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-111005
- **Related target files**: scripts/agent/http_lifecycle_command_validator.py
