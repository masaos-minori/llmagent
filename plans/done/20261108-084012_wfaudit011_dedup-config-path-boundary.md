## Goal
Route `mcp_dedup` config through the project's shared config-directory resolver and cache its load: no CWD-relative default path, no fallback DB path outside the project's DB-path fallback-literal convention, and no synchronous TOML re-read on every turn.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/shared/mcp_dedup.py` — default config path resolved via `resolve_config_dir()` (`config/mcp_dedup.toml` under the resolver-managed directory); `DEFAULT_DB_PATH` fallback kept as the module literal matching the project's DB-path fallback-literal convention (no `[paths]` section exists in any `config/*.toml` — verified 20261108 against HEAD `ad48bfa28`, see Notes); module-level cached load keyed by resolved absolute path (invalidatable for tests).
  - Tests: resolver-path behavior (`LLMAGENT_CONFIG_DIR` honored), cache behavior (second call performs no file read), fail-open contract preserved.
  - Docs: dedup config location and caching contract (`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`). Deployment docs verified to contain no `mcp_dedup` location statements (20261108) — no deployment-doc edit in scope.
- **Out-of-Scope**:
  - Changing dedup semantics (retention days, timeout values, retry classes).
  - Async file reading (`anyio.to_thread`) — caching removes the per-turn hot-path read, which is the issue; making the cold read async is not needed.
  - The dispatcher's own startup config consumption pattern beyond the shared loader (`scripts/mcp_servers/dispatch.py:183` benefits from the same cache automatically).
- **Dependencies**: None blocking. Independent of the recovery/status cluster.

## Background
`scripts/shared/mcp_dedup.py:29-30` hardcodes `DEFAULT_CONFIG_PATH = Path("config/mcp_dedup.toml")` (CWD-relative) and `DEFAULT_DB_PATH = "/opt/llm/db/mcp_dedup.sqlite"`, while every other config consumer resolves through `resolve_config_dir()` / `LLMAGENT_CONFIG_DIR` (`scripts/shared/config_loader.py:75`, `scripts/shared/execution_snapshot.py:159`, `scripts/shared/runtime_paths.py:51`). `WorkflowEngine.build_turn_control_message` (sync `def`, L148) calls `load_dedup_config()` per turn-execution attempt (`workflow_engine.py:165`) — a blocking TOML parse + file read on the turn path (called from the async turn flow; corrected mechanism in validation). Today it works only because services start at the production root (both `config/mcp_dedup.toml` and `/opt/llm/config/mcp_dedup.toml` exist). The engine's per-turn catch (L164-173: `try` L164, call L165, `except Exception` L167, `return None` L173) already degrades on config errors. Verified in the issue's `## Adversarial Validation`.

## Problem
A config consumer outside the resolver convention silently depends on the process CWD; any launch from a different directory turns every turn's dedup classification into a `ConfigMissingError` (degraded, logged, no control message). And the hot path re-parses the same TOML every turn.

## Reason for Change
Every other config path in the project flows through the resolver; this is the last outlier (issue's census). Caching converts an N-times-per-session file read into one, and the resolver move makes the config location an environment fact rather than a launch-directory accident.

## Implementation Intent
Resolve the default path once via `resolve_config_dir()`; read and parse once per resolved path via a module-level cache; keep the DB-path fallback as the module literal matching the project's per-service `db_path` + fallback-literal convention; keep every existing error type and the fail-open turn contract unchanged.

## Requirements
- `REQ-001`: `load_dedup_config()` with no explicit path resolves `config/mcp_dedup.toml` under `resolve_config_dir()` (honors `LLMAGENT_CONFIG_DIR`); explicit-path callers keep working unchanged.
- `REQ-002`: A successful load for a resolved path is cached; subsequent calls return the cached `DedupConfig` without touching the filesystem (test proves via file deletion/mtime change after first load).
- `REQ-003`: The DB-path default follows the project's DB-path convention: the service's own config key (`dedup.db_path`, already read at `mcp_dedup.py:86`) overrides, and the module fallback literal `DEFAULT_DB_PATH = "/opt/llm/db/mcp_dedup.sqlite"` matches the `DbConfig` fallback-literal pattern (`scripts/db/config.py:27-28`, `:72-73`). No `[paths]` section exists in this project (verified 20261108; see Notes); fallback behavior matches today's production path value (no new failure mode).
- `REQ-004`: Error contract unchanged: missing file -> `ConfigMissingError`, bad values -> `ConfigParseError` (typed errors preserved), and a failed load on the turn path still degrades per the documented catch (`workflow_engine.py:164-173`).
- `REQ-005`: A cache-invalidation seam exists for tests (explicit-path loads bypass the cache, or a `clear_dedup_config_cache()` helper); tests pin `REQ-001`-`REQ-004`.

## Implementation Target Files
**Freeze status**: Frozen (revalidated 20261108 against HEAD `ad48bfa28` per this pass — see Notes; two `Reference` rows demoted to the Reference Files table after no-change verification; line citations and the DB-path convention wording corrected; both remaining rows `Verified`)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/mcp_dedup.py` | Modify | Resolver-based default config path (L29); `DEFAULT_DB_PATH` fallback convention pinned (L30); module-level cache with invalidation seam | `REQ-001`-`REQ-003`/`REQ-005` | Hardcoded constants verified (L29-30, re-verified 20261108) | `tests/shared/test_mcp_dedup.py` | `Verified` |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Config-location and caching contract statement | `REQ-001`/`REQ-002` | Doc covers the dedup store (L43-44, L69-71, re-verified 20261108) | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/runtime_paths.py` | `resolve_config_dir` semantics (`LLMAGENT_CONFIG_DIR`, compiled-adjacent `config/`, legacy repo-root `config/`; L51-66) — must match other consumers exactly | `REQ-001` |
| `scripts/shared/config_loader.py` | `resolve_config_dir` usage pattern (L75) the dedup loader must match; the module contains no `[paths]` handling (verified 20261108) | `REQ-001` |
| `scripts/db/config.py` | DB-path fallback-literal convention (`workflow_db_path`/`eventbus_db_path` defaults L27-28, builder L70-73) that `DEFAULT_DB_PATH` mirrors; read-only reference (the shared-leaf import contract forbids `scripts/shared` importing `scripts/db`) | `REQ-003` |
| `scripts/agent/workflow/workflow_engine.py` (L148-173) | Confirmed no-change (verification 20261108): call site L165 unchanged in shape (still `load_dedup_config()`, now hitting the cache); the fail-open contract (catch L164-173) the change must preserve | `REQ-004` |
| `scripts/mcp_servers/dispatch.py` (L175-195) | Confirmed no-change (verification 20261108): L183 startup-time load already memoized in module globals; benefits from the shared cache, no contract change | `REQ-002` |
| `scripts/agent/tool_runner.py` (L174) | Confirmed no-change (verification 20261108): `retry_class(pc.name)` with no config loads per tool call and benefits from the cache automatically; no edit required | `REQ-002` |
| `config/mcp_dedup.toml` + `/opt/llm/config/mcp_dedup.toml` | Verify both trees resolve identically after the move (both files confirmed present 20261108) | Validation plan |

## Acceptance Criteria
- `REQ-001`: Test with `LLMAGENT_CONFIG_DIR` pointed at a tmp config dir: `load_dedup_config()` finds the file there; on HEAD the CWD-relative default would miss it.
- `REQ-002`: After the first successful load, deleting the config file and calling again returns the cached config (no `ConfigMissingError`).
- `REQ-003`: DB path resolution: the `dedup.db_path` configured value is used (existing behavior, pinned by test); the absent-key fallback equals the production value, and a test asserts `DEFAULT_DB_PATH == "/opt/llm/db/mcp_dedup.sqlite"` and its parent directory matches the other databases' fallback directory convention.
- `REQ-004`: Turn-control degradation test: a broken config on the turn path logs and proceeds (existing behavior preserved).
- `REQ-005`: Full `tests/shared/ tests/agent/workflow/` green; no config value semantics changed.

## Tests
- Resolver-honor test (env var), explicit-path bypass test.
- Cache hit/invalidation tests (seam-driven).
- Regression: existing dedup config value tests unchanged; engine turn-control fail-open tests unchanged.

## Documentation Impact
- `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` — config path resolution + one-load-per-process contract.
- `docs/90_deployment` checked 20261108: contains no `mcp_dedup` or `config/mcp_dedup.toml` location statements — no deployment-doc edit needed.
- Run docs checkers for domains db/deployment as applicable per `routing.md`.

## Assumptions
- Config file location in both dev and production trees is already the resolver-managed directory (`resolve_config_dir()` default resolves to the production config dir the same way other consumers use it — verified: both files exist at `config/` under repo root and `/opt/llm/config/`).
- A process-lifetime cache is acceptable: config changes require a service restart, matching every other config consumer in the project.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether the `[paths]` section currently has (or should gain) a dedicated key for the dedup DB, or reuse of the existing db-dir key | config schema decision | RESOLVED 20261108 by inspection: no `[paths]` section exists in any `config/*.toml` (or anywhere in `scripts/`/`docs/`); the project convention is a per-service `db_path` config key plus a module fallback literal (`/opt/llm/db/<name>.sqlite`, `scripts/db/config.py:27-28`). The existing `dedup.db_path` key is reused; `DEFAULT_DB_PATH` stays the matching literal | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/mcp_dedup.py` | Modify | agent turn path + dispatcher service | 1 | N/A | not applicable (rsynced) |
| docs (1-2 files) | Modify | docs only | N/A | N/A | not applicable |

## Design
**Resolve once, cache per resolved path.** `load_dedup_config(path=None)` resolves the default via `resolve_config_dir()` only when no explicit path is passed; a module-level `dict[Path, DedupConfig]` caches results. Explicit-path calls (tests) bypass or key separately — no cache-poisoning between test fixtures. Invalidation seam: a `clear_dedup_config_cache()` function (chosen over mtime checks: simpler, and restart-based reload matches project convention).

**DB path fallback convention.** `DEFAULT_DB_PATH` stays the literal `/opt/llm/db/mcp_dedup.sqlite` — the same fallback-literal shape `scripts/db/config.py` uses for the other databases (`UNK-01` resolved: no `[paths]` section exists in this project); `dedup.db_path` in `config/mcp_dedup.toml` already overrides it (L86), so no deployed database path changes and no new config wiring or failure mode is introduced. The Phase 2 deliverable is the equality test that pins the fallback against the convention.

**Fail-open preserved.** No exception-type changes: the engine catch (L166-170) keeps degrading on config failure; the cache only removes repeat reads, it does not swallow first-load errors.

## Implementation steps
1. **Phase 1: Resolver + cache (`REQ-001`, `REQ-002`, `REQ-005`).** Path resolution, cache + seam, tests.
2. **Phase 2: DB-path convention (`REQ-003`).** Fallback-literal convention pinned by the equality test (no config wiring change; `dedup.db_path` is already read).
3. **Phase 3: Docs.** Location/caching contract; docs checkers.

### Release units
**Unit**: wfaudit011-full | **Phases**: 1, 2, 3 | **Reason**: path resolution and caching are the same loader change; docs mirror it.

## Validation plan
- `uv run pytest tests/shared/ tests/agent/workflow/ -q` after each phase; full `uv run pytest tests/ -q` before completion.
- New resolver test fails on HEAD (CWD-relative miss), cache test fails on HEAD (second read observed).
- Deploy check: after restart, agent log shows no dedup config errors; dispatcher service starts cleanly.
- Lint/type gates per `rules/toolchain.md`; docs checkers after Phase 3.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cache hides a config edit made while the service runs | Medium | Low (restart required — matches project convention) | Documented contract in docs row; seam available for tooling |
| Resolver default resolves to a different directory than today's CWD-relative default on some launch path | Low | Medium (missing config -> degraded turns, logged) | Deploy verification step compares resolved path against the existing file on both trees before rollout |
| Dispatcher and agent cache the same file with different explicit paths | Low | Low | Cache keyed by resolved absolute path |

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: resolver + cache | In Progress | — | — |  |
| 2 | Phase 2: DB-path convention | In Progress | — | — |  |
| 3 | Phase 3: docs | In Progress | — | — |  |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261108-183007_01_scripts_shared_mcp_dedup.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261108-183007_02_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203224_wfaudit011_dedup-config-path-boundary.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084012
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem (CWD-relative path) | `scripts/shared/mcp_dedup.py` | resolver honored | env-var test |
| `REQ-002` | Issue Problem (per-turn re-read) | same | one load per path | cache tests |
| `REQ-003` | Issue Problem (hardcoded DB path) | same | fallback-literal convention | equality test |
| `REQ-004` | Issue constraint (fail-open) | engine contract preserved | degradation unchanged | regression tests |
| `REQ-005` | Issue Testing Expectations | tests | fail on HEAD | pytest |

## Notes
- Source verified against HEAD `926dbc109`; the `async def` mechanism in the issue was corrected during validation (sync `def` called from async turn flow — see the issue's `## Adversarial Validation`).
- 20261108 procedure-pass re-verification against HEAD `ad48bfa28` (Step 3a corrections):
  - Engine catch line range corrected: `L166-170` -> `L164-173` (`try` L164, `load_dedup_config()` call L165, `except Exception` L167-172, `return None` L173). Call-site L165 itself confirmed unchanged.
  - No `[paths]` config section exists anywhere in `config/*.toml`, `scripts/`, or `docs/` (verified 20261108). The plan's "DB-path via `[paths]` convention" mechanism was a misnomer; the real convention is a per-service `db_path` config key plus a module fallback literal (`scripts/db/config.py:27-28`, `:72-73`; `scripts/shared/execution_snapshot.py` `_DB_PATH_KEYS`/`_DB_PATH_DEFAULTS` L50-61). REQ-003, Acceptance Criteria, Design, Phase 2, and Requirement Traceability reworded accordingly; `UNK-01` resolved by this inspection (reuse `dedup.db_path`; `DEFAULT_DB_PATH` literal unchanged — no deployed path changes).
  - Two `Reference` rows (`scripts/agent/workflow/workflow_engine.py`, `scripts/mcp_servers/dispatch.py`) demoted from Implementation Target Files to Reference Files with no-change confirmations, so no procedure document is generated for them. `scripts/agent/tool_runner.py:174` (`retry_class(pc.name)` with no config, a per-tool-call `load_dedup_config()` beneficiary) and `scripts/db/config.py` added as confirmed no-change / read-only references.
  - `docs/90_deployment/` verified to contain no `mcp_dedup` mentions (grep 20261108) — the "deployment docs config-mirroring note" scope item is satisfied by a no-edit confirmation.
  - `tests/conftest.py` sets `LLMAGENT_CONFIG_DIR` to an isolated temp config dir for the whole suite, so resolver-honor tests use `monkeypatch` on a per-test tmp dir and cache-seam teardown; `DEFAULT_CONFIG_PATH` has no external consumers (`rg` verified 20261108: referenced only inside `scripts/shared/mcp_dedup.py`), so removing it is safe.
  - Overlap check `tools/check_plan_target_overlaps.py`: No findings. Dependency order `tools/plan_dependency_order.py`: this Plan `ready`, not gated.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-183007 -->