# Plan 007: Retention input validation and consistent timestamp cutoff

## Goal
- Make every retention/prune input validated at the boundary (negative rejected, `0` = rule disabled, bool/float/string rejected), compare age cutoffs in the one format the stored timestamps use (`%Y-%m-%dT%H:%M:%SZ`), and make the count-rule tie order deterministic.

## Priority
Medium (Issue Priority)

## Scope
- **In-Scope**: retention/limit value validation in the two retention `from_config` methods and the four purge helpers; `get_typed` bool rejection; `int()`-coercion replacement in `maintenance.py` and `config.py`; cutoff-format alignment in the six retention queries; `older_than_days` negative guard in the memory delete store; tie-breaker ordering; boundary tests; harness alignment to the production timestamp format in tests.
- **Out-of-Scope**: error-mode/transaction semantics (issue 006, `plans/20261115-050112_dbreview006_maintenance-error-semantics.md`, lands first); archive retention coverage gaps (issue 008); `scripts/agent/memory/count_ops.py:45` — the same `datetime('now', ?)` format mismatch exists in the agent-layer memory count query; it is outside this Issue's target files and is recorded as a follow-up candidate, not edited here. Changing default retention numbers (Issue Constraint).
- **Dependencies**: plans/20261115-050112_dbreview006_maintenance-error-semantics.md | phase all | sequencing only: 006 wraps the purge/prune flow in `begin_immediate` and changes failure `data`; 007 then edits the same functions' guards and SQL. 007's Phase 1 re-reads 006's landed code shape. No behavioral dependency, but 006's new rollback tests must stay green after 007's SQL rewrite (Phase 3 runs them).

## Background
From the Source Issue (F-007, written at commit `0fe68d3`), re-verified against the post-pull tree (HEAD `edc79f698`, 2026-11-15):

Adversarial re-verification 2026-11-16 (HEAD `8fc337615`): all "Claims that hold" re-confirmed against current source (no-guard behavior, `f"--5 days"` NULL no-op, `T/Z` vs space format mismatch at the six query sites, bare `int()` at the four `from_config` lines and `config.py:77-78`, `isinstance(True, int)` in `get_typed`, `ORDER BY created_at DESC` alone). Line-number citations corrected to current positions (`helper guards :172-173`→`:175`/`:304`, `_delete_sessions_beyond_limit :208-241`→`:206-240`, `ORDER BY :217`→`:216`, `get_typed :51-72`→`:54-76`, `_make_session_db :40-101`→ DDL `:40,48` + function `:93-101`); test count 57→58. Referenced test patterns all exist: `test_boundary_below/at/above_max_sessions` (`:189-215`), `ConfigLoader.load` monkeypatch (`:365`), `test_sqlite_helper.py` config-validation pattern (`:378-419`), `tests/shared/test_config_utils.py` contains only 5 `get_str` tests, `config/agent.toml:11-18` native TOML ints, `memory_data_ops.py:134-145` `--days >= 1` validation, `production_config_validator.py` lists the four retention keys, `git_models.py:25-43` local `_optional_real` untouched, docs `db_06` retention paragraphs at `:32`/`:42`. No contradicting findings.

Claims that hold:
- `_delete_sessions_beyond_limit` (`scripts/db/maintenance.py:206-240`) has no guard: `max_sessions=0` deletes every session (except the exempted one); `max_sessions=-1` slices `rows[-1:]` and deletes only the oldest row. Same shape in `_delete_corrupt_archives_beyond_limit` (`:321-342`): `max_files=0` deletes all archives. The two age helpers guard `<= 0` (`:175`, `:304`); negative age values currently disable the rule silently.
- Negative `older_than_days` in `SQLiteMemoryDeleteStore.delete_memories_before`/`collect_prunable_ids` (`scripts/db/store_impl.py:177-214`, no guard) builds `f"--5 days"`, `datetime()` returns NULL, and the delete silently no-ops (confirmed live in Step 2).
- Format mismatch confirmed live: stored defaults are `strftime('%Y-%m-%dT%H:%M:%SZ','now')` (`scripts/db/schema_sql.py:91,102,120-121,177-178`), while the cutoffs are `datetime('now', ?)` producing `YYYY-MM-DD HH:MM:SS` (space). Lexicographically `'...T...Z' < '... ...'` is false for same-cutoff-day rows, so retention is off by up to one day. Six affected queries: `maintenance.py:179,191,195` and `store_impl.py:182,192,211`.
- Bare `int(cfg.get(...))` coercion at `maintenance.py:112-113,132-133` and `config.py:77-78` accepts bools (`int(True)=1`) and truncates floats; `get_typed` (`scripts/shared/config_utils.py:54-76`) now raises on type mismatch but bool still passes `isinstance(True, int)`. `rules/coding.md` type-coercion policy prohibits the bare `int()`.
- `_delete_sessions_beyond_limit` orders by `created_at DESC` alone (`:216`); ties resolve in unspecified order.

Claims retired by upstream work (post-pull tree): `get_typed` silent-default-on-type-mismatch (now raises `ValueError`); empty `sqlite_path`/`sqlite_vec_so` validation (implemented at `config.py:36-42,52,66-69`); `_parse_since` naive-datetime parsing (module gone — the store API takes an `int` `older_than_days`); the `scripts/utils` architecture-orphan question (the package no longer exists; `shared/config_utils.py` is a contract-consistent shared-layer leaf).

Maintainer decision (2026-11-15 question, recorded): **`0` disables the rule (symmetric with the documented `max_age_days=0` semantics); negative values are rejected with `ValueError`.**

## Problem
A destructive delete whose scope depends on an unchecked integer and a mismatched date format deletes far more (all sessions/archives) or less (nothing, or only same-timestamp ties picked arbitrarily) than configured, with no diagnostic.

## Reason for Change
Retention deletes are irreversible; the configured number and the configured age window must mean exactly what the config says, and the result counts must be trustworthy (Issue: "Reason for Change").

## Implementation Intent
Validate at both boundaries: config load (`from_config`, `build_db_config`) via `get_typed` with explicit bool rejection plus a non-negative check, and the purge/prune helpers as the second line. Rewrite the six cutoff expressions to `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)` so both sides of every comparison use the stored format. Add `session_id DESC` as the ordering tie-breaker.

## Requirements
- `REQ-001` (AC-1): `RetentionConfig.from_config` and `CorruptArchiveRetentionConfig.from_config` reject negative values (`ValueError` naming the key); `0` is accepted and means "this rule is disabled"; the four purge helpers enforce the same contract for directly constructed configs (`== 0` disables, `< 0` raises `ValueError`). Maintainer semantics recorded in the dataclass docstrings.
- `REQ-002` (AC-3): `get_typed` rejects `bool` when `expected_type` is `int` or `float` (before the `isinstance` check), with the message naming the got-type `bool`; docstring updated. `bool` remains valid for `expected_type=bool`.
- `REQ-003` (AC-3): replace `int(cfg.get(...))` at `maintenance.py:112-113,132-133` and `config.py:77-78` with `shared.config_utils.get_typed(d, key, int, "an integer", default)`; bool, float, and string values are rejected (string acceptance via `int("100")` is removed — in-repo configs use native TOML ints, verified Step 2: `config/agent.toml:11-18`).
- `REQ-004` (AC-2): the six cutoff queries compare against `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)` — `maintenance.py:179,191,195` and `store_impl.py:182,192,211`; stored data format is untouched (Issue Constraint). A row older than the cutoff by one second is deleted regardless of the time of day.
- `REQ-005` (AC-1): `delete_memories_before` and `collect_prunable_ids` raise `ValueError` for negative `older_than_days` (`0` stays meaningful: cutoff = now). `memory_prune` already requires `--days >= 1` (`scripts/agent/commands/memory_data_ops.py:134-145`), so this guard protects direct/API callers.
- `REQ-006` (AC-4): `_delete_sessions_beyond_limit` orders `created_at DESC, session_id DESC` so tie groups resolve deterministically (lowest `session_id` deleted first).
- `REQ-007` (AC-1..AC-4): boundary tests in `tests/db/test_db_maintenance.py`, `tests/db/test_db_store_impl.py`, `tests/shared/test_config_utils.py`; the maintenance test harness `_make_session_db` is aligned to the production `T/Z` timestamp format so retention tests exercise the production comparison.

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8: every row exists, requires modification, has supporting evidence recorded this cycle, and links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/maintenance.py | Modify | Validated `from_config` parsing (REQ-001, REQ-003); helper guards `==0` disable / `<0` raise in the four purge helpers (REQ-001); cutoff rewrite in 3 queries (REQ-004); tie-breaker at `:216` (REQ-006) | REQ-001, REQ-003, REQ-004, REQ-006 / AC-1..AC-4 | `:112-113`, `:132-133`, `:175`, `:179`, `:191`, `:195`, `:206-240` (no guard), `:216`, `:304`, `:321-342` (checked Step 2, post-pull; line refs re-confirmed 2026-11-16) | tests/db/test_db_maintenance.py | Verified |
| scripts/db/store_impl.py | Modify | Negative-`older_than_days` guard in `delete_memories_before`/`collect_prunable_ids`; cutoff rewrite in 3 queries | REQ-004, REQ-005 / AC-1, AC-2 | `:177-214` no guard; `datetime('now', ?)` at `:182,192,211`; `f"--5 days"` NULL behavior confirmed live (Step 2) | `tests/db/test_db_store_impl.py` | Verified |
| scripts/shared/config_utils.py | Modify | `get_typed` bool rejection for `int`/`float` expected types + docstring | REQ-002 / AC-3 | `:54-76` `isinstance(True, int)` passes (checked Step 2) | `tests/shared/test_config_utils.py` | Verified |
| scripts/db/config.py | Modify | `build_db_config`: `get_typed` for `sqlite_timeout`/`sqlite_busy_timeout_ms` instead of bare `int()` | REQ-003 / AC-3 | `:77-78` bare `int(cfg.get(...))` (checked Step 2) | tests/db/test_sqlite_helper.py (existing config-validation tests `:378-419` pattern) | Verified |
| tests/db/test_db_maintenance.py | Modify | Boundary/negative/bool tests for both configs and both rules; cutoff-day 1-second regression test; tie-order test; align `_make_session_db` (`:93-101`; harness DDL `:40,48`) to the production `T/Z` format | REQ-007 / AC-1..AC-4 | 58 tests; zero/negative count-key coverage absent (grep this cycle); harness seeds space-format literals (`:146-163`) — mismatch invisible today | tests/db/test_db_maintenance.py | Verified |
| tests/db/test_db_store_impl.py | Modify | Negative-days `ValueError` tests; `days=0` cutoff-boundary test (older/newer rows) | REQ-007 / AC-1, AC-2 | Existing delete tests use `days=30/7` (`:401-627`); no negative or `days=0` case (grep this cycle) | tests/db/test_db_store_impl.py | Verified |
| tests/shared/test_config_utils.py | Modify | Add `get_typed` test class: bool rejected for int/float, bool accepted for bool, non-matching types raise | REQ-002, REQ-007 / AC-3 | File contains only 5 `get_str` tests (read this cycle) | tests/shared/test_config_utils.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/schema_sql.py `:91-209` | Single source for the stored timestamp format `strftime('%Y-%m-%dT%H:%M:%SZ','now')` the cutoffs must match; **no edit required** (Issue Constraint: stored data keeps its format) | scripts/db/store_impl.py / REQ-004 |
| plans/20261115-050112_dbreview006_maintenance-error-semantics.md | Lands first: `purge_old_sessions` `begin_immediate` wrap, failure `data` shape, and the new rollback tests 007 must keep green while rewriting the queries inside them | scripts/db/maintenance.py / REQ-001, REQ-004 |
| scripts/agent/commands/memory_data_ops.py `:134-145,360-373` | `memory_prune`'s `--days >= 1` validation and its dry-run `collect_prunable_ids` usage — the store guard must not break this consumer | scripts/db/store_impl.py / REQ-005 |
| scripts/agent/production_config_validator.py `:192-195` | Lists the four retention keys as known keys only (no value validation there); confirms config-load is the right validation point | scripts/db/maintenance.py / REQ-001 |
| scripts/mcp_servers/git/git_models.py `:25-43` | `_optional_real` deliberately avoids changing `get_typed` ("left untouched" comment) — records that REQ-002 hardens a shared helper its author knew about; local helper stays as-is (scope rule) | scripts/shared/config_utils.py / REQ-002 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-005`, `REQ-007`): Negative `max_sessions`, `max_age_days`, `max_files`, corrupt-archive `max_age_days`, or `older_than_days` raise `ValueError` with a key-naming message (config path and helper/store path); `0` disables the corresponding rule and deletes nothing (sessions/archives) or means cutoff=now for memories.
- AC-2 (`REQ-004`, `REQ-007`): A `T/Z`-stamped row older than the cutoff by one second is deleted by the age rule and by `delete_memories_before(0)`; a row one second inside the cutoff survives — regardless of time of day.
- AC-3 (`REQ-002`, `REQ-003`, `REQ-007`): `True`/`12.5`/`"100"` for `sqlite_retention_max_sessions` (and the other three keys, plus `sqlite_timeout`/`sqlite_busy_timeout_ms`) raise `ValueError` at config load; `get_typed` rejects bool for `int`/`float` and still accepts bool for `bool`.
- AC-4 (`REQ-006`, `REQ-007`): With equal `created_at` ties, the kept/deleted sets are deterministic (lowest `session_id` deleted first) across repeated runs.

## Tests
- `REQ-001/REQ-003` (AC-1, AC-3) in `tests/db/test_db_maintenance.py` (monkeypatch `db.maintenance.ConfigLoader.load`, pattern of `:365`): negative/bool/float/string for each of the four keys → `ValueError` naming the key; `0` values load cleanly and the corresponding rule deletes nothing (`max_sessions=0` with expired-by-count sessions keeps all; `max_files=0` keeps all archives; `max_age_days=0` stays disabled as today).
- `REQ-001` helper path (AC-1): directly constructed `RetentionConfig(max_sessions=-1, max_age_days=0)` and `CorruptArchiveRetentionConfig(max_files=-1, ...)` → `purge_old_sessions` / `purge_corrupt_archives` raise `ValueError` in both modes (validation precedes the mode handler).
- `REQ-004` (AC-2) in `tests/db/test_db_maintenance.py`: with the aligned `T/Z` harness, seed a session stamped 5 seconds past the cutoff (`utcnow - 1 day - 5 s`) and one 5 seconds inside it; `max_age_days=1` → exactly the past-cutoff row deleted (margin > test duration; the Issue's "one second" contract is exercised by the same mechanism). In `tests/db/test_db_store_impl.py`: `delete_memories_before(0)` with rows stamped `utcnow - 5 s` and `utcnow + 5 s` → older deleted, newer kept.
- `REQ-005` (AC-1): `delete_memories_before(-1)` and `collect_prunable_ids(-1)` raise `ValueError`; existing `days=30/7` delete tests (`:401-627`) stay green.
- `REQ-006` (AC-4): seed 5 sessions with one identical `created_at` and `max_sessions=2`; assert the exact kept set (`session_id` 4,5 kept; 1-3 deleted) and repeat twice for determinism.
- `REQ-002/REQ-007` (AC-3) in `tests/shared/test_config_utils.py`: `get_typed({"k": True}, "k", int, "an integer")` raises `ValueError` matching `bool`; float-for-int and str-for-int already raise — keep pinned; bool for `expected_type=bool` passes through.
- Regression watch: `tests/db/test_sqlite_helper.py:378-419` (config validation) stays green; Plan 006's rollback/atomicity tests (`tests/db/test_db_maintenance.py`) re-run after the SQL rewrite (Dependencies); Plan 004's rotation-invariance tests in the same file re-run (they do not touch cutoff SQL); `test_boundary_below/at/above_max_sessions` (`:189-215`) stay green under the new tie-breaker (distinct `created_at` seeds).

## Documentation Impact
- `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`: update the retention paragraph (`:32`, `:42`) — `0` disables the rule for all four keys (not only the age limits), negative values raise `ValueError`, bool/float/string config values are rejected at load, and cutoffs compare in the stored `T/Z` format. Issue Documentation Impact: "document the accepted range and meaning of `0` ... where they are described" — this file is where they are described. No other doc describes these keys (grep this cycle).

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC targets | `store_impl.py` top `delete_memories_before` B(7); `maintenance.py` top `_delete_sessions_beyond_limit` B(7), `purge_old_sessions` B(6); `config_utils.py` top A | `uv run radon cc scripts/db/store_impl.py scripts/shared/config_utils.py scripts/db/config.py -s` + Plan 006 recording (run this cycle) | 2026-11-15 |
| vulture targets | No `scripts/db` findings | `uv run vulture scripts/db --min-confidence 80` (run this cycle) | 2026-11-15 |
| bandit targets | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (run this cycle, recorded under Plan 005; tree unchanged) | 2026-11-15 |
| coverage targets | project total 95%; tree clean at recording | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (recorded under Plan 005; tree unchanged) | 2026-11-15 |
| operational check | no process holds `/opt/llm/db/rag.sqlite` or `/opt/llm/db/session.sqlite` (`fuser` empty, exit 1); dev-host only | `fuser /opt/llm/db/rag.sqlite /opt/llm/db/session.sqlite` (recorded under Plan 002 Step 3; re-run before implementation) | 2026-11-15 |

## Assumptions
- Production rows are stamped in the `T/Z` format by schema defaults (`schema_sql.py:91-209`); historical rows may predate that default — the lexicographic comparison stays correct for `YYYY-MM-DD`-prefixed values in either format except at the space-vs-`T` boundary, which the fix removes (checked Step 2).
- In-repo `agent.toml` values for all six keys are native TOML integers (`config/agent.toml:11-18`, `config/crawler.toml:9,12`, `config/ingester.toml:12,15`, `config/rag_pipeline_mcp_server.toml:19,22` — read this cycle), so removing string acceptance via `int("...")` affects no shipped config.
- `get_typed` hardening is safe for its current consumers: mcp_servers `int`-expected call sites (`web_search`, `file` models) currently pass TOML-typed ints; a bool there would now fail closed at server config load — intended fail-closed behavior.
- A 5-second test margin is sufficient to prove the one-second contract deterministically (SQL `now` and Python `utcnow` are both UTC; test execution is sub-second).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any deployed host has a `T/Z`-vs-space mixed `sessions` table with rows exactly on a cutoff day (upstream data written before the schema default existed) | Cannot inspect production DBs from this dev host (`fuser` check: no live process) | Behavior change is strictly "delete up to one day more correctly"; flagged in Risks; operator confirmation at deployment | False |
| UNK-02 | Whether `scripts/agent/memory/count_ops.py:45` (same mismatch, agent layer) should join the fix | Outside this Issue's target files | Recorded as follow-up candidate; file an issue after 007 lands if the maintainer wants the same contract for counts | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/maintenance.py | Modify | Medium (agent/rag maintenance services, agent purge command) | 2 | High (single author, >70%) | not applicable (rsynced) |
| scripts/db/store_impl.py | Modify | Medium (`memory_prune` command, maintenance prune) | 2 | High (single author, >70%) | not applicable (rsynced) |
| scripts/shared/config_utils.py | Modify | Medium (eventbus + 9 mcp_servers consumers of `get_typed`/`get_str`) | 0 | High (single author, >70%) | not applicable (rsynced) |
| scripts/db/config.py | Modify | Medium (every DB-config consumer) | 2 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_db_maintenance.py | Modify | Low (test-only) | 5 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_db_store_impl.py | Modify | Low (test-only) | 2 | High (single author, >70%) | not applicable (rsynced) |
| tests/shared/test_config_utils.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |

## Cross-Plan Target Overlap Scan

- Re-run with all plans frozen so far (`tools/check_plan_target_overlaps.py`, 2026-11-15, after this Plan freezes): findings — `scripts/db/maintenance.py` (006+007), `scripts/db/store_impl.py` (006+007), `tests/db/test_db_maintenance.py` (004+006+007). Judgment: **sequencing** — fixed batch order 004 → 006 → 007 (008 last). 006 edits the mode/transaction flow of `purge_old_sessions`/`prune_old_memories`; 007 adds guards at the top of the same functions and rewrites the cutoff expressions inside them — 007's Phase 1 re-reads 006's landed shapes, and 007 Phase 3 re-runs 006's rollback tests (Dependencies). In `tests/db/test_db_maintenance.py`, 004 adds rotation-invariance tests, 006 mode/transaction tests, 007 validation/boundary tests — disjoint test classes; 007 also aligns the shared `_make_session_db` harness (`:40-101`), which 004's and 006's session tests also use: the alignment (space → `T/Z`) is verified not to change their seeded-comparison outcomes (year/month differing positions precede the format byte; Phase 3 runs the whole file). No plan contradicts another's semantics.
- Update after Plan 008 froze (same tool, 2026-11-15): `scripts/db/maintenance.py` now 3 plans (006+007+008), `scripts/db/config.py` now 2 plans (007+008), `tests/db/test_db_maintenance.py` now 4 plans (004+006+007+008). Judgment: **disjoint regions** — 008's `ArtifactRetentionConfig.from_config` reuses 007's landed `get_typed` semantics (0=disabled, negative/bool rejected) rather than editing them; `resolve_unique_path` is a new symbol beside `format_timestamp`, untouched by 007's `build_db_config` edit. 008 is last in the fixed batch order 001→008; no contradiction.

## Design
- **Two-boundary validation**: `from_config` methods reject negatives (so a broken `agent.toml` fails at load with the key named), and the four helpers (`_delete_sessions_by_age`, `_delete_sessions_beyond_limit`, `_delete_corrupt_archives_by_age`, `_delete_corrupt_archives_beyond_limit`) enforce `== 0 → disabled`, `< 0 → ValueError` for directly constructed configs. Rejected alternative: validation in `RetentionConfig.__post_init__` only — the frozen dataclasses are constructed directly by many existing tests and callers; helpers must not be reachable with invalid values either way, and the helper guard is where deletion actually happens.
- **Semantics table (maintainer decision 2026-11-15)**: `0` = the rule is disabled (symmetric with today's documented `max_age_days=0`); negative = rejected. `older_than_days` in the memory store is different: there is no "disabled" concept — `0` means cutoff=now (today's documented prune semantics), negative raises.
- **`get_typed` bool rejection before isinstance**: `if expected_type in (int, float) and isinstance(value, bool): raise ValueError(f"'{key}' must be {type_label}, got bool: {value!r}")`. Issue AI Instruction honored: no new coercion mechanism — the existing helper is hardened and reused by `maintenance.py`/`config.py` (`db → shared` is a legal import edge per `rules/env.md` Architecture).
- **Cutoff expression rewrite**: inline `strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?)` with the unchanged `f"-{n} days"` parameter — Issue Required Change ("`strftime(...)` or an equivalent consistent format") applied at exactly the six verified sites; inline chosen over a shared SQL constant module because the queries are hand-written strings in two files and an indirection would obscure them from grep (Issue Constraint: stored data unchanged; only the right-hand side moves).
- **Tie-breaker**: `ORDER BY created_at DESC, session_id DESC` — newest-first, and within equal timestamps the highest ids are kept, lowest deleted; documented in the helper docstring so the count-rule outcome is reproducible (AC-4).
- **Harness alignment**: `tests/db/test_db_maintenance.py:_make_session_db` DDL default becomes `strftime('%Y-%m-%dT%H:%M:%SZ','now')` and seeded literals switch to the same shape — test-only change that makes the production format mismatch visible to the suite (this is what the hidden regression was).
- **Architecture check** (Step 3): new import edges `db.maintenance → shared.config_utils` and `db.config → shared.config_utils` — allowed by the layer diagram (`db → shared`); `lint-imports` must stay at 6 contracts kept.
- **Persisted schema check**: N/A — no schema change; existing stored timestamp format untouched by design (Issue Constraint).

## Implementation steps
1. **Phase 1: Shared accessor and config validation** (REQ-002, REQ-003; `scripts/shared/config_utils.py`, `scripts/db/config.py`, `scripts/db/maintenance.py`)
   - [ ] Add the bool guard to `get_typed` + docstring (REQ-002; scripts/shared/config_utils.py)
   - [ ] `build_db_config`: `get_typed` for the two timeout keys (REQ-003; scripts/db/config.py)
   - [ ] Both `from_config` methods: `get_typed` + non-negative check with key-named messages (REQ-001 half, REQ-003; scripts/db/maintenance.py)
2. **Phase 2: Purge/prune guards, cutoff rewrite, tie-breaker** (REQ-001 helper half, REQ-004, REQ-005, REQ-006; `scripts/db/maintenance.py`, `scripts/db/store_impl.py`) — re-read Plan 006's landed flow first (Dependencies)
   - [ ] Add `== 0 disabled` / `< 0 raise` guards with updated docstrings to the four helpers (REQ-001; scripts/db/maintenance.py)
   - [ ] Rewrite the three session cutoff queries to `strftime('%Y-%m-%dT%H:%M:%SZ','now', ?)` (REQ-004; scripts/db/maintenance.py)
   - [ ] Rewrite the three store cutoff queries and add the negative-`older_than_days` guard (REQ-004, REQ-005; scripts/db/store_impl.py)
   - [ ] Add `session_id DESC` tie-breaker (REQ-006; scripts/db/maintenance.py)
3. **Phase 3: Tests, docs, validation** (REQ-007; test files, docs)
   - [ ] Align `_make_session_db` to the `T/Z` format; add the Tests-section tests across the three test files (REQ-007)
   - [ ] Update `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` (`:32`, `:42`) (Documentation Impact)
   - [ ] Run `uv run pytest tests/db tests/shared tests/agent/commands -v` (includes Plan 006 regression watch), then full suite `-n auto`
   - [ ] Run ruff, mypy (CI form), bandit `-ll`, `lint-imports`, `tools/check_docs_consistency.py --domain db`; diff-cover ≥ 90% on the branch diff
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md` after commit+push; deploying is the user's decision (UNK-01 operator confirmation)

### Release units
**Unit**: retention-input-validation | **Phases**: 1, 2, 3 | **Reason**: the validation contract (config load ↔ helper guards ↔ tests) is one semantic unit; shipping accessor hardening without the guards would leave negatives reaching the delete helpers through direct construction.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/config_utils.py | Unit (get_typed bool/type matrix) | `uv run pytest tests/shared/test_config_utils.py -v` | AC-3 asserted |
| scripts/db/maintenance.py | Config-load and helper-guard unit tests + boundary integration on real temp DB | `uv run pytest tests/db/test_db_maintenance.py -v` | AC-1, AC-2, AC-4 asserted |
| scripts/db/store_impl.py | Negative-guard + cutoff-boundary unit/integration tests | `uv run pytest tests/db/test_db_store_impl.py -v` | AC-1, AC-2 asserted |
| scripts/db/maintenance.py + store_impl.py (regression) | Plan 006 rollback/atomicity tests and Plan 004 rotation tests re-run after SQL rewrite | `uv run pytest tests/db/test_db_maintenance.py -v` | Plan 006/004 additions stay green |
| scripts/ (regression) | Full suite (maintenance services, memory_prune command, mcp config consumers) | `uv run pytest tests/ -n auto` | No regressions |
| scripts/db + scripts/shared (static) | radon / vulture / lint-imports gates | `uv run radon cc scripts/db/maintenance.py scripts/db/store_impl.py -s`; `uv run vulture scripts/db --min-confidence 80`; `lint-imports` | Top ≤ B(7) (guards add ≤1 branch to already-B(7) functions — extract the guard message builder if exceeded); no new findings; 6 contracts kept |
| branch diff | Coverage gate | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (`--fail-under=90`) | Baseline recorded this cycle (95%); branch diff ≥ 90% |

## Risks
- **Risk**: the cutoff fix makes age rules delete up to one day more than they did before (the off-by-one-day was masking retention debt) → **Mitigation**: this is the configured behavior restored (AC-2); UNK-01 records the operator confirmation at deployment; docs state the corrected comparison.
- **Risk**: `get_typed` hardening breaks a shipped config that uses float or bool for an int key → **Mitigation**: all in-repo configs verified native-int this cycle; the failure is a clear load-time `ValueError` naming the key, not a silent miscount.
- **Risk**: harness format alignment (`_make_session_db`) changes assertions in Plan 004/006 tests that seed space-format literals → **Mitigation**: seed literals move to `T/Z` in the same edit; Phase 3 runs the whole file; differing year/month positions dominate the comparison byte, so existing delete/keep expectations are format-independent (checked Step 2 against `:146-215` seeds).
- **Risk**: guards raise inside already-wrapped `begin_immediate` blocks (Plan 006), converting a validation error into a rolled-back transaction path → **Mitigation**: guards run before the `with` blocks (Phase 2 places them at the top of each helper); STRICT/BEST_EFFORT propagation of `ValueError` stays as Plan 006 documented.
- **Risk**: negative-value `ValueError` in the store could surface as an uncaught error in a command path → **Mitigation**: `memory_prune` already validates `--days >= 1` (`memory_data_ops.py:134-145`); no other in-repo caller passes unvalidated ints (grep this cycle).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Shared accessor and config validation (config_utils.py, config.py, maintenance.py) | In Progress | — | — | procedure docs 20261116-073054_01/_03/_04 generated |
| 2 | Purge/prune guards, cutoff rewrite, tie-breaker (maintenance.py, store_impl.py) | In Progress | — | — | procedure docs 20261116-073054_01/_02 generated |
| 3 | Tests, docs, validation | In Progress | — | — | procedure doc 20261116-073054_05 generated; store/config tests are companions in _02/_03; docs/41_db/db_06 update stays a plan-level step (not a target-file row) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-007-1 | Phase 3 | Follow-up candidate (issue filing): `scripts/agent/memory/count_ops.py:45` cutoff-format mismatch (UNK-02) | Open (planning record) | Maintainer | After Plan 007 lands |
| implementations/20261116-073054_01_scripts_db_maintenance.py.md | 1 | Procedure | Created | — | — |
| implementations/20261116-073054_02_scripts_db_store_impl.py.md | 2 | Procedure | Created | — | — |
| implementations/20261116-073054_03_scripts_shared_config_utils.py.md | 1 | Procedure | Created | — | — |
| implementations/20261116-073054_04_scripts_db_config.py.md | 1 | Procedure | Created | — | — |
| implementations/20261116-073054_05_tests_db_test_db_maintenance.py.md | 3 | Procedure | Created | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092855_dbreview007_retention-input-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-050559
- **Related target files**: scripts/db/maintenance.py, scripts/db/store_impl.py, scripts/shared/config_utils.py, scripts/db/config.py, tests/db/test_db_maintenance.py, tests/db/test_db_store_impl.py, tests/shared/test_config_utils.py

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem bullets 1-2; Required Changes bullet 1; Unresolved Question answered 2026-11-15 (0=disabled, negative rejected) | scripts/db/maintenance.py | Phases 1-2 | AC-1 | Config + helper boundary tests | Verified by test (Issue reproduction; re-verified Step 2) |
| REQ-002 | Problem bullet 4 (`bool` via `isinstance`); AI Implementation Instruction (use `get_typed`) | scripts/shared/config_utils.py | Phase 1 | AC-3 | get_typed matrix tests | Explicit in code (`config_utils.py:51-72`) |
| REQ-003 | Problem bullet 4; `rules/coding.md` coercion policy | scripts/db/maintenance.py, scripts/db/config.py | Phase 1 | AC-3 | Config-load tests; `config/agent.toml:11-18` checked | Explicit in code (`maintenance.py:112-113,132-133`; `config.py:77-78`) |
| REQ-004 | Problem bullet 3; Required Changes bullet 2 | scripts/db/maintenance.py, scripts/db/store_impl.py | Phase 2 | AC-2 | Cutoff-day boundary tests | Verified by test (Step 2 live SQL confirmation) |
| REQ-005 | Problem bullet 2 (NULL silent no-op) | scripts/db/store_impl.py | Phase 2 | AC-1 | Negative-days ValueError tests | Verified by test (Step 2 live confirmation) |
| REQ-006 | Problem bullet 5; Required Changes bullet 3 | scripts/db/maintenance.py | Phase 2 | AC-4 | Tie-order determinism test | Explicit in code (`:217`) |
| REQ-007 | Testing Expectations; Required Changes bullet 4 | tests/db/test_db_maintenance.py, tests/db/test_db_store_impl.py, tests/shared/test_config_utils.py | Phase 3 | AC-1..AC-4 | New tests + harness alignment | Verified by test (gaps confirmed this cycle) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261116-073054 -->
