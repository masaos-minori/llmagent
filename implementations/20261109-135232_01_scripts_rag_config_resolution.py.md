## Goal

Make `resolve_rag_config` resolve into a fresh mapping without mutating the caller's dict or object, layer `cfg` over `module_cfg` over defaults for a dict or object `cfg`, and make `rag_db_path` a required key when `use_search=True` by defaulting it to `""` so the existing non-empty check reports it (`REQ-001`: no mutation; `REQ-002`: required path; `REQ-003`: `module_cfg` layering; `REQ-004`: unchanged branches and defaults; `REQ-005`: MCP service construction resolves its configured values).

## Scope
**Release unit**: ragrev008-core

- In scope: `resolve_rag_config`, three new private helpers, and the `rag_db_path` default in `scripts/rag/config_resolution.py`; the companion tests in `tests/rag/test_config_resolution.py`.
- Out of scope: how config files are loaded, the `cfg is None` branch semantics (config loader first, `module_cfg` only as fallback), the `RagConfigImpl` passthrough, other default values, `build_rag_cfg_adapter`, and removing `:memory:` from test helpers that set it explicitly.
- Plan: `plans/20261108-165441_ragrev008_rag-config-defaults-mutation.md` (Plan steps 1 and 2).

## Assumptions

- Re-verified at generation time (by symbol): the dict branch assigns `_raw_cfg = cfg` and the object branch `_raw_cfg = cfg.__dict__`, then the defaults loop writes into it; `_DEFAULTS_FOR_ALL["rag_db_path"]` is `":memory:"`; `module_cfg` is read only inside the `else` branch where `cfg` is `None`; the `use_search` check over `rag_db_path`, `llm_url`, `embed_url` raises `ValueError("RAG config requires non-empty ... when use_search=True")`.
- The only production caller is `RagPipeline.__init__` in `scripts/rag/pipeline.py`; the MCP service builds `RagPipeline(http, rag_cfg, module_cfg=module_cfg)` where `rag_cfg` (from `build_rag_cfg_adapter`) lacks the database and tuning keys and `module_cfg` carries them (`_build_module_cfg` in `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`). Constructing `RagPipeline` does not open the database.
- Layering keeps the caller's values highest: for a dict or object `cfg`, `cfg` keys win over `module_cfg` keys, and `module_cfg` keys win over defaults.
- The default for `rag_db_path` changes to `""` only; every other default is unchanged. `use_search=False` without a path still resolves.
- Companion test file: `tests/rag/test_config_resolution.py` is named in `Related Tests` of this row only and needs no design decision of its own, so it is a companion here (it gets no document).
- Fallout tests (`tests/agent/commands/test_agent_rag.py`, found in Step 3a) are covered by `..._04_tests_agent_commands_test_agent_rag.py.md`; this and that procedure ship in Release unit `ragrev008-core` because the required-path validation breaks the fixture until both land.
- Locate code by symbol name; line numbers drift.

## Design decisions

- Extract `_load_raw_cfg` (new), `_apply_defaults` (new), and `_require_search_fields` (new) so each helper stays at complexity grade A or B; `resolve_rag_config` is grade D (24) today and must not rise.
- `_load_raw_cfg` (new) returns a new dict: for a dict `cfg`, `{**module, **cfg}`; for an object, `{**module, **vars(cfg)}` (via `__dict__`); the `None` branch keeps its current order (loader, then `module_cfg` only as fallback) and returns a copy.

## Alternatives considered

- Only copy and require the path: rejected; the MCP adapter lacks `rag_db_path`, so service start would fail.
- Add the missing keys to `build_rag_cfg_adapter`: viable but touches the MCP package and leaves other callers exposed (Plan UNK-03); a separate Plan if wanted.
- Keep `:memory:` and check the original input for the key: rejected; it would still pass for callers that deliberately rely on resolution.

## Implementation
### Target file
`scripts/rag/config_resolution.py`

### Procedure
1. Change `_DEFAULTS_FOR_ALL["rag_db_path"]` from `":memory:"` to `""`.
2. Add `_load_raw_cfg(cfg, module_cfg, config_loader)` (new) holding the current source-selection logic, returning a new dict: a dict `cfg` layers over `module_cfg or {}`; an object with `__dict__` layers its attributes over `module_cfg or {}`; the `None` branch keeps the loader-then-`module_cfg` fallback exactly as today and returns `dict(...)` of the result.
3. Add `_apply_defaults(raw)` (new) returning `{k: raw[k] if k in raw else _DEFAULTS_FOR_ALL[k] for k in _ALL_FIELDS}`; this also performs the unknown-key filtering the current code does after the defaults loop.
4. Add `_require_search_fields(filtered_cfg)` (new) holding the current `use_search` check and the same `ValueError` text.
5. Rewrite `resolve_rag_config` to: return a `RagConfigImpl` input unchanged; call `_load_raw_cfg` (new), `_apply_defaults` (new); run the existing validator, warning, and error handling; call `_require_search_fields` (new); return `RagConfigImpl(**filtered_cfg)`.
6. Update the docstring's priority list: for a dict or object `cfg`, caller values, then `module_cfg`, then defaults; for `None`, config loader then `module_cfg`; and the `Raises` note that `rag_db_path` is required with `use_search=True`.

### Method
- Never assign into the input `cfg`, its `__dict__`, `module_cfg`, or the loader's returned dict; every write goes to a new dict.
- Keep the error message form `RAG config requires non-empty {names} when use_search=True` with names in the order `rag_db_path`, `llm_url`, `embed_url`.

### Details
- Existing tests, including those using the real validator, run unmodified (`REQ-004`); do not edit assertions of existing tests, and keep `test_module_cfg_fallback_when_no_loader_and_no_exception` as is.
- Run `uv run radon cc scripts/rag/config_resolution.py -s -n C` after the edit: `resolve_rag_config` must not be above its previous grade and each new helper must be A or B.
- `uv run python tools/check_module_size.py` must stay clean; add no import beyond what exists.

### Companion test files
- `tests/rag/test_config_resolution.py`
  - Procedure: add tests for non-mutation of a dict and of a `SimpleNamespace` (snapshot equality of keys, values, attribute count; AC-1); `use_search=True` with a missing, empty, and `None` `rag_db_path` raising `ValueError` naming `rag_db_path` and listing all empty names together, and `use_search=False` without a path still resolving (AC-2); an adapter-shaped `SimpleNamespace` plus `module_cfg={"rag_db_path": "/x", "sqlite_timeout": 9, "mqe_n_queries": 7}` resolving to those values and a key present on `cfg` beating the same key in `module_cfg` (AC-3); a service-shaped `RagPipeline(MagicMock(), cfg, module_cfg=...)` construction whose `_rag_db_path` equals the `module_cfg` value (AC-5); keep every existing test unmodified (AC-4).
  - Validation: `uv run pytest tests/rag/test_config_resolution.py tests/agent/test_rag_get_cfg.py -q`; the new tests fail on HEAD and pass after, and the existing tests pass unmodified.

## Compatibility considerations

- Public signature and return type are unchanged. Behavior changes: the caller's dict or object is no longer mutated; `module_cfg` is now honored for a dict or object `cfg`; `use_search=True` without a path now raises instead of resolving to `:memory:`.
- The MCP service keeps working because `module_cfg` supplies `rag_db_path`; its configured database and tuning values are now honored instead of defaults (Plan UNK-01: owner check after deploy).
- In-tree fixtures that relied on the implicit `:memory:` default fail until fixed: `tests/agent/commands/test_agent_rag.py` (separate procedure); the Phase 1 full-suite baseline run can name more, each a fallout amendment.

## Security considerations

N/A: configuration resolution only; the change removes a silent fallback to an in-memory database and adds no new input source.

## Rollback considerations

N/A: revert the commit together with the fallout procedure (Release unit `ragrev008-core`).

## Validation plan

- Record the pre-change baseline `uv run pytest tests -q` before editing (Plan step 1, no file change), then compare after the change.
- `uv run pytest tests/rag/test_config_resolution.py tests/agent/test_rag_get_cfg.py -q`, `uv run pytest tests/mcp_servers/rag_pipeline -q`, `uv run pytest tests -q`.
- `uv run ruff check scripts/rag/config_resolution.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit scripts/rag/config_resolution.py`.
- `uv run radon cc scripts/rag/config_resolution.py -s -n C`, `uv run python tools/check_module_size.py`, `uv run python tools/check_docstrings.py`.

## Completion criteria

- The caller's dict or object is unchanged after resolution; a dict or object `cfg` gets missing keys from `module_cfg` before defaults and its own keys always win.
- `use_search=True` without a non-empty `rag_db_path` raises `ValueError` naming it together with any empty `llm_url` / `embed_url`.
- A service-shaped `RagPipeline` has `_rag_db_path` equal to the `module_cfg` value.
- Existing resolver tests pass unmodified; the full suite shows no new failures versus the baseline; static gates are clean.

## Out of Scope

- `tests/agent/commands/test_agent_rag.py`, other fallout fixtures, and docs (separate procedures or fallout amendments).
- `build_rag_cfg_adapter`, config file loading, unrelated default values.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Record the pre-change `uv run pytest tests -q` baseline (no file change) | Pending | — | — | |
| 2 | Add the failing tests to the companion `tests/rag/test_config_resolution.py` and confirm they fail on HEAD | Pending | — | — | |
| 3 | Implement the helpers, layering, and `""` default in `scripts/rag/config_resolution.py` | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`), the MCP service tests, and compare the full suite with the baseline | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (no mutation), `REQ-002` (required path), `REQ-003` (`module_cfg` layering), `REQ-004` (unchanged branches), `REQ-005` (service construction)
- **Source issue**: issues/20261108-131121_ragrev008_rag-config-defaults-mutation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165441_ragrev008_rag-config-defaults-mutation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-135232
- **Related target files**: `scripts/rag/config_resolution.py`, `tests/rag/test_config_resolution.py`
