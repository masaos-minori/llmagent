# sess005 — Guard the current session from /session purge retention deletes

**Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`

> Path B (7 target files: 3 source + 2 test + 2 docs). Full analysis run.
> Verification 2026-10-25 — all issue claims confirmed against current source EXCEPT
> one (see Unknowns U-001, disproven): the `/session delete` guard exists
> (`cmd_session.py:65-77` "Cannot delete the current session."); purge chain
> confirmed (`cmd_session.py:229` -> `db_session_ops.py:43-65` ->
> `db_maintenance_service.py:64-70` -> `maintenance.py:205` `purge_old_sessions`);
> both delete rules key on `created_at` (`_delete_sessions_by_age` 167-182,
> `_delete_sessions_beyond_limit` 185-202); `session_restore.py` contains no
> timestamp `UPDATE` (grep-verified); `config/agent.toml:14-15` =
> `sqlite_retention_max_sessions = 100`, `sqlite_retention_max_age_days = 30`;
> `messages.session_id ... ON DELETE CASCADE` (`schema_sql.py:102`);
> `PRAGMA foreign_keys=ON` in write mode (`helper.py:43`). `DbSessionOps.__init__`
> already holds `ctx` (`db_session_ops.py:14-16`) — no `cmd_session.py` edit needed.
> Confidence: High.

## Goal

Retention purge MUST NOT delete the session the agent is actively writing to: thread
an optional current-session id through the purge call chain so both retention rules
(age and count) exempt it, and surface the exemption in the purge output.

## Priority

High (issue-stated). Unrecoverable data loss (`ON DELETE CASCADE` on messages)
triggered by a normal documented workflow (`/session load` of an old session, then a
periodic `/session purge`). Preventive and cheap.

## Scope

In scope:
- Optional `keep_session_id`-style parameter through
  `purge_old_sessions` -> `DbMaintenanceService.purge` -> `DbSessionOps.purge`.
- Exemption in both retention delete rules + reporting the skip.
- Real-DB regression tests + command-level test.
- Two docs (retention policy, `/session purge` operational note).

Out of scope (issue-stated):
- Retention ordering change (`created_at` -> activity-based).
- Cleanup of sessions already corrupted by past purges.
- `/session delete` semantics (guard stays as is).
- Retention config keys/defaults (constraint: unchanged).

## Background

Asymmetry proves the risk is already understood on the manual path: `_session_delete`
guards the active session; the purge path has no equivalent. A loaded old session
keeps its original `created_at` (restore performs no timestamp UPDATE — verified),
so a fully active session can be 30+ days old while the REPL writes to it; the next
purge deletes its row and cascades its messages; subsequent saves then hit FK
IntegrityError (`foreign_keys=ON`) and turns are silently lost. Churn: all three
source targets low-churn (0-1 commits/30d). `purge_old_sessions` is exported from
`scripts/db/__init__.py` for non-agent consumers, so the guard parameter must be
optional (issue Constraint).

## Problem

`/session purge` deletes by age (`DELETE FROM sessions WHERE created_at <
datetime('now', ?)`) and by count (keep `max_sessions` most-recent by `created_at
DESC`) with no active-session exclusion. The live session row and all its messages
can be deleted mid-conversation.

## Reason for Change

Confirmed by code reading (line-precise, 2026-10-25) of the whole purge chain. Data
integrity loss after cascade is unrecoverable; the fix is preventive and small.

## Implementation Intent

Thread an optional current-session id from the command layer (which already holds
`ctx`) down to the two deletion helpers, which exclude it from candidates. No
REPL-global state lookups inside `scripts/db/` (issue AI-instruction). Report the
exemption in the purge result so operators see it.

## Requirements

| ID | Requirement | Priority | Target |
|---|---|---|---|
| REQ-001 | `purge_old_sessions(db, cfg, mode, keep_session_id: int \| None = None)` — optional guard parameter; default None preserves current behavior for non-agent callers. | must | scripts/db/maintenance.py |
| REQ-002 | Both `_delete_sessions_by_age` and `_delete_sessions_beyond_limit` exempt `keep_session_id`; queries stay parameterized. | must | scripts/db/maintenance.py |
| REQ-003 | Purge result surfaces the exemption (e.g. `kept_active_session` in result data) and `DbSessionOps.purge` output states it. | must | scripts/db/maintenance.py, scripts/agent/commands/db_session_ops.py |
| REQ-004 | `DbMaintenanceService.purge` accepts and forwards the current session id. | must | scripts/agent/services/db_maintenance_service.py |
| REQ-005 | `DbSessionOps.purge` passes `self._ctx.session.session_id` (None-safe). | must | scripts/agent/commands/db_session_ops.py |
| REQ-006 | Retention semantics for all other sessions unchanged (age rule, count rule, STRICT/BEST_EFFORT); `/session delete` guard unchanged; config keys unchanged. | must | scripts/db/maintenance.py |
| REQ-007 | Docs state the exemption as policy. | should | docs/41_db/db_06..., docs/23_agent/agent_07_07... |

## Implementation Target Files

> One row per directly affected file.

| File | Action | Contract / Exports to Keep |
|---|---|---|
| scripts/db/maintenance.py | modify | `purge_old_sessions(db, cfg=None, mode=STRICT)` positional order unchanged; guard appended as keyword-with-default (REQ-001); return `MaintenanceResult` shape extended additively (new key in `data`, existing `age_deleted`/`count_deleted`/`sessions_removed` unchanged); parameterized SQL retained; checkpoint/vacuum/recover paths untouched. |
| scripts/agent/services/db_maintenance_service.py | modify | `purge(max_sessions, max_age_days)` signature extended with an optional current-session keyword; forwarding only, no policy logic here. |
| scripts/agent/services/models.py | modify | `DbPurgeResult` gains one optional field `kept_active_session: int \| None = None` (additive; existing constructions unchanged). Added by re-verification: REQ-003 surfacing is impossible without it — the dataclass carries only `sessions_removed` and the service discards `raw.data`. |
| scripts/agent/commands/db_session_ops.py | modify | `purge(rest)` public entry unchanged for `cmd_session.py` call site; adds `self._ctx.session.session_id` forwarding + exemption note in the success line; `CommandValidationError` flows unchanged. |
| tests/db/test_db_maintenance.py | modify | Existing purge tests pass unmodified (keep=None path); add real-DB backdated-session regressions (see Tests). |
| tests/agent/commands/test_agent_cmd_session.py | modify | Existing command tests unmodified; add `/session purge` current-session guard test. |
| docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md | modify | Session retention behavior: active session exempt (policy statement, no code detail). |
| docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md | modify | `/session purge` operational note: current session is never removed; kept-count effect. |

Not edited (verified): `scripts/agent/commands/cmd_session.py` (`DbSessionOps` already
holds `ctx` at `db_session_ops.py:14-16`; dispatch at `cmd_session.py:229` unchanged),
`scripts/agent/services/session_restore.py` (issue's `validate_session_id` claim
disproven — see U-001), `scripts/db/helper.py`, `scripts/db/schema_sql.py`.

## Reference Files

- `scripts/agent/commands/cmd_session.py:65-77` — `_session_delete` guard (behavior model to mirror).
- `scripts/db/maintenance.py:167-230` — the two delete rules + `purge_old_sessions` result construction.
- `scripts/agent/commands/db_session_ops.py:43-65` — purge option parsing + output line ("Purged: N session(s) removed [Session]").
- `scripts/agent/services/db_maintenance_service.py:64-70` — service wrapper (`SQLiteHelper("session")` context ownership stays here; `maintenance.py` receives the open db).
- `scripts/db/schema_sql.py:100-106` — `messages` FK `ON DELETE CASCADE`.
- `scripts/db/helper.py:38-43,161` — FK pragma in write mode.
- `config/agent.toml:14-15` — retention defaults (unchanged).
- `tests/db/test_db_maintenance.py` — existing real-DB maintenance fixtures (pattern for new tests).

## Acceptance Criteria

| ID | Criterion | Maps to |
|---|---|---|
| AC-001 | Backdated active session (older than age limit, real temp DB): purge with guard keeps it AND its `messages` rows; all other expired sessions and only their messages are cascade-deleted. | REQ-001, REQ-002 |
| AC-002 | Count rule: active session beyond `max_sessions` most-recent survives; the `max_sessions` most-recent others are kept as before; exemption surfaced in result data. | REQ-002, REQ-003 |
| AC-003 | `DbSessionOps.purge` success line reports the kept active session when the exemption fired (spy/output-capture test). | REQ-003, REQ-005 |
| AC-004 | `keep_session_id=None` (default): byte-for-byte same SQL behavior as today — all existing purge/maintenance tests pass unmodified. | REQ-001, REQ-006 |
| AC-005 | `/session purge` command test: current session row survives purge; `/session delete` guard test unmodified and passing. | REQ-005, REQ-006 |
| AC-006 | Both docs state the exemption; docs checker passes; ruff + mypy clean on changed files. | REQ-007 |

## Tests

`tests/db/test_db_maintenance.py` (real temp SQLite, existing fixture pattern),
written first (red):
1. Age rule + guard: two sessions backdated beyond the age limit (one is the
   "active" id) + fresh session → `purge_old_sessions(db, cfg, keep_session_id=active)`
   → active survives with its messages; the other expired session and its messages are
   gone; `data["kept_active_session"] == active`.
2. Count rule + guard: `max_sessions=2`, active is 3rd by `created_at` → active
   survives, the other over-limit session deleted.
3. Guard absent (`keep_session_id=None`): expired active-equivalent session IS
   deleted (today's behavior preserved).
4. No-op guard: `keep_session_id` not present in `sessions` → identical counts to
   today.

`tests/agent/commands/test_agent_cmd_session.py`:
5. `/session purge` with ctx whose `session.session_id` is a backdated row in a
   real-DB fixture → current row survives; output mentions the kept session.

Characterization guards: entire existing `tests/db/test_db_maintenance.py`,
`test_agent_cmd_session.py` (incl. the `/session delete` guard test).

## Documentation Impact

- `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` — retention
  policy: the session currently active in the agent is exempt from both rules; when
  exempted it may make the kept count exceed `max_sessions` by one.
- `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` —
  `/session purge` note: current session never removed; output states the exemption.
- Policy wording only, no code detail (issue Documentation Impact); English; docs
  checker must pass.

## Assumptions

| Assumption | Confidence | Verification |
|---|---|---|
| `DbSessionOps` is the only production caller path that needs the guard (`DbMaintenanceService.purge` has no other callers that pass a live session). | High | grep `\.purge(`/`purge_old_sessions` across `scripts/`: only `db_session_ops.py:60` -> `db_maintenance_service.py:70`; non-agent consumers of `scripts/db` use the default `None`. |
| Exempting one session is the correct semantic (vs bumping the effective limit): the kept count may exceed `max_sessions` by one after a guarded purge. | Medium | Design decision recorded in Design; docs state it explicitly; revisit if an operator contract requires a hard cap. |
| `self._ctx.session.session_id` is the authoritative "active session" at purge time. | High | Same value used by the `_session_delete` guard (`cmd_session.py:70`). |

## Unknowns

| ID | Question | Confidence | Blocking | Verification Steps |
|---|---|---|---|---|
| U-001 | Issue Unresolved Question 2 claims `validate_session_id` in `session_restore.py` has a 90-day validity window. **Disproven**: no `validate_session_id`, no 90-day/age window anywhere in `scripts/agent` (grep 2026-10-25). The 30-day purge vs load-consistency follow-up therefore has no current code anchor. | High (absence verified) | No | Do not edit `session_restore.py`. If a validity window is wanted later, file a separate issue; recorded here so the claim is not silently inherited. |
| U-002 | Issue Unresolved Question 1 (report skipped active session as "kept (active)"?) — resolved by decision: YES, surfaced in `MaintenanceResult.data["kept_active_session"]` and in the command success line (issue Required Changes mandates surfacing). | High (decision recorded) | No | Exact output wording finalized in the implementation procedure; AC-003 pins the behavior. |

## Affected areas

- `scripts/db/maintenance.py` — two delete helpers + `purge_old_sessions` signature
  (keyword-default addition; `scripts/db` layer imports nothing new from `agent` —
  guard arrives as a parameter, satisfying the import contract and the issue's
  AI-instruction).
- `agent.services.db_maintenance_service`, `agent.commands.db_session_ops` — one
  forwarded argument each; other ops (health/checkpoint/vacuum/recover) untouched.
- Non-agent consumers of `scripts/db.purge_old_sessions` (exported in
  `scripts/db/__init__.py:23,92`): unaffected via default `None`.
- DB: no schema/config change; `deploy.sh` impact: none.
- Ordering: independent of sess001-004 (no shared target files; overlap checker
  clean). `session_restore.py` overlap dissolved by U-001.

## Design

Chosen shape (issue option "the command/service layer passes the current session_id
down"):

- `purge_old_sessions(db, cfg=None, mode=STRICT, *, keep_session_id: int | None = None)`
  — keyword-only, default None (REQ-001; keeps every existing call site and the
  `scripts/db` public contract intact).
- `_delete_sessions_by_age(db, max_age_days, keep_session_id=None)`: when a guard is
  present, `DELETE FROM sessions WHERE created_at < datetime('now', ?) AND session_id
  != ?` (still parameterized); otherwise the current SQL verbatim.
- `_delete_sessions_beyond_limit(db, max_sessions, keep_session_id=None)`: candidate
  list `rows[max_sessions:]` filtered by `row[0] != keep_session_id`; the active
  session does not consume a keep slot (semantics: exempt on top of the N kept —
  Assumption 2, documented).
- Result: `data` gains `"kept_active_session": keep_session_id if exempted else None`
  (additive key; existing keys unchanged).
- `DbMaintenanceService.purge(max_sessions, max_age_days, *, current_session_id: int | None = None)`
  → forward. `DbSessionOps.purge` → passes `self._ctx.session.session_id`; success
  line appends the kept-session note when the exemption fired.
- No REPL state read inside `scripts/db/` (constraint honored).

Rejected alternatives:
- Look up the live session inside `maintenance.py` — violates layering and the issue
  AI-instruction.
- Switch retention ordering to last-activity — explicitly out of scope.

## Implementation steps

1. Phase 1 — write the failing real-DB tests 1-4 (red).
2. Phase 2 — implement helpers + keyword threading in `maintenance.py`,
   `db_maintenance_service.py`, `db_session_ops.py`; Phase 1 tests green; existing
   maintenance tests green unmodified.
3. Phase 3 — command-level test 5 green.
4. Phase 4 — docs updates + full validation (`rules/toolchain.md`), single commit.

## Validation plan

- Targeted: `uv run pytest tests/db/test_db_maintenance.py tests/agent/commands/test_agent_cmd_session.py -x -q`.
- Full: `uv run pytest tests/ -q` (baseline 10082 passed / 9 skipped) +
  `rules/toolchain.md` sequence; `lint-imports` 6 kept / 0 broken (no new
  cross-layer imports — parameter threading only).
- Static: ruff + mypy on the three changed source files (issue Testing Expectations);
  bandit: the existing `# nosec B608` justification on the placeholder-built DELETE
  stays valid; no new suppressions.
- Docs checkers after the two doc edits (`routing.md` Tools).
- Manual DB safety: validation uses temp DBs only; no production purge executed.

## Adversarial Re-verification (2026-10-25, procedure generation)

Frozen status re-checked against HEAD (all prior citations live; line numbers
confirmed):
- `scripts/db/maintenance.py` — `_delete_sessions_by_age` 167-182,
  `_delete_sessions_beyond_limit` 185-202, `purge_old_sessions` 205-235,
  `MaintenanceResult` dataclass 48, `data` keys 230 (`sessions_removed`/`mode`/
  `max_sessions`/`max_age_days`), `# nosec B608` on the placeholder-built DELETE.
- `scripts/agent/services/db_maintenance_service.py` — `purge` 64-74; line 70
  discards `raw.data` except `sessions_removed`.
- `scripts/agent/commands/db_session_ops.py` — `purge` 43-63; ctx held in
  `__init__` (`self._ctx`), service call at 60, success line 61-63.
- `scripts/agent/commands/cmd_session.py` — guard `_session_delete` 65, message
  71, purge dispatch 229 (`asyncio.to_thread` + `getattr`); `AgentContext` real
  path is `scripts/agent/context.py` (the plan body's `scripts/agent/session.py`
  reference for ctx ownership is loose — ctx is `context.AgentContext`, used at
  `db_session_ops.py:4` import).
- `scripts/db/schema_sql.py:102` messages FK `ON DELETE CASCADE`;
  `config/agent.toml:14-15` `max_sessions=100`, `max_age_days=30`.
- `tests/db/test_db_maintenance.py` — `_FakeDB` (76) wraps a real in-memory
  SQLite with `PRAGMA foreign_keys=ON` and a cascade-capable `_SESSION_SCHEMA`
  (37-50); `_make_session_db` (95) is the fixture the new tests 1-4 must use
  (the plan's "real temp SQLite" is satisfied by this fixture, not by temp files);
  `TestPurgeOldSessions` from 127. `TestRetentionConfig.test_defaults` (113)
  pins the dataclass defaults 100/90; the deployed 100/30 comes from
  `[retention]` config only.
- `tests/agent/commands/test_agent_cmd_session.py` — `TestCmdSessionPurge` at
  513; arg-forwarding assertions at 544 (`assert_called_once_with(10, None)`)
  and 558 (`(None, 30)`); `_make_cmd` at 29 wires `MagicMock(spec=...)` services.
- No purge callers in deploy.sh / init scripts / conf.d; `scripts/db/__init__.py`
  re-exports `purge_old_sessions` (23, 92); private helpers not directly tested.
- Suite collect-only at this HEAD: 10091 tests (supersedes the "10082 passed /
  9 skipped" baseline cited above). `lint-imports`: 6 contracts, 0 broken.

Corrections applied:
- U-001 resolved: `grep` finds no `validate_session_id` in any `scripts/`
  module; `session_restore.py` is not a target file (dissolves the overlap with
  sess004).
- Gap found while validating REQ-003: `DbPurgeResult`
  (`scripts/agent/services/models.py:188`, frozen dataclass) carries only
  `sessions_removed`, and `DbMaintenanceService.purge` discards `raw.data`, so
  the kept-session exemption cannot reach `DbSessionOps.purge` without a field
  addition. A `scripts/agent/services/models.py` target row was added to the
  Implementation Target Files table: `kept_active_session: int | None = None`
  (additive, default-preserving; REQ-001 contract rule satisfied).
- Characterization caveat: making `DbSessionOps.purge` pass
  `current_session_id` to the service changes the mock-arg assertions at
  test_agent_cmd_session.py 544/558; those two existing purge assertions are
  expected to be updated (the "existing tests unmodified" guarantee applies to
  `scripts/db` maintenance/delete tests, not to these cmd-level mock args).

## Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Signature change breaks an unseen `scripts/db` consumer. | Medium | Low | Keyword-only default-None parameter; exported function's positional contract unchanged; suite + `scripts/db/__init__` re-export check. |
| Exempted session makes kept count exceed `max_sessions`, surprising operators. | Low | Medium | Surfaced in result + docs policy statement (AC-002/AC-003). |
| Age-rule SQL branch (`AND session_id != ?`) diverges between guarded/un-guarded paths and hides a regression. | Medium | Low | Tests cover both branches (tests 1-2 guarded, test 3 unguarded). |
| `session_id` None at purge time (no active session) treated as guard for NULL rows. | Low | Low | `None` guard means "no guard" (branch selection), not SQL `!= NULL`; test 4 pins semantics. |

## Execution Status

Blockers:

| Blocker ID | Type | Blocks Step(s) | Owner | Target Date | Status | Notes |
|---|---|---|---|---|---|---|
| U-001 | Unknown | 3 | agent | 2026-10-25 | Resolved | `validate_session_id` does not exist in `scripts/`; `session_restore.py` is not a target file. |

Step execution:

| Step | Work Item | Target File(s) | Procedure Doc | Status | Depends On | Notes |
|---|---|---|---|---|---|---|
| — | Plan | — | — | Frozen | — | Re-verified 2026-10-25; `models.py` target row added for REQ-003. |
| 1 | Phase 1: failing real-DB tests 1-4 (red) | `tests/db/test_db_maintenance.py` | `20261025-141651_05_tests_db_test_db_maintenance.py.md` | In Progress | — | Uses `_make_session_db` fixture (real in-memory SQLite, FK ON). |
| 2 | Phase 2: helpers + keyword threading, Phase 1 green | `scripts/db/maintenance.py`, `scripts/agent/services/db_maintenance_service.py`, `scripts/agent/services/models.py`, `scripts/agent/commands/db_session_ops.py` | `20261025-141651_01_scripts_db_maintenance.py.md`, `20261025-141651_02_scripts_agent_services_db_maintenance_service.py.md`, `20261025-141651_03_scripts_agent_services_models.py.md`, `20261025-141651_04_scripts_agent_commands_db_session_ops.py.md` | Pending | 1 | TDD red → green; `lint-imports` 6 kept. |
| 3 | Phase 3: command-level test 5; update mock-arg assertions 544/558 | `tests/agent/commands/test_agent_cmd_session.py` | `20261025-141651_06_tests_agent_commands_test_agent_cmd_session.py.md` | Pending | 2 | Re-verification caveat: 544/558 assertions change with the new kwarg. |
| 4 | Phase 4a: docs policy statements | `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`, `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | `20261025-141651_07_docs_41_db_db_06_api_and_operations-maintenance-and-rotation.md.md`, `20261025-141651_08_docs_23_agent_agent_07_07_cli-and-commands-slash-commands-session-mcp.md.md` | Pending | 2, 3 | Docs checkers after edits. |
| 5 | Phase 4b: full validation, single commit | gate only; modifies no file | — | Pending | 1-4 | `rules/toolchain.md` sequence; collect-only baseline 10091. |

Work Items Created:

| Procedure Doc | Target File | Status |
|---|---|---|
| `20261025-141651_01_scripts_db_maintenance.py.md` | `scripts/db/maintenance.py` | Created |
| `20261025-141651_02_scripts_agent_services_db_maintenance_service.py.md` | `scripts/agent/services/db_maintenance_service.py` | Created |
| `20261025-141651_03_scripts_agent_services_models.py.md` | `scripts/agent/services/models.py` | Created |
| `20261025-141651_04_scripts_agent_commands_db_session_ops.py.md` | `scripts/agent/commands/db_session_ops.py` | Created |
| `20261025-141651_05_tests_db_test_db_maintenance.py.md` | `tests/db/test_db_maintenance.py` | Created |
| `20261025-141651_06_tests_agent_commands_test_agent_cmd_session.py.md` | `tests/agent/commands/test_agent_cmd_session.py` | Created |
| `20261025-141651_07_docs_41_db_db_06_api_and_operations-maintenance-and-rotation.md.md` | `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` | Created |
| `20261025-141651_08_docs_23_agent_agent_07_07_cli-and-commands-slash-commands-session-mcp.md.md` | `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | Created |

## Traceability

- Implementation step 1 → REQ-001, REQ-002, REQ-006 (tests 1-4 encode AC-001, AC-002, AC-004).
- Implementation step 2 → REQ-001..REQ-004, REQ-006; AC-001..AC-002, AC-004.
- Implementation step 3 → REQ-003, REQ-005; AC-003, AC-005.
- Implementation step 4 → REQ-007; AC-006.

## Requirement Traceability

| Requirement | Test / Evidence | Acceptance Criterion |
|---|---|---|
| REQ-001 | Tests 1-4 (signature + default path) | AC-001, AC-004 |
| REQ-002 | Tests 1-2 (both rules), test 4 (parameterized no-op) | AC-001, AC-002 |
| REQ-003 | Result-data assertion in tests 1-2; output capture test 5 | AC-002, AC-003 |
| REQ-004 | Command-level wiring through service in test 5 | AC-005 |
| REQ-005 | Test 5 (ctx session survives purge) | AC-003, AC-005 |
| REQ-006 | Unmodified existing maintenance/delete tests | AC-004, AC-005 |
| REQ-007 | Docs diff + docs checker | AC-006 |
