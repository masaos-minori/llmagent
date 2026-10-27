# Plan: Offload turn-path session SQLite writes from the REPL event loop

**Generated from**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
**Date**: 2026-10-27
**Task classification**: Path B — cross-module contract change (sync → async persistence
boundary), thread-safety configuration, sequenced dependency on turn001

## Goal

Run all turn-path session-DB writes off the asyncio event loop via the repo's existing
`asyncio.to_thread` pattern, inside the single `TurnPersistence` boundary introduced by
`plans/20261027-070403_turn001_atomic-turn-persistence.md`, so a busy-lock wait (up to
the 30s `busy_timeout`) cannot stall signal handling, shutdown coordination, or
background-task callbacks.

## Priority

Medium (inherited from the issue).

## Scope

**In scope:**

- REQ-001: offload turn-boundary SQLite writes with `asyncio.to_thread` at the single
  persistence boundary (no new executor/queue abstraction).
- REQ-002: explicit thread-safe connection setup for the boundary's reused write
  connection: a `check_same_thread` pass-through in `scripts/db/helper.py`, used with
  `False` only by the boundary; every other helper usage keeps the default `True`.
- REQ-003: preserve strict write ordering within a turn (sequential awaits).
- REQ-004: existing public signatures preserved (`AgentSession` facade, `complete_round`);
  the only contract change is `TurnPersistence` phase methods becoming awaitable.
- REQ-005: thread-safety probe tests for the DB helper under `asyncio.to_thread` run
  FIRST, before wiring the offload (issue AI Instruction).
- REQ-006: contention test proving the event loop stays responsive during a locked write.
- REQ-007: threading boundary recorded in DB helper docs.

**Out of scope:**

- WAL mode or `busy_timeout` value changes (issue Out of Scope).
- Command-path dispatch (already offloaded: `cmd_session.py` L222-228 `asyncio.to_thread`
  dispatch table; `wal_checkpoint_manager.py`).
- `tool_runner.py` L430 `ctx.session.save_many([])`: verified NOT a DB write —
  `SessionMessageRepository.save_many` early-returns on empty input before opening any
  connection (`session_message_repo.py` L104-116, `not messages` → `return`). Review +
  grep acceptance is satisfied without touching it.
- `session.save_diagnostic`: dead facade (zero callers repo-wide).

## Background

From a `python-code-review` pass (finding F-010). Verification against current source:

- `PRAGMA busy_timeout` is applied to every connection (`scripts/db/helper.py` L41,
  default 30000 ms; `scripts/db/config.py` L31).
- Turn-path sync write sites today: `llm_turn_runner.py` L107 (`ctx.session.save`),
  `conversation_state_manager.py` L119 (`ctx.session.save("user", line)`),
  `tool_round_completion.py` L82 (`ctx.session.save_many`, inside `async def
  complete_round` L55), `workflow_engine_adapter.py` L358 (`ctx.session.save`).
  Stale claim corrected: `orchestrator.py` has no direct `session.save*` call sites (grep
  zero matches); the call sites live in the turn-runner modules. Stale claim corrected:
  `save_assistant_message` and a `complete_round` method on `session.py` do not exist;
  `complete_round` is a module function in `tool_round_completion.py`.
- Stale claim corrected/updated: `save_many([])` at `tool_runner.py` L430 opens no
  connection (evidence above).
- Thread-safety facts (resolves the issue's Unresolved Question):
  - `helper._connect()` (L128-138) calls `sqlite3.connect(path, timeout=...)` with no
    `check_same_thread` argument → default `True`: a connection may only be used from the
    thread that created it.
  - `open()` (L166-196) creates a NEW connection per call unless `reuse_connection=True`;
    the current per-call pattern (open-use-close inside one sync method) is therefore
    safe under `asyncio.to_thread`: the whole method, including `connect()`, runs on one
    worker thread.
  - The exception is turn001's design: `TurnPersistence` holds ONE reused write
    connection for the whole turn (turn001 Plan Design). Reused connections cross threads
    under `to_thread` and need `check_same_thread=False`; sequential (never concurrent)
    use — guaranteed by sequential `await` of phases — makes this safe.
  - `sqlite-vec` loading happens per connection at open (L140-153); executed on whichever
    thread opens that connection; no cross-thread concern.
- Established offload pattern: `cmd_session.py` L222-228 (`asyncio.to_thread` dispatch
  table), `wal_checkpoint_manager.py`.
- Churn (90d commits): `helper.py` 4; `tool_runner.py` 19. `turn_persistence.py` does not
  exist yet (created by turn001).

## Problem

Today a mid-turn save runs synchronously on the event-loop thread; under lock contention
it can block the loop for up to 30s (issue Problem).

## Reason for Change

REPL reliability contract: signal/shutdown responsiveness must not be undermined by a
hidden synchronous DB wait inside the turn (issue).

## Implementation Intent

Follow the issue's preferred option: reuse `asyncio.to_thread` at the single persistence
boundary created by turn001 (explicit issue Constraint: "Coordinate with the
atomic-persistence issue so the transaction work and this offload do not implement two
different persistence wrappers"). The offload lives inside `TurnPersistence` phase
methods; call sites only add `await`.

## Requirements

| ID | Requirement | Issue Evidence | Reason It Solves It | Scope Decision | Basis |
|----|-------------|----------------|---------------------|----------------|-------|
| REQ-001 | Turn-path session-DB writes run on worker threads via `asyncio.to_thread` inside the single `TurnPersistence` boundary | Summary; Implementation Intent "Wrap ... with the existing offload pattern"; Constraint against two wrappers | Loop never executes sqlite calls during a turn | In | Explicit in issue |
| REQ-002 | `helper.py` gains a `check_same_thread` pass-through; the boundary's reused connection opens with `False`; all other usage keeps `True` | Constraints: "offloading must use a per-call connection ... or an explicitly thread-safe setup"; Unresolved Question | Makes the turn001 reused-connection design legal across threads without abandoning it | In | Explicit in issue Constraints |
| REQ-003 | Strict write ordering preserved within a turn | Constraints | Sequential awaits: each phase completes before the dependent step, same as today | In | Explicit in issue Constraints |
| REQ-004 | Existing public signatures unchanged; `TurnPersistence` phase methods become awaitable | AI Instruction "Preserve write ordering and public method signatures" | Facade/API compatibility for all non-turn users | In (with the recorded boundary-API transition) | Explicit in issue + turn001 dependency |
| REQ-005 | DB-helper thread-safety probe tests before wiring | AI Instruction "resolve it with a probe test before wiring the offload"; Required Changes bullet 2 | Validates `check_same_thread` behavior and the per-call pattern under threads with evidence | In | Explicit in issue |
| REQ-006 | Contention test: loop stays responsive (timer fires) while a locked write waits | Acceptance Criteria, Testing Expectations | Proves the actual reliability property | In | Explicit in issue |
| REQ-007 | Threading boundary documented (worker-thread calls, connection-per-call rule, boundary exception) | Documentation Impact | Future maintainers see which calls leave the loop | In | Explicit in issue |
| OUT-1 | WAL / `busy_timeout` changes | Out of Scope | — | Out | Explicit in issue |
| OUT-2 | Command-path dispatch | Out of Scope | — | Out | Explicit in issue |
| OUT-3 | `tool_runner.py` L430 `save_many([])` | Acceptance "no direct synchronous session-write call remains" | Verified no-DB-access (early return L104-116); not a write | Out | Step 2 verification |

## Implementation Target Files

**Freeze status**: Frozen (`issue-to-plan` Step 8 Implementation Target Files
Validation passed — structure check exit 0; all rows verified against source except the
two turn001-created rows, explicitly marked Deferred; all overlaps are sequenced
continuations of the Frozen turn001 Plan adjudicated Compatible.)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
implementation skill — including file paths inside inline code snippets — MUST reference
exactly these paths and no others: a skill MUST NOT create, split, merge, rename, or
otherwise introduce any file that is not a row in this table. When a discovered need
does not map onto any row, it is an unresolved question that reopens the Plan — not
something the skill may resolve by inventing a file.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/helper.py | Add `check_same_thread: bool = True` pass-through from `SQLiteHelper.__init__`/`open` into `_connect` (`sqlite3.connect`) | Boundary's reused connection must be legal across worker threads (sequential use); today no knob exists (L135 no arg) | REQ-002 | Read: `_connect` L128-138, `open` L166-196, `_load_vec_extension` per-open | tests/db/test_helper_thread_safety.py | Verified |
| scripts/agent/turn_persistence.py | `TurnPersistence` phase-write and compensation methods become `async def` running their sync sqlite core via `await asyncio.to_thread(...)`; boundary connection opened with `check_same_thread=False`; sequential awaits preserve order | Single-boundary offload per issue Constraint "do not implement two different persistence wrappers" | REQ-001, REQ-002, REQ-003, REQ-004 | File is created by Frozen Plan `plans/20261027-070403_turn001...` (Design: one reused write connection per turn); this row is executable only after turn001 is implemented (issue Dependencies) | tests/agent/test_turn_persistence.py | Deferred: created by turn001 |
| scripts/agent/orchestrator.py | Await boundary creation/phase/compensation calls added by turn001 | Offloaded boundary calls become awaitables | REQ-003, REQ-004 | Read: orchestrator has no direct `session.save*` today; turn001 adds boundary calls per execute_turn | tests/agent/test_orchestrator.py | Verified |
| scripts/agent/conversation_state_manager.py | Await boundary calls in `append_user_message` (L119 site) and compression writes | Same | REQ-003, REQ-004 | Read: `ctx.session.save("user", line)` L119 in async method | tests/agent/test_history_compression_consistency.py | Verified |
| scripts/agent/llm_turn_runner.py | Await boundary call replacing L107 save | Same | REQ-003, REQ-004 | Read: `ctx.session.save` L107 | tests/agent/test_llm_turn_runner.py | Verified |
| scripts/agent/tool_round_completion.py | Await boundary call replacing L82 `save_many` in `async def complete_round` | Same | REQ-003, REQ-004 | Read: L82; `complete_round` L55 async | tests/agent/test_tool_round_completion.py | Verified |
| scripts/agent/workflow_engine_adapter.py | Await boundary call replacing L358 save | Same | REQ-003, REQ-004 | Read: `ctx.session.save("assistant", answer)` L358 | tests/agent/test_llm_turn_runner.py indirect + workflow tests | Verified |
| tests/db/test_helper_thread_safety.py | New probe-test module: per-call `open` pattern used from a worker thread via `asyncio.to_thread` succeeds; `check_same_thread=False` connection created on one thread used sequentially from another succeeds; default `True` connection used cross-thread raises `sqlite3.ProgrammingError` | REQ-005 probe gate before wiring offload; resolves the issue Unresolved Question with runtime evidence | REQ-002, REQ-005 | Read: no `check_same_thread` anywhere in `scripts/db/` today; `sqlite3.connect` default True | this file | Verified (new file; name collision checked) |
| tests/agent/test_turn_persistence.py | Extend: phase writes execute off the loop thread; contention test — second connection holds write lock (`BEGIN IMMEDIATE`), a 50 ms heartbeat task keeps ticking while the boundary write waits, then write completes within busy_timeout | REQ-006 contention acceptance | REQ-001, REQ-003, REQ-006 | File is created by turn001; extended here | this file | Deferred: created by turn001 |
| tests/agent/test_llm_turn_runner.py | Mock/await-contract updates for boundary methods becoming async | REQ-004 transition | REQ-004 | Exists (turn001 test inventory) | — | Verified |
| tests/agent/test_tool_round_completion.py | Mock/await-contract updates | REQ-004 transition | REQ-004 | Exists | — | Verified |
| tests/agent/test_orchestrator.py | Await-contract updates for boundary/compensation calls | REQ-004 transition | REQ-004 | Exists | — | Verified |
| tests/agent/test_history_compression_consistency.py | Await-contract updates | REQ-004 transition | REQ-004 | Exists | — | Verified |
| tests/agent/test_agent_session.py | Await-contract updates for `turn_boundary()` factory consumers | REQ-004 transition | REQ-004 | Exists | — | Verified |

Deferred target row (not touched during `python-implementation`; executed in the
workflow's Step 10 docs phase):

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md | Record the persistence threading boundary: turn-boundary writes run on worker threads via `asyncio.to_thread`; connection-per-call remains the default rule; the single exception is the boundary's reused connection opened with `check_same_thread=False` used sequentially only | Documentation Impact; today db_04 documents connection options without any threading rule (L35 lists options, no threading) | REQ-007 | `docs/00_index.md` L124/L152/L191 map SQLite/connection/WAL/transactions and Session/DB persistence to db_04 | N/A: documentation only | Verified |

## Reference Files

These files are read-only for context and MUST NOT be modified; any change to them
requires reopening the Plan with an explicit decision recorded under Assumptions.

| Path | How to use it | Requirements |
|------|---------------|------------|
| `scripts/agent/session.py` | Facade (`save`/`save_many`/`replace_messages` L57-83) signatures stay unchanged; `turn_boundary()` factory added by turn001 is the boundary entry | REQ-004 |
| `scripts/agent/commands/cmd_session.py` | L222-228 `asyncio.to_thread` dispatch table — the pattern to imitate | REQ-001 |
| `scripts/agent/tool_runner.py` | L429-431: verified no-DB no-op; must NOT be "offloaded" (nothing to offload) | OUT-3 |
| `scripts/agent/wal_checkpoint_manager.py` | Existing `to_thread` usage reference | REQ-001 |
| `plans/20261027-070403_turn001_atomic-turn-persistence.md` | Frozen design this Plan extends: reused connection, per-phase `begin_immediate`, compensation | REQ-001 |

## Acceptance Criteria

- REQ-001: grep + review of the async turn path (`orchestrator.py`, `llm_turn_runner.py`,
  `tool_round_completion.py`, `conversation_state_manager.py`, `workflow_engine_adapter.py`)
  shows no direct synchronous session-write call; all turn writes go through awaited
  boundary methods offloaded inside `turn_persistence.py`.
- REQ-002: probe tests green, including the `ProgrammingError` case proving default `True`
  semantics; only the boundary connection passes `check_same_thread=False`.
- REQ-003: existing turn/session tests pass unchanged in behavior (issue Acceptance).
- REQ-005: probe test module runs and passes BEFORE the offload wiring step is accepted.
- REQ-006: contention test: heartbeat ticks during a ≥1 s lock hold, write completes after
  release; total loop stall ≈ 0.
- REQ-007: db_04 documents the threading boundary (docs phase).
- `mypy`/`ruff` clean.

## Tests

| Test target | Tool | What it proves | Requirements |
|-------------|------|----------------|------------|
| `tests/db/test_helper_thread_safety.py` (new) | pytest | helper thread-safety facts under `asyncio.to_thread` (probe gate) | REQ-002, REQ-005 |
| `tests/agent/test_turn_persistence.py` (extended) | pytest | writes execute off the loop thread; loop responsive under a held write lock; ordering preserved | REQ-001, REQ-003, REQ-006 |
| `tests/agent/test_llm_turn_runner.py`, `test_tool_round_completion.py`, `test_orchestrator.py`, `test_history_compression_consistency.py`, `test_agent_session.py` | pytest | await-contract updates; turn/session behavior unchanged | REQ-003, REQ-004 |
| full suite (`uv run pytest`) | pytest | no regression across REPL paths | REQ-001, REQ-003 |

## Documentation Impact

- `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`: threading-boundary
  section (deferred docs row).
- `docs/23_agent/agent_09_01_data-layer-session-db.md`: assessed, no change needed — it
  describes repository behavior (lazy rebind, filtering, purge), not call-site threading.
- `rules/env.md` knowledge candidate after implementation (see Knowledge candidates).

## Assumptions

- Sequencing (issue Dependencies): this Plan is implemented ONLY after
  `plans/20261027-070403_turn001...` is fully implemented; `turn_persistence.py` rows
  depend on that. If turn001 implementation reveals a different boundary API shape, the
  Unknown below is resolved then.
- Overlap adjudication: all overlaps with turn001-targeted files
  (`orchestrator.py`, `conversation_state_manager.py`, `llm_turn_runner.py`,
  `tool_round_completion.py`, `workflow_engine_adapter.py`, `turn_persistence.py`, the five
  test files) are Compatible by construction — this Plan is the sequenced continuation of
  turn001 on the same boundary, never a second wrapper (issue Constraint).
- Overlap `conversation_state_manager.py` with memory001: disjoint members (memory001
  touches `handle_memory_injection` retry bookkeeping; this Plan touches the
  `append_user_message`/compression call lines) — Compatible.
- Sequential-only use of the boundary connection is the safety precondition for
  `check_same_thread=False`; it is enforced by awaiting each phase before the next and is
  stated as a design rule in `turn_persistence.py`.

## Unknowns

- Exact `TurnPersistence` method surface after turn001 implementation (which methods are
  sync today in the implemented code) — resolve at implementation start by reading
  `turn_persistence.py`; this Plan adapts those methods to `async def` with the same
  behavior. This does not reopen scope; only mechanics are affected.

## Affected areas

| Area | Change | Blast radius | Requirements |
|------|--------|--------------|------------|
| DB helper layer | new `check_same_thread` kwarg (default unchanged) | `_connect` + constructor/open plumbing; all existing call sites unaffected by default | REQ-002 |
| turn persistence boundary | sync → awaitable phase methods with internal `to_thread` | 5 call-site modules add `await`; facade APIs untouched | REQ-001, REQ-003, REQ-004 |
| test suite | 1 new module + 6 extended | test-only | REQ-005, REQ-006 |
| docs | threading-boundary section | db_04 | REQ-007 |

## Design

- Offload point: inside `TurnPersistence` (single boundary per the issue Constraint), not
  at call sites — 1 offload instead of 6, and compensation gets it for free. Phase method
  body pattern: `await asyncio.to_thread(self._write_core_immediate, ...)` where
  `_write_core_immediate` is the current sync `begin_immediate` transaction core.
- Connection strategy: keep turn001's one reused write connection, opened with
  `check_same_thread=False` (issue Constraint's "explicitly thread-safe setup" branch).
  Safety: phases and compensation are awaited strictly sequentially, so exactly one thread
  touches the connection at any moment. Rejected alternatives: (a) per-call connections
  inside the boundary — abandons turn001's frozen reused-connection design and re-opens
  that Plan; (b) dedicated per-turn executor/queue — explicitly forbidden by the issue AI
  Instruction.
- Probe-first gate (issue AI Instruction): REQ-005 tests are implemented and run before
  any wiring; if `check_same_thread=False` with the session target (which loads sqlite-vec
  per open, L176: session default `load_vec=True`) misbehaves, STOP and reopen this Plan —
  the fallback (per-call connections in the boundary) requires a turn001 design decision.
- Ordering (REQ-003): call sites already await each persistence step in turn order;
  adding `await` to boundary calls preserves the existing sequence exactly.

## Implementation steps

0. Prerequisite gate: turn001 fully implemented; read `scripts/agent/turn_persistence.py`
   and record its actual method surface (closes the Unknown).
1. `tests/db/test_helper_thread_safety.py` (REQ-005, REQ-002): probe tests; run green
   before any production change.
2. `scripts/db/helper.py` (REQ-002): `check_same_thread` kwarg plumbed to `_connect`.
3. `scripts/agent/turn_persistence.py` (REQ-001, REQ-002, REQ-003): phase/compensation
   methods → `async def` with `await asyncio.to_thread(...)`; boundary connection opened
   thread-safe; document the sequential-use rule at the connection creation site.
4. Call sites (REQ-003, REQ-004): add `await` in `orchestrator.py`,
   `conversation_state_manager.py`, `llm_turn_runner.py`, `tool_round_completion.py`,
   `workflow_engine_adapter.py`.
5. Test updates + contention/offload tests (REQ-006): extend
   `tests/agent/test_turn_persistence.py`; update the five mock/await-contract test files.
6. Full validation sequence (see Validation plan).
7. Step 10 docs phase (REQ-007): db_04 threading-boundary section.

Strict order: 0 → 1 → 2 → 3 → 4 → 5 → 6; 7 deferred.

## Validation plan

| Check | Command | Expected | Requirements |
|-------|---------|----------|------------|
| probe gate first | `uv run pytest tests/db/test_helper_thread_safety.py` | green before step 2 merge | REQ-005 |
| offload/contention | `uv run pytest tests/agent/test_turn_persistence.py` | heartbeat ticks during held lock; writes off loop thread | REQ-001, REQ-006 |
| turn-path grep review | `grep -n "session\.save\|save_many(" scripts/agent/orchestrator.py scripts/agent/llm_turn_runner.py scripts/agent/tool_round_completion.py scripts/agent/conversation_state_manager.py scripts/agent/workflow_engine_adapter.py` | no direct sync session writes remain (OUT-3 no-op documented) | REQ-001 |
| full suite | `uv run pytest` | green | REQ-003 |
| static | `uv run ruff check . && uv run ruff format --check . && uv run mypy scripts/ && uv run bandit -c bandit.yaml -r scripts/ -q` | clean | REQ-002, REQ-004 |

## Risks

| Risk | Likelihood | Impact | Mitigation | Affected requirements |
|------|------------|--------|------------|-----------------------|
| Future code runs two boundary operations concurrently on the reused connection (breaks `check_same_thread=False` safety) | Low | High | Sequential-await design rule stated at connection creation + contention test; add assert-only guard consideration during implementation (no new abstraction) | REQ-002, REQ-003 |
| Probe reveals sqlite-vec load interaction with `check_same_thread=False` fails for the session target | Low | High | STOP-and-reopen this Plan (Design gate); fallback per-call connections requires a turn001 design decision, not an in-skill invention | REQ-002, REQ-005 |
| await-contract churn hides a behavior regression in mocked tests | Medium | Medium | Characterization: full suite + test_history_compression_consistency behavior asserts unchanged; mocked files updated mechanically, behavior asserts kept | REQ-003 |

## Knowledge candidates

- Candidate (rule): "Turn-path session writes run on worker threads inside
  `TurnPersistence` via `asyncio.to_thread`; the boundary's reused connection is the only
  `check_same_thread=False` connection in the codebase and must be used sequentially" →
  `rules/env.md`. Confirm with the owner at implementation time.

## Execution Status

| Field | Value |
|-------|-------|
| Phase | P0: turn001 prerequisite + boundary API read; P1: probe tests; P2: helper kwarg; P3: boundary offload; P4: call-site awaits; P5: test updates + contention test; P6 (deferred docs): db_04 |
| Status | Planned — START BLOCKED until turn001 implementation completes (issue Dependencies) |
| Completed scope | none yet |
| Next action | `plan-to-implementation-procedure` after turn001 implementation |

## Traceability

- **Workflow phase**: `issue-to-plan`
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the plan
- **Source implementation procedure**: N/A: not yet generated
- **Generated at**: 20261027-090510
- **Related target files**: `scripts/db/helper.py`, `scripts/agent/turn_persistence.py`, `scripts/agent/orchestrator.py`, `scripts/agent/conversation_state_manager.py`, `scripts/agent/llm_turn_runner.py`, `scripts/agent/tool_round_completion.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/db/test_helper_thread_safety.py`, `tests/agent/test_turn_persistence.py`, `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`
