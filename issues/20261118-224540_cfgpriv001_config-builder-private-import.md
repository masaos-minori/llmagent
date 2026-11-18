# Route memory JSONL dir resolution through a public config helper instead of a private import

## Priority
Low

## Summary
`config_path.resolve_memory_jsonl_dir()` imports the underscore-prefixed helper
`_get_str_or_default` from `agent.config_section_builders`. Replace that private
import with a stable, public accessor so the memory layer no longer depends on a
non-public implementation detail of the config-builders module.

## Background
The refactor commit `e6233a903` (see `issues/done/20261019-165345_memcfg001_memory-event-writers-read-a-missing-config-key.md`)
centralized the three change-event writers on `resolve_memory_jsonl_dir()` to avoid
a `KeyError('memory')` from the nonexistent nested config key. That fix introduced
`from agent.config_section_builders import _get_str_or_default` inside
`resolve_memory_jsonl_dir()`. `_get_str_or_default` is a private helper used only
internally by the `_build_*_config` builders; it is not part of any public API.

## Problem
The memory layer reaches into a private symbol (`_get_str_or_default`) of an
unrelated module. A rename, move, or removal of that helper breaks
`resolve_memory_jsonl_dir()` with an `ImportError` outside the memory module's
control and without any public contract guaranteeing its existence.

## Reason for Change
The coupling is latent today but is a maintainability risk: the next refactor of
`config_section_builders` can silently break memory path resolution. No open issue
tracks this residual; `memcfg001` fixed the `KeyError` but left the private import
in place.

## Implementation Intent
Introduce or reuse a public helper that resolves a flat string config key with a
default, and call it from `resolve_memory_jsonl_dir()`. Prefer exposing the helper
on the config-builders public surface; if a public accessor already exists, route
through it instead. Preserve the current default value and the returned value
(equal to `ctx.cfg.memory.memory_jsonl_dir` for the same input).

## Target Files or Areas
- `scripts/agent/memory/config_path.py`
- `scripts/agent/config_section_builders.py` (public surface only)

## Required Changes
- Remove `from agent.config_section_builders import _get_str_or_default` from
  `resolve_memory_jsonl_dir()`.
- Call a public accessor that resolves the flat `memory_jsonl_dir` key with the
  same default, or add such an accessor to the config-builders public surface.
- Keep the late import pattern if the resolver must stay free of top-level
  config imports, but import only the public symbol.

## Constraints
- The returned value must remain equal to `ctx.cfg.memory.memory_jsonl_dir` for the
  same input (do not change the resolved path semantics).
- Do not change the default `/opt/llm/memory` value.
- Do not alter the other change-event writers' behavior.

## Acceptance Criteria
- `config_path.py` no longer imports any underscore-prefixed symbol from
  `config_section_builders`.
- `resolve_memory_jsonl_dir()` returns the same path as before for identical input.
- `lint-imports` still passes (no new cross-layer violation).

## Testing Expectations
- Run `tests/agent/memory/test_config_path.py` and confirm it still passes.
- Add a test asserting `resolve_memory_jsonl_dir()` equals the typed
  `cfg.memory.memory_jsonl_dir` for a sample config, if not already present.
- `uv run ruff check` and `uv run mypy` on the touched files.

## Documentation Impact
None required. If `config_section_builders` documents its public API surface, note
the newly exposed helper there.

## Out of Scope
- Changing which config key is read or its default.
- Refactoring the other config consumers in `config_section_builders`.
- Any change to `memcfg001`'s original `KeyError` fix.

## Dependencies
- Addresses the residual private-import coupling left by the already-resolved
  `issues/done/20261019-165345_memcfg001_memory-event-writers-read-a-missing-config-key.md`.

## Unresolved Questions
- Whether a suitable public accessor already exists in `config_section_builders`
  that was not identified, or whether one must be added. `Needs confirmation`:
  inspect the public exports of `config_section_builders`.

## AI Implementation Instruction
- Do not touch files outside `scripts/agent/memory/config_path.py` and, if needed,
  the public export list of `scripts/agent/config_section_builders.py`.
- Preserve the resolved path and default exactly.
- Import only public symbols; never reintroduce an underscore-prefixed import.
- Run ruff, mypy, and `tests/agent/memory/test_config_path.py` before finishing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261118-224540
- **Related target files**: scripts/agent/memory/config_path.py, scripts/agent/config_section_builders.py
