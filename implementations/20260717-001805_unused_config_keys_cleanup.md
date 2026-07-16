# Implementation Procedure: Resolve Unused Configuration Keys Across config/*.toml and workflows/default.json

Source plan: `plans/20260716-234130_plan.md`
Source requirement: `requires/20260716_22_require.md`

## Goal

Every config key audited in `requires/20260716_22_require.md` either drives real runtime behavior or no longer exists in any `config/*.toml` / `config/workflows/*.json` file, its Python parsing code, and its documentation — per the user-confirmed per-item disposition (Group 1: remove; Group 2: wire up).

## Scope

**Disposition (user-confirmed interactively before this plan was written):**
- **Group 1 — remove**: `web_search_max_results` (agent.toml), `[mcp_servers.*].healthcheck_mode` ×10 (agent.toml), `mdq_mcp_server.toml`'s `status`, `workflows/default.json`'s `stages[].description`, `workflows/default.json`'s `retry_policy.backoff`.
- **Group 2 — wire up**: `mdq_mcp_server.toml`'s `include_globs`, `exclude_globs`, `max_snippet_chars`, `max_chunk_chars`, `max_file_chars`, `search_timeout_sec`; `workflows/default.json`'s `stages[].retryable`.

**In scope**
1. `config/agent.toml` — remove 1 top-level key + 10 identical `healthcheck_mode` lines.
2. `scripts/agent/config_dataclasses.py` — remove `RAGConfig.web_search_max_results`.
3. `scripts/agent/config_builders.py` — remove its builder line.
4. `scripts/agent/commands/cmd_config_display.py` — remove its `/config` display line.
5. `scripts/shared/mcp_config.py` — remove `HealthcheckMode` enum, `McpServerConfig.healthcheck_mode` field + validation branch, `_derive_healthcheck_mode()`, and the `healthcheck_mode` resolution branch in `_build_single_server()`.
6. `scripts/agent/services/config_reload.py` — remove `"healthcheck_mode"` from `_MCP_SERVER_FIELDS`.
7. `config/mdq_mcp_server.toml` — remove `status`; keep and wire `include_globs`, `exclude_globs`, `max_snippet_chars`, `max_chunk_chars`, `max_file_chars`, `search_timeout_sec`.
8. `scripts/mcp_servers/mdq/indexer.py` — consume `include_globs`/`exclude_globs` in place of hardcoded `rglob("*.md")` (4 call sites); consume `max_file_chars` (skip-with-warning) and `max_chunk_chars` (truncate) during indexing.
9. `scripts/mcp_servers/mdq/search.py` — consume `max_snippet_chars` in place of hardcoded `[:150]`; consume `search_timeout_sec` via a bounded wait.
10. `config/web_search_mcp_server.toml` — no key removal; `default_max_results`/`max_results_limit` become actually-consumed.
11. `scripts/mcp_servers/web_search/models.py` — source `SearchRequest`'s Pydantic `Field` bounds from `WebSearchConfig.load()` instead of hardcoded module constants.
12. `config/workflows/default.json` — remove `description` from all 3 stage entries; remove `backoff` from `retry_policy`; keep `retryable` on all 3 stages.
13. `scripts/agent/workflow/workflow_loader.py` — remove `description`/`backoff` from `_StageJson`/`StageDefinition`/`_REQUIRED_STAGE_KEYS`/`_RetryPolicyJson`/`RetryPolicy`/`_REQUIRED_POLICY_KEYS`/`_SUPPORTED_BACKOFF`.
14. `scripts/agent/workflow/workflow_engine.py` — generalize `_run_execute_with_retry` into a stage-agnostic `_run_stage_with_retry` gated on `stage_def.retryable`, applied to `plan`/`execute`/`verify` uniformly.
15. `scripts/agent/workflow/models.py` — remove `StageDefinition.description`, `RetryPolicy.backoff` (confirm exact field list by reading the file first).
16. Tests: `tests/test_workflow_loader.py`, `test_workflow_models.py`, `test_workflow_engine.py`, `test_web_search_models.py`, `test_mdq_indexer.py`, `test_mdq_search.py`, and any test referencing `HealthcheckMode`/`healthcheck_mode`, `web_search_max_results`, or MDQ's six wired-up keys.
17. Docs: any doc listing `healthcheck_mode`, `web_search_max_results`, MDQ's `status`, or the workflow schema's `description`/`backoff` as configurable.

**Out of scope**
- Implementing a second MCP healthcheck transport — only the inert placeholder is removed.
- Any backoff strategy beyond `"fixed"`.
- Redesigning MDQ's chunking/parsing algorithm — size enforcement is a bound/truncation layer, not a `parser.py` rewrite.
- The `[[tool_definitions]]` block's ~300 JSON-schema properties in `agent.toml`.

## Assumptions

1. `StageDefinition`/`RetryPolicy` in `scripts/agent/workflow/models.py` are plain dataclasses (to be confirmed by direct read in Procedure step 1 — exact field-removal syntax depends on this).
2. `_search_docs_structured()` in `search.py` is synchronous, called via `asyncio.to_thread`. Wrapping it in `asyncio.wait_for(...)` bounds the caller's wait but cannot forcibly abort a truly hung SQLite call in the background thread — accepted as a documented limitation (see Risks R-1), not a blocker.
3. MDQ's `max_chunk_chars`/`max_file_chars` have no existing enforcement point (`_index_single_file` writes content verbatim with no length check). Chosen design: skip-with-warning for oversized files (a silently-truncated file would produce misleading search results), truncate for oversized chunks (see UNK-01 resolution below).
4. Removing `RAGConfig.web_search_max_results` does not remove `WebSearchConfig.default_max_results`/`max_results_limit` — these survive as the sole source of truth per Group 1's "consolidate on the web-search server's own config" wording.
5. `SearchRequest`'s Pydantic `Field` bounds are evaluated once at class-definition (module-import) time; sourcing them from `WebSearchConfig.load()` at import time is consistent with `server.py`'s existing `_cfg: WebSearchConfig = WebSearchConfig.load()` pattern — config is fail-fast-loaded once at process startup, not hot-reloaded per request.
6. `workflow_engine.py`'s `_run_execute_with_retry` retrying only `"execute"` today is a hardcoded stage-name check, not a structural constraint — `_run_stage` already takes an arbitrary `stage_id`; generalizing to gate on `stage_def.retryable` is a mechanical refactor.
7. No config file other than `config/agent.toml` and `config/workflows/default.json` references any of the removed keys (`healthcheck_mode`, `web_search_max_results`, `status`, `description`, `backoff`) outside their home files — no cross-file schema-version bump needed.

## Unknowns to resolve during implementation

- **UNK-01 (resolved by analysis, non-blocking)**: `max_file_chars` overflow → skip-and-warn (file not indexed at all), not truncate-and-index — a silently-truncated file would produce misleading search results (a query matching content past the truncation point would never find it); skip-and-warn is loud and traceable, matching the existing pattern where `authorize_path()` failures raise loudly.
- **UNK-02 (non-blocking, resolve in Procedure step 1)**: exact current field order/type of `StageDefinition`/`RetryPolicy` in `models.py` — read the file directly before editing.
- **Confirm in Procedure step 5**: `config/workflows/default.json`'s current `retryable` values per stage should already be `true` only for `execute`; if `plan`/`verify` are also `true`, generalizing the retry wrapper is a behavior change requiring explicit flag-up before merging, not a silent assumption (see Risk R-2).

## Implementation

### Target file

Multiple files across `config/`, `scripts/agent/`, `scripts/shared/`, `scripts/mcp_servers/mdq/`, `scripts/mcp_servers/web_search/`, `scripts/agent/workflow/`, and `tests/`. This is a single cohesive cleanup+wiring change; grouped below by phase.

### Procedure

1. **Read `scripts/agent/workflow/models.py` in full** (resolves UNK-02) and `deploy/deploy.sh` (confirms whether `config/agent.toml` is in its copy list) before any edit.

2. **Group 1 removals** (each independently revertable):
   - Remove `web_search_max_results` from `agent.toml`, `RAGConfig` (`config_dataclasses.py`), `_build_rag_config` (`config_builders.py`), `cmd_config_display.py`'s display line; grep `tests/` for references and update; add a short dated NOTE comment in `agent.toml` matching the repo's removed-key convention.
   - Remove `healthcheck_mode` ×10 from `agent.toml`; remove `HealthcheckMode` enum, `McpServerConfig.healthcheck_mode` field + validation branch, `_derive_healthcheck_mode()`, and the resolution branch in `_build_single_server()` from `scripts/shared/mcp_config.py`; remove `"healthcheck_mode"` from `_MCP_SERVER_FIELDS` in `config_reload.py`; grep `tests/` for `HealthcheckMode`/`healthcheck_mode` references (e.g. `McpServerConfig(...)` constructions) and update.
   - Remove `mdq_mcp_server.toml`'s `status` line; add a NOTE comment matching this file's existing 6-block convention (what was removed, when, why, where to look if re-adding).
   - Remove `workflows/default.json`'s `description` ×3 stage entries + `retry_policy.backoff`; remove corresponding fields/constants from `workflow_loader.py` (`_StageJson`, `_REQUIRED_STAGE_KEYS`, `_RetryPolicyJson`, `_REQUIRED_POLICY_KEYS`, `_SUPPORTED_BACKOFF`) and `models.py` (`StageDefinition.description`, `RetryPolicy.backoff`); grep and update `tests/test_workflow_loader.py`/`test_workflow_models.py`/`test_workflow_engine.py`.
   - Run `rg -n "healthcheck_mode|HealthcheckMode|web_search_max_results|\"description\"|\"backoff\"" config/ scripts/ tests/ docs/` and confirm only intentional survivors remain.

3. **Group 2 wiring — MDQ indexing knobs**:
   - Add a shared `_iter_indexable_files(service, directory)` helper to `indexer.py` yielding files matching `service.include_globs`, excluding `service.exclude_globs`; replace all 4 `rglob("*.md")` call sites (`_index_directory`, `refresh_paths` force-mode branch, incremental-mode branch, deletion-detection scan) with this helper.
   - Add `max_file_chars` skip-and-warn check in `_index_single_file`: after `path.stat().st_size` is available but before parsing, check file length; if it exceeds `service.max_file_chars`, log a warning and `return` before writing any chunk (mirrors the existing `if not sections: ... return` early-exit pattern).
   - Add `max_chunk_chars` truncation in the per-section loop: if `len(section["content"])` exceeds `service.max_chunk_chars`, truncate before `content_hash` is computed from it, so hash and stored content stay consistent.
   - Replace `search.py`'s hardcoded `snippet=row["content"][:150]` with `snippet=row["content"][: service.max_snippet_chars]`.
   - Wrap `_search_docs_structured`'s invocation in `search_docs()` with `asyncio.wait_for(asyncio.to_thread(_search_docs_structured, service, req), timeout=service.search_timeout_sec)`, raising `MdqConsistencyError` on `asyncio.TimeoutError`.

4. **Group 2 wiring — web-search config**:
   - Verify whether `WebSearchConfig.load()` at `models.py`'s module-import time creates a circular import with `server.py` (which already imports from `models.py`).
   - If no circular import: source `SearchRequest`'s `Field` bounds (`ge=1, le=_cfg.max_results_limit`, default `_cfg.default_max_results`) from a module-level `_cfg = WebSearchConfig.load()` in `models.py`, matching `server.py`'s existing pattern.
   - If circular import occurs: fall back to keeping the config load in `server.py` and pass resolved bounds into a factory function that builds `SearchRequest` dynamically.

5. **Group 2 wiring — workflow `retryable`**:
   - Verify `config/workflows/default.json`'s current `retryable` values per stage (expected: `true` for `execute`, `false` for `plan`/`verify`) — if not as expected, flag as a behavior-change decision point before proceeding (Risk R-2).
   - Add `_run_stage_with_retry(task, stage_id, fn)` to `workflow_engine.py`: looks up `stage_def.retryable` via `self._wdef.get_stage(stage_id)`; if not retryable, calls `_run_stage` once; if retryable, loops with the existing backoff/logging/span logic up to `policy.max_attempts`, raising `WorkflowHaltError` on exhaustion.
   - Replace `run()`'s 3 call sites (`_run_stage(task, "plan", plan_fn)`, `_run_execute_with_retry(task, execute_fn)`, `_run_stage(task, "verify", verify_fn)`) with `_run_stage_with_retry(task, "plan"/"execute"/"verify", ...)`.
   - Delete `_run_execute_with_retry` once its logic is folded into `_run_stage_with_retry`.

6. **Tests**:
   - `tests/test_mdq_indexer.py`: a file matching `exclude_globs` is not indexed; a non-`.md` file matching a customized `include_globs` is indexed; an oversized file is skipped with a warning log and absent from `documents`; an oversized chunk is truncated in storage.
   - `tests/test_mdq_search.py` (or `test_mdq_service.py`): snippet length respects `max_snippet_chars`; a search exceeding `search_timeout_sec` raises `MdqConsistencyError` (via monkeypatched slow query or small timeout + artificial delay).
   - `tests/test_web_search_models.py`: `SearchRequest`'s bound reflects a monkeypatched non-default `WebSearchConfig`.
   - `tests/test_workflow_engine.py`: a stage with `retryable: false` does not retry on failure (new coverage for `plan`/`verify` under the generalized wrapper); existing `execute`-retries behavior unchanged.
   - Remove/update any test asserting on now-removed fields (`healthcheck_mode`, `web_search_max_results`, workflow `description`/`backoff`, MDQ `status`).

7. **Full validation pass** (per `rules/toolchain.md`): ruff format/check, mypy, lint-imports, bandit, full pytest, check-mcp-docs, diff-cover (≥90%), pre-commit.

8. **Documentation sweep**: `rg -rl "healthcheck_mode|web_search_max_results" docs/` and update/remove stale references; update MDQ's config-table doc to note the 6 keys are now enforced, not just documented defaults; update workflow schema docs to drop `description`/`backoff` and note `retryable` is now enforced per-stage.

9. **Deployment & verification**: confirm `config/agent.toml`'s presence in `deploy/deploy.sh`'s copy list (content-only change, no list update needed if already present — flag separately if absent); rerun `tests/test_config_reload.py` explicitly since `_MCP_SERVER_FIELDS` was edited; no new service/port, no restart-policy change.

### Method

- Direct source/config edits, phase-ordered so each group (removals, MDQ wiring, web-search wiring, workflow wiring) is independently committable and testable.
- New `_iter_indexable_files()` and `_run_stage_with_retry()` helpers follow existing code style/patterns in their respective modules (no new abstraction layer beyond what's needed).
- `rg`/`grep` sweeps at the end of each group to catch stray references before moving to the next.

### Details

- Do not trust the `_iter_indexable_files()` pseudocode as final — `pathlib.Path.match()` handles `**` differently from `Path.rglob()`; empirically test against the default `exclude_globs` value (`[".git/**", "__pycache__/**"]`) on a realistic directory tree before considering the glob wiring done; switch to `fnmatch` against a relative POSIX path string if `Path.match()` proves unreliable (Risk R-3).
- Truncate `max_chunk_chars` content *before* computing `content_hash`, not after, so the hash matches what's actually stored.
- Do not assume `plan`/`verify` are `retryable: false` in `config/workflows/default.json` — verify directly; if either is `true`, this refactor changes observable behavior and must be flagged before merging (Risk R-2), not silently accepted.
- `HealthcheckMode` removal touches a widely-imported module (`mcp_config.py`); the `rg` sweep must search for `HealthcheckMode` (the class name), not just the `healthcheck_mode` field name, to catch isinstance-checks or imports elsewhere.

## Validation plan

| Target | Tool / Command | Expected outcome |
|---|---|---|
| Group 1 removals | `rg -n "healthcheck_mode\|HealthcheckMode\|web_search_max_results" scripts/ config/ tests/` | 0 matches outside intentional NOTE comments |
| MDQ indexer glob wiring | `uv run pytest tests/test_mdq_indexer.py -v` | `exclude_globs` match → skipped; oversized file → skipped + warning; oversized chunk → truncated in DB |
| MDQ search snippet/timeout | `uv run pytest tests/test_mdq_search.py -v` | snippet length ≤ `max_snippet_chars`; simulated slow query raises `MdqConsistencyError` within timeout bound |
| Web-search config bounds | `uv run pytest tests/test_web_search_models.py -v` | `SearchRequest`'s bound reflects a monkeypatched `WebSearchConfig` |
| Workflow `retryable` wiring | `uv run pytest tests/test_workflow_engine.py -v` | non-retryable stage does not retry; `execute`'s existing retry behavior unchanged |
| Full regression | `uv run pytest -v` | no new failures vs. pre-change baseline |
| Doc consistency | `uv run check-mcp-docs` | no new issues |
| Lint/type/arch/security | `ruff`, `mypy`, `lint-imports`, `bandit` | 0 errors / no new findings |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
| Pre-commit | `uv run pre-commit run --all-files` | pass |

## Risks (carried from source plan)

- **R-1**: `search_timeout_sec` only bounds the caller's wait, not the underlying SQLite call — a wedged query keeps running in a background thread. Mitigation: document explicitly; `_search_docs_structured` closes its own connection in `finally`, so the thread eventually exits (delayed, not permanent leak).
- **R-2**: Generalizing the retry wrapper changes `plan`/`verify` behavior if their `retryable` flag is not already `false` — verify before considering the refactor complete; treat `true` as a separate decision point requiring explicit confirmation.
- **R-3**: `Path.match()`'s `**` semantics may differ from expected shell-style globbing for `exclude_globs` like `.git/**` — must empirically test against the default value before considering the feature done.
- **R-4**: `mcp_config.py` is widely imported; removing `HealthcheckMode` risks a missed reference elsewhere — the `rg` sweep plus full `pytest -v` + `mypy scripts/` pass is the empirical backstop.
