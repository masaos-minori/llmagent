# resolve_rag_config mutates the caller config and defaults the database to :memory:

## Priority
Medium

## Summary
`resolve_rag_config` writes defaults into the caller-supplied dict or object `__dict__`, and it applies the non-empty default `rag_db_path = ":memory:"` before the "required when `use_search=True`" validation, so a configuration that omits `rag_db_path` passes validation and silently searches an empty in-memory database.

## Background
Review finding F-010. Evidence (Explicit in code, Verified by reproduction): in `scripts/rag/config_resolution.py` the dict branch assigns `_raw_cfg = cfg` and the loop `for k in _ALL_FIELDS: ... _raw_cfg[k] = _DEFAULTS_FOR_ALL[k]` mutates it. Calling `resolve_rag_config({"use_search": True, "llm_url": "http://l", "embed_url": "http://e"})` returned a config with `rag_db_path == ":memory:"` and left the caller dict with 29 keys. The validation for empty `rag_db_path`, `llm_url` and `embed_url` runs after defaults are filled, so the omitted `rag_db_path` is never reported; `llm_url` and `embed_url` default to `""` and are reported, which makes the behavior inconsistent. At query time the vector search then fails with an `OperationalError` that `_search_all_queries` counts as an FTS error and returns no results.

## Problem
A missing database path produces an apparently healthy pipeline that never returns hits, with the cause hidden in a degraded counter. Mutating shared config objects can also leak defaults into other consumers of the same object.

## Reason for Change
Ambiguous config behavior (defaults that mask a required key) is the kind of fault that surfaces only in production.

## Implementation Intent
Resolve into a new mapping without mutating the input, and validate required keys against the caller-provided values (or give `rag_db_path` no usable default when search is enabled).

## Target Files or Areas
- `scripts/rag/config_resolution.py` (`resolve_rag_config`, `_DEFAULTS_FOR_ALL`)
- `tests/rag/test_config_resolution.py`

## Required Changes
- Copy the input before applying defaults.
- Treat `rag_db_path` as required when `use_search` is true, reporting it like `llm_url` and `embed_url`.
- Add tests for non-mutation and for the missing-path error.

## Constraints
- Keep the priority order of configuration sources.
- Do not change the default values of unrelated keys.

## Acceptance Criteria
- The caller dict or object is unchanged after resolution.
- `use_search=True` without `rag_db_path` raises `ValueError` naming it.
- Existing configurations that set the path keep working.

## Testing Expectations
- Unit tests in `tests/rag/test_config_resolution.py`.
- `uv run pytest tests/rag -q`, ruff and mypy.

## Documentation Impact
Update the RAG configuration reference if it lists `rag_db_path` as optional.

## Out of Scope
- Changing how configuration files are loaded.
- Removing `:memory:` from test helpers that rely on it.

## Dependencies
N/A: none

## Unresolved Questions
Whether any in-tree caller relies on `:memory:` as a default with `use_search=True` is `Needs confirmation` (search `tests/` and `scripts/`).

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131121
- **Related target files**: `scripts/rag/config_resolution.py`, `tests/rag/test_config_resolution.py`
