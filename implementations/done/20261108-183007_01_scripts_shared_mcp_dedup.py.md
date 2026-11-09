## Goal
Route the `mcp_dedup` config default through the shared config-directory resolver and add a per-resolved-path load cache with an invalidation seam: no CWD-relative default path (`REQ-001`), no TOML re-read per turn (`REQ-002`), the fallback DB path pinned to the project's fallback-literal convention (`REQ-003`), and the seam that lets tests prove both (`REQ-005`) — while keeping every existing error type and the engine's fail-open turn contract (`REQ-004`) unchanged.

## Scope
**Release unit**: wfaudit011-full

- Covers Plan `plans/20261108-084012_wfaudit011_dedup-config-path-boundary.md` row 1 only: `scripts/shared/mcp_dedup.py`.
- Tests added in the existing `tests/shared/test_mcp_dedup.py` (not a plan-table row, so it gets no document of its own).

## Assumptions
- `resolve_config_dir()` (L51-66 in `scripts/shared/runtime_paths.py`) precedence: explicit argument > `LLMAGENT_CONFIG_DIR` (must exist) > compiled-adjacent `config/` > legacy repository-root `config/` (`_REPO_ROOT_CONFIG`, already an absolute path). A no-arg dev run therefore resolves the same `config/mcp_dedup.toml` it loads today, just CWD-independently; the compiled production binary resolves `/opt/llm/config` (both trees hold the file — verified 20261108).
- `DEFAULT_CONFIG_PATH` has no external consumers (`rg` verified 20261108: referenced only inside `scripts/shared/mcp_dedup.py`), so removing it breaks nothing.
- The root `tests/conftest.py` sets `LLMAGENT_CONFIG_DIR` to an isolated temp config dir for the whole suite; resolver tests use a per-test `monkeypatch` of that variable, and the new cache tests call the invalidation seam in teardown so the module cache never leaks across tests.
- A process-lifetime cache is acceptable: config changes require a service restart, matching every other config consumer in the project (plan Assumptions).
- `scripts/shared` must not import `scripts/db` (the shared-leaf import contract, stated at `scripts/shared/execution_snapshot.py` L48-49), so the DB-path convention is honored as a matching literal plus tests, not an import.
- Overlap check `tools/check_plan_target_overlaps.py` (20261108): no findings. Sibling procedures `175155_02`/`170505_06` modify `scripts/agent/workflow/workflow_engine.py` but not the loader or its call site (this plan's confirmed no-change reference), so there is no sequencing dependency against this document.

## Design decisions
- Resolve lazily at call time via `_default_config_path` (new) instead of an import-time constant: import-time resolution would freeze `LLMAGENT_CONFIG_DIR` before per-test `monkeypatch` and bypass the compiled-binary guard timing (plan "resolve once" is satisfied by the cache, not by import-time evaluation).
- Cache every successful load in `_DEDUP_CONFIG_CACHE` (new), keyed by the resolved absolute path; failures are never cached, so a first-load error keeps propagating to the engine catch (`workflow_engine.py:162-171`) and the dispatcher fail-open (`dispatch.py` `_dedup_context`) exactly as today (`REQ-004`).
- Invalidation seam: a `clear_dedup_config_cache` (new) function (plan Design choice over mtime checks: simpler, and restart-based reload matches project convention).
- `DEFAULT_DB_PATH` stays the literal `/opt/llm/db/mcp_dedup.sqlite` — the same fallback-literal shape `scripts/db/config.py` uses for the other databases; no config wiring (`UNK-01` resolved: no `[paths]` section exists in this project).

## Alternatives considered
- mtime-based cache invalidation: rejected — a per-turn stat is still a hot-path syscall and in-process config drift contradicts the project's restart-based convention.
- Bypassing the cache for explicit-path calls: rejected — keying by resolved absolute path already prevents fixture poisoning (unique `tmp_path` per test), and the dispatcher/engine startup loads also benefit.
- Import-time `DEFAULT_CONFIG_PATH` computed from `resolve_config_dir()`: rejected — breaks the `LLMAGENT_CONFIG_DIR` test override pattern used by `tests/conftest.py`.

## Implementation
### Target file
`scripts/shared/mcp_dedup.py`

### Procedure
Replace the CWD-relative default constant with a resolver-based lazy default, add the module-level config cache and clear seam, and pin the DB fallback convention with a comment; error types and the store class are untouched.

### Method
1. Import: add `from shared.runtime_paths import resolve_config_dir` to the existing `shared` import block (after `from shared.execution_snapshot import snapshot_json`, L25), respecting ruff `I` ordering.
2. Constants block (L29-32): delete `DEFAULT_CONFIG_PATH = Path("config/mcp_dedup.toml")` (L29). Keep `DEFAULT_DB_PATH = "/opt/llm/db/mcp_dedup.sqlite"` (L30) byte-identical; add a one-line comment naming the convention it mirrors (`workflow_db_path`/`eventbus_db_path` fallbacks in `scripts/db/config.py` L27-28; the shared-leaf contract forbids importing `scripts/db`, the same reason `execution_snapshot.py` keeps `_DB_PATH_DEFAULTS` as literals).
3. Add the cache: `_DEDUP_CONFIG_CACHE: dict[Path, DedupConfig] = {}` (new) as a module-level name after the constants block.
4. Add `_default_config_path() -> Path` (new): `return resolve_config_dir() / "mcp_dedup.toml"`; docstring states resolver precedence and lazy call-time resolution (`REQ-001`).
5. Rewrite the head of `load_dedup_config` (L69): signature becomes `def load_dedup_config(path: str | Path | None = None) -> DedupConfig:`; body computes `key = (_default_config_path() if path is None else Path(path)).expanduser().resolve()`, returns `_DEDUP_CONFIG_CACHE[key]` on a hit, otherwise runs today's parse/validation body unchanged against `key` (the error-message filename stays `Path(key).name`) and stores the result before returning. `ConfigMissingError` and `ConfigParseError` (raised at L75, L80, L84, L93-95, L104-117) propagate uncached (`REQ-002`, `REQ-004`).
6. Add `clear_dedup_config_cache() -> None` (new) after `load_dedup_config`: `_DEDUP_CONFIG_CACHE.clear()`; docstring names it the test/tooling seam and states production reload happens at restart (`REQ-005`).
7. No other edits: `DedupConfig` keeps `db_path: str = DEFAULT_DB_PATH` (L61-66); `retry_class` (L128-132) and `open_dedup_store` (L360-365) and the whole `DedupStore` class stay untouched.

### Details
- Update the module docstring (L5-7): the config file is located through the shared config-directory resolver and parsed once per process; the DB-file default wording stays valid.
- Callers unchanged and cache-transparent: `workflow_engine.py:163` (per turn), `dispatch.py:183` (startup, already memoized in `_dedup_context`), `tool_runner.py:177` (`retry_class` with no config, per tool call). All are confirmed no-change rows of the plan.
- Cache thread-safety: plain dict, written only on successful loads; a benign concurrent duplicate cold read is acceptable under the GIL and self-heals via the last write — no lock needed, matching the dispatcher's existing module-global memo pattern.
- `REQ-003` code delta is comment-only; the guarantee is enforced by the equality test in the Validation plan.

## Compatibility considerations
- No API break: no-arg `load_dedup_config()` keeps working; the signature widens (`path` now accepts `None`); all current call sites pass no argument (verified 20261108).
- Dev behavior: a `uv run` no-arg load previously depended on the process CWD; after the change it resolves the absolute repository-root `config/` — the same file today's services read, strictly more robust elsewhere (plan Risk 2: deploy verification compares the resolved path against the existing file on both trees before rollout).
- A config edit made while a service runs is invisible until restart (plan Risk 1) — the documented process-lifetime contract is row 2's doc edit; the seam remains available for tooling.
- Dispatcher and agent loading the same file through different spellings resolve to one cache entry because the key is the resolved absolute path (plan Risk 3).

## Security considerations
- No new sensitive data and no new file access: the resolver validates that an `LLMAGENT_CONFIG_DIR` override exists before use (`_assert_env_path`), and the config content and validation rules are unchanged.

## Rollback considerations
- Revert the commit; the module reverts to an uncached CWD-relative load with no persistent state to unwind (the cache is in-memory only).

## Validation plan
- New class `TestConfigResolutionAndCache` (new) in `tests/shared/test_mcp_dedup.py`, with an autouse fixture calling `clear_dedup_config_cache` (new) around each test:
  - `test_default_path_honors_llmagent_config_dir` (new): `monkeypatch` `LLMAGENT_CONFIG_DIR` to a tmp dir holding a minimal `[dedup]` file; `load_dedup_config()` finds it (`REQ-001`). Fails on HEAD (CWD-relative miss -> `ConfigMissingError`).
  - `test_explicit_path_still_loads` (new): explicit tmp-path loads behave as today (`REQ-001` compatibility).
  - `test_second_load_serves_cache_without_file` (new): load once, delete the file, load again — the cached `DedupConfig` returns with no `ConfigMissingError` (`REQ-002`). Fails on HEAD (second read observed).
  - `test_cache_clear_forces_reload` (new): load, rewrite the file with a different `retention_days`, call `clear_dedup_config_cache` (new), load again — the new value appears (`REQ-005`).
  - `test_missing_file_error_not_cached` (new): two calls against a missing file both raise `ConfigMissingError` (`REQ-004`).
  - `test_db_path_fallback_matches_convention` (new): a config without `db_path` yields `DedupConfig.db_path == DEFAULT_DB_PATH == "/opt/llm/db/mcp_dedup.sqlite"`, and its parent directory equals the parent of the `scripts/db/config.py` fallbacks (`REQ-003` equality test).
- Regression, unchanged: existing `TestConfigValidation` tests (`tests/shared/test_mcp_dedup.py` L215-272), the fail-open turn-control tests in `tests/agent/workflow/test_workflow_engine.py` (`build_turn_control_message` call sites, L707-765 region), and `tests/mcp_servers/test_mcp_dispatch.py`.
  - Amended 20261109 (first run): the resolver-based default made the conftest isolation config (a copy of `config/` with `/opt/llm/db` paths rewritten into the isolation root) loadable inside the test process, so `dispatch._dedup_context` enabled the durable store for `TestDispatchIdempotencyCache` and its four fixed-key overlay-only cases failed as durable store hits. Fix applied in the test file: that class's autouse fixture now explicitly sets `_dedup_store=None`, `_dedup_config=None`, `_dedup_disabled=True` via monkeypatch, keeping the overlay-only contract the class docstring and the plan Risks row require. Production behavior is unaffected: the change is test-fixture isolation, not a dispatch edit.
- Run `uv run pytest tests/shared/test_mcp_dedup.py tests/agent/workflow/ tests/mcp_servers/test_mcp_dispatch.py -q` after each phase; full `uv run pytest tests/ -q` before completion; lint/type gates per `rules/toolchain.md`.
- Post-deploy (plan Validation plan, executed at deploy time, not in this procedure): after restart, the agent log shows no dedup config errors and the dispatcher service starts cleanly.

## Completion criteria
- A no-arg load resolves `config/mcp_dedup.toml` under `resolve_config_dir()` (honors `LLMAGENT_CONFIG_DIR`) in dev, test, and compiled trees; the second load performs no filesystem access; the fallback DB path equals the production value; the typed-error and fail-open contracts still pass; the full suite is green.

## Out of Scope
- Dedup semantics (retention days, timeout values, retry classes) — plan Out-of-Scope.
- Async cold-read offloading (`anyio.to_thread`) — plan Out-of-Scope.
- The dispatcher's own startup consumption pattern beyond the shared loader (`dispatch.py` `_dedup_context`) — confirmed no-change.
- The docs location/caching contract statement (plan row 2 document `183007_02`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-100136 | 20261109-100136 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261109-100136 | 20261109-100136 | TestConfigResolutionAndCache added; TestDispatchIdempotencyCache fixture amended (see Validation plan amendment) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-100136 | 20261109-100136 | lint/type/import/bandit/gates + targeted tests pass; full suite at end of release unit full suite 11947 passed; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-100136 | 20261109-100136 | docs update is plan row 2's scope (`183007_02`) docs update delivered by 183007_02 (plan row 2); docs checkers pass |

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
- **Requirement ID**: `REQ-001` (resolver-based default path), `REQ-002` (one load per resolved path), `REQ-003` (fallback-literal DB convention), `REQ-004` (fail-open contract preserved), `REQ-005` (cache invalidation seam)
- **Source issue**: `issues/20261107-203224_wfaudit011_dedup-config-path-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084012_wfaudit011_dedup-config-path-boundary.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-183007
- **Related target files**: `scripts/shared/mcp_dedup.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-183007 -->