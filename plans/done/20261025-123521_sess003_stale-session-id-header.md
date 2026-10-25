# sess003 — Refresh X-Session-Id when the active session id changes

**Source issue**: `issues/20261025-115646_sess003_stale-session-id-header.md`

> Path B (5 target files: 3 source + 1 new test + 1 docs; cross-module helper).
> Full analysis run. All issue claims verified against current source 2026-10-25:
> `set_session_id` has exactly one call site outside the tools layer
> (`repl_input_loop.py:110`, startup-only); session-id mutation points are
> `session.py:148` (`start()`) and `session_restore.py:97` (grep-verified exhaustive);
> `conversation_service.clear_conversation(new_session=True)` calls
> `ctx.session.start()` (lines 30-31); doc quotes confirmed at
> `mcp_02_01:50` and `mcp_03_03:64`. Confidence: High.

## Goal

Establish the invariant: whenever the agent's active session id changes, the MCP
transport correlation id is refreshed to match, so `X-Session-Id` on every tool call
equals the session that is actually active.

## Priority

Medium (issue-stated). Silent cross-layer misattribution of all MCP calls after
`/session load` or `/clear` new-session — grows with normal daily usage.

## Scope

In scope:
- A single shared refresh helper (new function) and its call at every post-startup
  session-id change point (`restore_session`, `clear_conversation(new_session=True)`).
- New spy-based tests.
- `docs/22_mcp/mcp_02_01_endpoints-and-transport.md` wording.

Out of scope (issue-stated):
- Server-side handling of session ids in MCP servers.
- The message-repo binding fix (sess001).
- MCP transport internals (header injection unchanged).
- Startup call behavior — unchanged (must still be set before the first turn).

## Background

Wiring was written for the single-session startup case (`repl_input_loop.py:107-110`:
set once, guarded by `tools is not None` and `session_id is not None`). Multi-session
flows were added later: `/session load` delegates to `restore_session`
(`cmd_session.py:259`, reassigns at `session_restore.py:97`) and `/clear` new-session
calls `ctx.session.start()` (`conversation_service.py:31`). Neither refreshes the
tools' correlation id. Churn: all three target source files are low-churn
(1-3 commits/30d, 3 authors each); `mixin_base.py` has 10 importers — the helper
addition is additive and touches none of them.

## Problem

After a restore or new-session clear, every MCP tool call carries the previous
session's id. Server-side audit logs attribute calls to the wrong session and the
documented cross-layer correlation key (`X-Session-Id`, "spans the entire session" per
`mcp_03_03:64`) silently breaks for the rest of the REPL run.

## Reason for Change

Confirmed by exhaustive grep (2026-10-25): exactly one `set_session_id` call site
outside the tools layer, executed once before the REPL loop; both id-mutation flows
miss it. The defect widens with each session switch in a long REPL run.

## Implementation Intent

One shared refresh helper (issue AI-instruction: prefer a shared helper over
duplicated `set_session_id` calls). Both id-changing flows call it immediately after
the id changes. The startup call site stays where it is. The helper centralizes the
guards (`tools is None`, `session_id is None`) and the `int -> str` conversion so
future change points call one function instead of re-deriving the pattern.

## Requirements

| ID | Requirement | Priority | Target |
|---|---|---|---|
| REQ-001 | A single shared helper refreshes the tools' session id from `ctx` and centralizes the `int -> str` conversion and None guards. | must | scripts/agent/commands/mixin_base.py |
| REQ-002 | `restore_session()` refreshes the correlation id after reassigning `session_id`. | must | scripts/agent/services/session_restore.py |
| REQ-003 | `clear_conversation(new_session=True)` refreshes after `ctx.session.start()`. | must | scripts/agent/services/conversation_service.py |
| REQ-004 | Startup behavior unchanged: id still set before the first turn via `repl_input_loop.py:110`. | must | scripts/agent/repl_input_loop.py (verify only) |
| REQ-005 | Refresh is a no-op when `tools is None` (MCP disabled) or `session_id is None` — mirrors the existing startup guard. | must | scripts/agent/commands/mixin_base.py |
| REQ-006 | Docs state the invariant (set at startup, refreshed on every session-id change) without code detail. | should | docs/22_mcp/mcp_02_01_endpoints-and-transport.md |

## Implementation Target Files

> One row per directly affected file.

| File | Action | Contract / Exports to Keep |
|---|---|---|
| scripts/agent/commands/mixin_base.py | modify | `reset_session_stats` and `MixinBase` exports unchanged; add module-level helper (working name `refresh_session_correlation(ctx)`) — guards `ctx.services_required.tools is not None` and `ctx.session.session_id is not None`, calls `tools.set_session_id(str(ctx.session.session_id))`, else no-op. |
| scripts/agent/services/session_restore.py | modify | `restore_session()` signature, return (`SessionRestoreResult`), non-destructiveness, and `reset_session_stats(ctx)` call unchanged; add helper call after `ctx.session.session_id = session_id` (line 97 at audit time). |
| scripts/agent/services/conversation_service.py | modify | `clear_conversation()` signature/return and no-new-session path unchanged; add helper call after `ctx.session.start()` in the new-session branch. |
| tests/agent/test_session_correlation_refresh.py | create | New spy-based tests (see Tests): helper unit tests + restore-flow + clear-flow tests. Deliberately a NEW file — keeps zero target-file overlap with sess001's `test_session_restore.py` changes. |
| docs/22_mcp/mcp_02_01_endpoints-and-transport.md | modify | Line 50 wording: "set during agent startup" -> set at startup AND refreshed whenever the active session id changes; state invariant + failure behavior only, no code detail. |

Not edited (verified): `scripts/agent/repl_input_loop.py` (startup call stays; its
inline guard duplicates the helper's guards — acceptable, startup must not be
reordered), `scripts/shared/tool_transport_invoker.py` / `http_transport.py` (transport
unchanged per Constraint), `docs/22_mcp/mcp_03_03_transport-and-health.md` (line 64
"spans the entire session" remains accurate per-session after the fix).

## Reference Files

- `scripts/agent/repl_input_loop.py:107-110` — startup call + guards (pattern to mirror).
- `scripts/agent/services/session_restore.py:97-98` — id reassignment + `reset_session_stats` adjacency.
- `scripts/agent/services/conversation_service.py:26-36` — new-session branch.
- `scripts/agent/commands/cmd_session.py:255-259` — `/session load` -> `restore_session` delegation.
- `scripts/agent/commands/mixin_base.py:19-27` — `reset_session_stats` precedent: module-level shared helper used by all three flows (clear / load / restore); chosen home for the new helper.
- `scripts/shared/tool_transport_invoker.py:73-77` — `set_session_id(str)` fan-out to transports.
- `tests/shared/test_tool_executor_routing.py:420-455` — existing tools-layer behavior guards (characterization).

## Acceptance Criteria

| ID | Criterion | Maps to |
|---|---|---|
| AC-001 | Spy test: `restore_session()` on a ctx with spy tools → `set_session_id(str(restored_id))` called after the switch. | REQ-001, REQ-002 |
| AC-002 | Spy test: `clear_conversation(new_session=True)` → `set_session_id(str(new_id))` called. | REQ-003 |
| AC-003 | Helper unit tests: `tools is None` → no-op (no exception); `session_id is None` → no-op; both set → single call with the str value. | REQ-001, REQ-005 |
| AC-004 | Startup: `repl_input_loop` unchanged; existing REPL wiring tests pass; id still set before first turn. | REQ-004 |
| AC-005 | `tests/agent/commands/test_agent_cmd_session.py` and REPL/session test sets pass unmodified; ruff + mypy clean on changed files; `lint-imports` 6 kept / 0 broken. | REQ-001..REQ-003 |
| AC-006 | `mcp_02_01` states the refresh invariant; docs checker passes. | REQ-006 |

## Tests

New file `tests/agent/test_session_correlation_refresh.py`:
1. Helper unit: MagicMock tools + session_id=42 → `set_session_id("42")` called once.
2. Helper unit: `tools=None` → no-op, no exception (resolves issue Unresolved Question).
3. Helper unit: `session_id=None` → no-op.
4. Restore flow: mock-ctx pattern from `tests/agent/test_session_restore.py` + spy
   tools → after `restore_session(ctx, id)`, spy recorded `set_session_id(str(id))`.
5. Clear flow: `clear_conversation(ctx, new_session=True)` with mocked `session.start`
   assigning a new id + spy tools → spy recorded `set_session_id(str(new_id))`.

Characterization guards (unmodified): `tests/agent/commands/test_agent_cmd_session.py`,
`tests/agent/test_repl*.py`, `tests/agent/test_session_restore.py` (its MagicMock ctx
tolerates the new helper call), `tests/shared/test_tool_executor_routing.py`.

Execution order: targeted new file + the guard sets → `tests/agent/test_session*.py`
selected set → full suite.

## Documentation Impact

- `docs/22_mcp/mcp_02_01_endpoints-and-transport.md:50` — replace "set during agent
  startup" with startup + refresh-on-change invariant (issue Documentation Impact,
  verbatim intent).
- `docs/22_mcp/mcp_03_03_transport-and-health.md` — verified no change needed; line 64
  wording stays true per session.
- `docs/00_index.md` MCP transport mapping scope; docs checker must pass; English per
  `skills/DESIGN.md`.

## Assumptions

| Assumption | Confidence | Verification |
|---|---|---|
| The only post-startup session-id change points are `restore_session` and `clear_conversation(new_session=True)` (both funnel through `session.py:148` / `session_restore.py:97`). | High | Exhaustive grep of `session_id =` assignments in `scripts/` 2026-10-25; helper docstring states the invariant so future call sites are discoverable. |
| `agent.services -> agent.commands.mixin_base` import direction is permitted. | High | `session_restore.py` already imports `reset_session_stats` from it; `lint-imports` currently 6 kept. |
| No-op when `tools is None` is the intended behavior (MCP disabled). | High | Mirrors startup guard (`repl_input_loop.py:107`) and `startup_mcp_starter` None-handling; resolves the issue's Unresolved Question (recorded as decision). |

## Unknowns

| ID | Question | Confidence | Blocking | Verification Steps |
|---|---|---|---|---|
| U-001 | Does the desktop/web runtime (`agent_web`) have its own startup wiring that sets `set_session_id` once and also needs the refresh? Grep found the REPL call site only. | High (resolved) | No | RESOLVED 2026-10-25 re-verification: `agent_web/` does not exist in the repository; `repl_input_loop.py:110` is the only `set_session_id` call site outside the tools layer. REPL is the only affected runtime. |
| U-002 | Whether `/clear` without new_session should also refresh (id is unchanged — no-op by definition). | High | No | Design decision recorded: no call in that branch (id unchanged); test 5's sibling asserts single-call behavior only for the new-session branch. |

## Adversarial Re-verification (2026-10-25, procedure generation)

- Startup guards + call confirmed at `repl_input_loop.py:106-110`
  (`ctx.services_required.tools is not None and ctx.session.session_id is not None` →
  `set_session_id(str(...))`).
- `session_restore.py:97` (`ctx.session.session_id = session_id`) and `:98`
  (`reset_session_stats(ctx)`) — confirmed. `reset_session_stats` already imported from
  `agent.commands.mixin_base` by both services (`session_restore.py:14`,
  `conversation_service.py:14`) — import direction confirmed.
- `conversation_service.clear_conversation` spans 24-37; new-session branch
  `ctx.session.start()` at line 31.
- `session.py:148` (`self.session_id = cur.lastrowid`) — confirmed; `set_session_id` has
  exactly one call site outside the tools layer (`repl_input_loop.py:110`, grep re-run).
- `agent_web/` does NOT exist in the repository (sess001 verification finding re-confirmed):
  U-001's verification target is obsolete; Phase 3 resolves as "no other runtime wiring
  exists" (U-001 closed, non-blocking, no follow-up).
- `mcp_02_01:50` quote confirmed verbatim; `mcp_03_03:64` "spans the entire session"
  confirmed. Docs checkers per `routing.md` (`check_docs_quality.py`,
  `check_docs_structure.py`, `check_docs_content_policy.py`,
  `check_docs_consistency.py --domain mcp`).
- Test figures: "186-test baseline set" is wrong — `tests/agent/test_session*.py` collects
  78 tests (4 files). Full suite collects 10091 tests at HEAD fb9359f22.
  `test_tool_executor_routing.py` session-id tests confirmed around lines 419-457.
- `mixin_base` importers: 11 files (plan said 10) — additive helper stays safe.

## Affected areas

- `agent.commands.mixin_base` (10 importers) — additive function, no existing export
  changes; importers unaffected.
- `agent.services.session_restore`, `agent.services.conversation_service` — one added
  call each; existing flows' observable behavior otherwise unchanged.
- MCP transport/tools layer: untouched; only the value of the correlation header
  changes for post-switch calls (server-side audit attribution improves).
- Ordering dependency: sess001 lands first (issue Dependencies); no shared target
  files after routing the new tests into a new file (`session_restore.py` is edited
  only by sess003; sess001's plan left it unmodified).
- DB/services/`deploy.sh`: no impact (in-process wiring only).

## Design

Chosen: **shared helper in `mixin_base.py`, called by each id-changing flow** — the
issue's option 1+2 hybrid, matching the existing `reset_session_stats` precedent
(same ctx-mutation point, same three flows).

- `mixin_base.py`: module-level `refresh_session_correlation(ctx)`: guards
  `ctx.services_required.tools is not None and ctx.session.session_id is not None` →
  `ctx.services_required.tools.set_session_id(str(ctx.session.session_id))`. Docstring
  states the invariant: MUST be called by every flow that changes the active session
  id outside `Agent.start()`'s own startup use.
- `session_restore.py`: call immediately after `ctx.session.session_id = session_id`
  (next to `reset_session_stats(ctx)`).
- `conversation_service.py`: call after `ctx.session.start()` in the new-session
  branch only.
- Startup (`repl_input_loop.py:110`) unchanged (issue Constraint: no reorder; its
  guards already match the helper's).

Rejected alternatives:
- Helper on `AgentContext` as a method — touches the central DI hub for a narrow
  concern; higher blast radius than a module function with identical semantics.
- Duplicating `set_session_id` calls in each flow — explicitly disfavored by the
  issue AI-instruction ("prefer one shared refresh helper").
- Watching `session_id` via property/event — over-engineering for two known call
  sites (grep-verified exhaustive).

## Implementation steps

1. Phase 1 — write `tests/agent/test_session_correlation_refresh.py` tests 1-5 first
   (tests 4-5 red: flows do not refresh yet).
2. Phase 2 — add `refresh_session_correlation` to `mixin_base.py`; wire calls into
   `session_restore.py` and `conversation_service.py`; Phase 1 tests green.
3. Phase 3 — U-001 check on `agent_web/` wiring (read-only); record outcome.
4. Phase 4 — docs update (`mcp_02_01`), full validation (`rules/toolchain.md`),
   single commit.

## Validation plan

- Targeted: `uv run pytest tests/agent/test_session_correlation_refresh.py tests/agent/commands/test_agent_cmd_session.py tests/agent/test_session_restore.py tests/agent/test_repl.py -x -q`.
- Selected: `tests/agent/test_session*.py` (186-test baseline set).
- Full: `uv run pytest tests/ -q` (baseline 10082 passed / 9 skipped) +
  `rules/toolchain.md` sequence; `lint-imports` must stay 6 kept / 0 broken.
- Static: ruff + mypy on the three changed source files (issue Testing Expectations);
  bandit baseline on these files must not regress.
- Docs: docs checker (per `routing.md`) after `mcp_02_01` edit.

## Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Existing mock-ctx tests break because the new helper call traverses MagicMock ctx (attribute-chain surprises). | Medium | Medium | Helper uses only `services_required.tools` + `session.session_id` (both already exercised by startup guard); characterization sets run in Phase 2 gate. |
| Future session-id change point forgets the helper (invariant decays). | Medium | Medium | Helper docstring states the MUST; helper lives beside `reset_session_stats`, which every flow already calls — a natural co-location; grep-verified call-site inventory recorded in this plan. |
| Double refresh at startup (helper + existing startup call). | Low | Low | Startup flow does not call the helper; `set_session_id` is idempotent fan-out (invoker:73-77) regardless. |
| Collision with sess001 in `session_restore.py` / restore-flow tests. | Low | Medium | sess001 lands first and left `session_restore.py` unmodified; sess003 tests live in a new file; re-verify line references after sess001 (issue Dependencies). |

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first (`tests/agent/test_session_correlation_refresh.py`) | In Progress | — | — | re-verified against HEAD b5c215cdb 2026-10-25 |
| 2 | Phase 2: helper + wiring (`mixin_base.py`, `session_restore.py`, `conversation_service.py`) | In Progress | — | — | `REQ-001`..`REQ-003`, `REQ-005` |
| 3 | Phase 3: U-001 runtime-wiring check (read-only) | Completed | 2026-10-25 | 2026-10-25 | resolved in re-verification: `agent_web/` does not exist; REPL is the only runtime |
| 4 | Phase 4: docs update + full validation, single commit | In Progress | — | — | docs row procedure generated; validation is gate only |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261025-134617_01_scripts_agent_commands_mixin_base.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261025-134617_02_scripts_agent_services_session_restore.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261025-134617_03_scripts_agent_services_conversation_service.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261025-134617_04_tests_agent_test_session_correlation_refresh.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261025-134617_05_docs_22_mcp_mcp_02_01_endpoints-and-transport.md.md | 4 | Procedure | Pending | — | — |

## Traceability

- Implementation step 1 → REQ-001..REQ-003, REQ-005 (failing tests encode AC-001..AC-003).
- Implementation step 2 → REQ-001..REQ-003, REQ-004 (startup untouched), AC-004, AC-005.
- Implementation step 3 → U-001 resolution.
- Implementation step 4 → REQ-006, AC-006.

## Requirement Traceability

| Requirement | Test / Evidence | Acceptance Criterion |
|---|---|---|
| REQ-001 | Helper unit tests 1-3 | AC-001, AC-003 |
| REQ-002 | Restore-flow spy test 4 | AC-001 |
| REQ-003 | Clear-flow spy test 5 | AC-002 |
| REQ-004 | Unmodified REPL wiring tests | AC-004 |
| REQ-005 | Unit tests 2-3 (no-op guards) | AC-003 |
| REQ-006 | `mcp_02_01` diff + docs checker | AC-006 |
