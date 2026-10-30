# Plan: Make stale-attempt recovery timezone-safe and ownership-aware

**Task Classification:** Path B (more than 3 files; adds `attempts` columns to the `workflow.sqlite` schema; adds a shared timestamp helper). Path B analysis applied (`skills/issue-to-plan/workflow-path-b.md`); design choices recorded in `Design`.

## Goal
- Make stale-attempt recovery work on the timestamps production writes, never treat a live attempt as stale, and decide staleness from attempt ownership and a lease instead of a fixed elapsed-time threshold.

## Priority
Medium

## Scope
- **In-Scope**: one strict UTC ISO-8601 parser in `scripts/shared/json_utils.py`; timezone-independent recovery; observable handling of unparseable `started_at`; `owner_id` and `lease_expires_at` on `attempts` with a registered migration; lease set at attempt start from the stage timeout; conditional takeover; a conservative rule and documented manual path for legacy rows without a lease; tests with production-format timestamps; documentation and ADR-001 INV-07 wording.
- **Out-of-Scope**: attempt numbering, ledger semantics, and task transitions (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`); retry policy and failure propagation (`issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md`); changing the output of `now_iso()`; periodic lease renewal (UNK-02); the unrelated local `Z` parse in `scripts/agent/memory/scoring.py`.
- **Dependencies**: (1) Phase 2 (schema) depends on `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3 (workflow domain wiring). (2) Phases 2-3 follow `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (Phases 2-3 there): both change the attempt row and `recover_stale_attempts`; the lease fields are added to its contract and its conditional `finish_attempt` provides the fencing. Phase 1 does not depend on it. (3) Shared files with other Frozen Plans: see Assumptions.

## Background
- `now_iso()` (`scripts/shared/json_utils.py:45`) returns `YYYY-MM-DDTHH:MM:SSZ`; the workflow DDL defaults (`scripts/db/schema_sql.py:172-203`) use the same format. `StateStore.find_stale_running_attempts()` (`state_store.py:217`) parses with `time.strptime(started_at, "%Y-%m-%dT%H:%M:%S")`, which raises `ValueError: unconverted data remains: Z` for every production row (reproduced on Python 3.13.5); the method swallows it with `continue`, so recovery never recovers a production attempt (checked in Step 3).
- The parsed value goes through `time.mktime` (local time) while the stored value is UTC; `_STALE_GRACE_SEC = 30` (`state_store.py:22-23`) is shorter than the execute stage `timeout_sec` of 120 (`config/workflows/default.json`).
- Tests hide the defect: seeds use `"2026-01-01T00:00:00"` without `Z` (`tests/agent/workflow/test_workflow_state_store.py:285,335,359`) and `tests/agent/workflow/test_state_store.py` mocks `find_stale_running_attempts` or feeds `"not-a-date"` (`:210-222`).
- Recovery runs once in `Orchestrator.__init__` (`scripts/agent/orchestrator.py:92`). `attempts` has no owner or lease column. No worker or process identity exists in `scripts/` (the only `worker_id` is the session ID at `audit_event_emitter.py:84`), and no process lock or single-instance guard exists, so two agent processes can open one `workflow.sqlite`.
- `WorkflowEngine._run_stage` enforces the stage deadline with `asyncio.wait_for(fn(), timeout=timeout_sec)` (`workflow_engine.py:224`), so a normally running stage cannot outlive `timeout_sec`.

## Problem
Recovery cannot parse production timestamps and so recovers nothing; if only the parser is fixed, a second process would mark another process's live long stage `failed` after 30 seconds; an unparseable `started_at` leaves an attempt `running` forever with no diagnostic.

## Reason for Change
Parsing and liveness are one decision; fixing either alone yields a wrong outcome. The parsing defect is in effect today and makes the existing recovery code dead in production. Medium: recovery output is not currently consumed by a production resume path (see the wfrecovery001 Plan), so the visible effect is stale `running` rows.

## Implementation Intent
- One strict, timezone-aware UTC parser for what `now_iso()` writes; no local time.
- Unparseable timestamps are reported, not silently ignored.
- A lease written at attempt start as `now + stage timeout + margin`: because the engine enforces the stage deadline, no renewal is needed in the normal path; staleness means the lease expired.
- Takeover is a conditional update on the expected owner and lease, requiring one row; a fenced owner's late finish fails on the wfrecovery001 conditional finish.
- Legacy rows without a lease use a conservative age rule and a documented manual path.

## Requirements
- `REQ-001`: Add `parse_iso_utc(value)` to `scripts/shared/json_utils.py`: returns an aware UTC `datetime`; accepts `Z`, explicit offsets (converted to UTC), and fractional seconds; raises `ValueError` for naive and malformed strings.
- `REQ-002`: Recovery parses `started_at` and `lease_expires_at` only with `parse_iso_utc` and never with `time.mktime` or local time; results do not depend on the host timezone.
- `REQ-003`: An unparseable persisted timestamp is logged (warning, attempt ID, value), counted in a distinct recovery outcome, and not treated as stale or silently skipped; recovery exposes the counts (recovered, still-live, legacy-recovered, unparseable) through a report while `recover_stale_attempts()` keeps returning the recovered count.
- `REQ-004`: Add nullable `owner_id TEXT` and `lease_expires_at TEXT` to `attempts` through a registered forward-only migration step (after the wfrecovery001 schema step), bump `WORKFLOW_SCHEMA_VERSION`, and add the columns to `REQUIRED_WORKFLOW_TABLES`.
- `REQ-005`: Attempt start records `owner_id` (a per-process identifier created once: host, process ID, random suffix) and `lease_expires_at = now + stage timeout_sec + margin`; the engine passes the stage timeout and margin; the margin is a named constant.
- `REQ-006`: An attempt is stale only when its lease is expired; an unexpired lease is never recovered, including by another process; the fixed 30-second rule (`_STALE_GRACE_SEC`) is removed.
- `REQ-007`: Takeover is a conditional update on the attempt ID, `status='running'`, and the expected `owner_id` and `lease_expires_at`, requiring exactly one updated row; two racing recoverers yield one takeover; a late finish by the fenced owner is rejected by the wfrecovery001 conditional finish and surfaces as a typed error.
- `REQ-008`: A `running` attempt with no lease (legacy) is recovered only when `started_at` parses and is older than a conservative constant age; legacy rows with an unparseable `started_at` are reported and left for the documented manual recovery.
- `REQ-009`: Tests use the literal production timestamp format and cover the parser cases, the host-timezone independence, a live lease held while a second process recovers, owner death with lease expiry, a takeover race, repeated recovery, malformed and legacy rows, and migration on a database with existing `running` rows; the mock-only and naive-timestamp seeds are replaced.
- `REQ-010`: Update the `agent_03_03` "Startup Recovery" section (lease semantics, timestamp format contract, manual recovery of legacy and unparseable rows) and amend ADR-001 INV-07 so that "interrupted Attempt" means a lease-expired attempt, under the ADR change protocol.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on 2026-10-30: every row exists, or is a new file in an existing directory with "New file" stated, requires modification, cites checkable evidence, and links to a Requirement; existing paths confirmed on branch `docs/issues-workflow-persistence`).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/json_utils.py` | Add the strict UTC parser | No ISO-8601 parser exists in `scripts/shared/`; only a local `Z` replace in `scripts/agent/memory/scoring.py:25` | REQ-001 / AC-1 | `json_utils.py:45-51` `now_iso`; `rg fromisoformat scripts/shared` empty (checked in Step 3) | `tests/shared/test_json_utils.py` | Verified |
| `scripts/agent/workflow/state_store.py` | Parse, report, lease-based detection, conditional takeover; drop the fixed grace | `time.strptime` without `Z` at `:232`, `time.mktime`, `_STALE_GRACE_SEC` at `:22-23`, silent `continue` | REQ-002, REQ-003, REQ-006, REQ-007, REQ-008 / AC-2..AC-7 | `state_store.py:22-23,217-282` (checked in Step 3) | `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py` | Verified |
| `scripts/agent/workflow/attempt_ops.py` | Set `owner_id` and `lease_expires_at` when an attempt starts | Attempt insert has no ownership fields | REQ-004, REQ-005 / AC-5 | `attempt_ops.py:12-31` (checked in Step 3) | `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `scripts/agent/workflow/idempotency_ops.py` | Carry the lease duration into the attempt-start transaction | `begin_stage_if_new` inserts the attempt row without ownership | REQ-005 / AC-5 | `idempotency_ops.py:18-67` (checked in Step 3) | `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `scripts/agent/workflow/workflow_engine.py` | Pass stage `timeout_sec` plus margin as the lease; define the margin constant | `_run_stage` knows the stage timeout at attempt start | REQ-005 / AC-5 | `workflow_engine.py:188-224` (checked in Step 3) | `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `scripts/db/schema_sql.py` | Add `owner_id`, `lease_expires_at`; bump version | `attempts` DDL lacks ownership columns | REQ-004 / AC-8 | `schema_sql.py:184-194`, `:25` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `scripts/agent/services/workflow_schema.py` | Require the new columns at startup | `REQUIRED_WORKFLOW_TABLES` lists attempt columns without them | REQ-004 / AC-8 | `workflow_schema.py:44-50`, version compare `:114` (checked in Step 3) | `tests/agent/test_repl_health.py` | Verified |
| `tests/shared/test_json_utils.py` | Parser tests | `now_iso` tests at `:383`; no parser tests | REQ-001, REQ-009 / AC-1 | `test_json_utils.py:383` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_state_store.py` | Production-format seeds; lease and takeover tests | Naive seeds at `:285,335,359`; recovery tests `:285-535` | REQ-002, REQ-006, REQ-007, REQ-009 / AC-2..AC-7 | `test_workflow_state_store.py:285-535` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_state_store.py` | Replace mock-only and invalid-timestamp tests | `"not-a-date"` test at `:210-222`; mocked detection | REQ-003, REQ-009 / AC-2, AC-3 | `test_state_store.py:14-231` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_engine.py` | Assert the lease passed at attempt start | Existing engine and timeout tests (`:161-230`) | REQ-005, REQ-009 / AC-5 | `test_workflow_engine.py:161-185` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_stale_recovery_lease.py` | New multi-connection, crash, TZ, race, and legacy-row tests | New file: no multi-connection recovery test exists; directory exists | REQ-007, REQ-008, REQ-009 / AC-4..AC-7 | `ls tests/agent/workflow` (checked in Step 3) | itself | Verified |
| `tests/db/test_create_schema.py` | Column and migration tests | DDL copy `:359`; schema tests | REQ-004, REQ-009 / AC-8 | `test_create_schema.py:359` (checked in Step 3) | itself | Verified |
| `tests/agent/test_repl_health.py` | Update workflow-table fixtures for the new required columns | Minimal `CREATE TABLE` fixtures `:540-590` | REQ-004 / AC-8 | `test_repl_health.py:540-590` (checked in Step 3) | itself | Verified |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Rewrite "Startup Recovery" | States recovery marks active attempts failed by elapsed time and never changes task status | REQ-010 / AC-9 | `agent_03_03_...md:143-146` (checked in Step 3) | docs checkers | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | INV-07 wording | "interrupted Attempts" needs the lease definition | REQ-010 / AC-9 | `adr_02_02_001_...md:171,187` (checked in Step 3) | `tools/check_adr_preservation.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. No directory, glob, component name, file group, or vague phrase appears as a row.
- A test, configuration, schema, migration, deployment, or documentation file is its own row when it requires modification.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section is `Frozen`.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/orchestrator.py` | Calls `recover_stale_attempts(get_connection())` at `:92`; unchanged while the signature is kept | REQ-002 |
| `scripts/db/helper.py` | `begin_immediate()` and `execute` cursor `rowcount` for conditional updates | REQ-007 |
| `config/workflows/default.json` | Stage `timeout_sec` values the lease derives from | REQ-005 |
| `scripts/agent/memory/scoring.py` | Existing local `fromisoformat` handling of `Z` (`:25`), not modified | REQ-001 |
| `scripts/db/create_schema.py` | Version guard that makes the schema change migration-gated (`:54-77`) | REQ-004 |
| `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` | Migration registry and backup gate | REQ-004 |
| `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` | Attempt contract, conditional finish, atomic recovery this Plan extends | REQ-005, REQ-007 |
| `tools/check_db_separation.py` | Table-ownership inventory; run after DDL changes | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): `parse_iso_utc` returns the correct UTC instant for `Z`, `+09:00`-style offsets, and fractional seconds, and raises `ValueError` for naive and malformed input; a test uses `now_iso()` output.
- AC-2 (REQ-002): recovery of an attempt whose `started_at` is `now_iso()` output works under `TZ=UTC` and under a non-UTC `TZ` with the same result; `rg "mktime|strptime" scripts/agent/workflow` is empty.
- AC-3 (REQ-003): an unparseable `started_at` or `lease_expires_at` yields a warning log, an `unparseable` count in the report, and an attempt that is neither recovered nor silently dropped.
- AC-4 (REQ-006): an execute attempt running longer than 30 seconds with an unexpired lease is not recovered by a second process.
- AC-5 (REQ-005): a started attempt has `owner_id` and `lease_expires_at` equal to start plus the stage `timeout_sec` plus the margin.
- AC-6 (REQ-006, REQ-007): after the lease expires without a finish, recovery marks the attempt `failed` once; repeated recovery changes nothing; two concurrent recoverers produce exactly one takeover.
- AC-7 (REQ-007, REQ-008): a late `finish_attempt` from the fenced owner raises a typed error; a legacy `running` row older than the legacy age is recovered once and a younger or unparseable one is not.
- AC-8 (REQ-004): a database at the previous version with existing `running` rows migrates with the new columns null; `check_workflow_schema` fails when a required new column is missing; the version differs from the previous value.
- AC-9 (REQ-010): the documentation and ADR-001 INV-07 describe the implemented semantics and the manual recovery path, and the docs and ADR checkers pass with each ADR change explained.

## Tests
- `REQ-001`: `tests/shared/test_json_utils.py` (`Z`, offset, fractional, malformed, naive).
- `REQ-002`, `REQ-003`: `tests/agent/workflow/test_workflow_state_store.py`, `test_state_store.py`, `test_stale_recovery_lease.py` (production-format timestamps, `TZ` set with `monkeypatch` and `time.tzset()`, malformed rows).
- `REQ-004`: `tests/db/test_create_schema.py`, `tests/agent/test_repl_health.py` (columns, startup check, migration on `running` rows).
- `REQ-005`: `tests/agent/workflow/test_workflow_engine.py`, `test_workflow_state_store.py`.
- `REQ-006`..`REQ-008`: `tests/agent/workflow/test_stale_recovery_lease.py` (two connections, owner death, race, fencing, legacy rows).
- `REQ-009`: the replaced seeds across the files above.
- `REQ-010`: docs and ADR checkers.

## Documentation Impact
Yes: `REQ-010`. `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` "Startup Recovery" and ADR-001 INV-07 (Accepted ADR; change protocol applies), located through `docs/00_index.md` "Document References by Task": intent, ownership semantics, timestamp contract, and operational manual recovery; no DDL or code restatement. `docs/41_db/db_02_architecture_and_schema-schema-reference.md` section 7 names tables only and is not a target. Record the multi-process assumption as a Needs Confirmation item if unresolved (UNK-01).

## Assumptions
- `workflow.sqlite` is a local file used by processes on one host, so UTC wall-clock comparison of `lease_expires_at` is meaningful; clock steps are covered by the margin and the fencing by the conditional update.
- The lease margin is a named constant (30 seconds), and the legacy age is a named constant (3600 seconds); both are conservative relative to the 120-second execute timeout and are not configuration (UNK-03, UNK-04).
- Step 8b overlap judgments (`tools/check_plan_target_overlaps.py`, 2026-10-30): `state_store.py`, `attempt_ops.py`, `idempotency_ops.py`, `workflow_engine.py`, `workflow_schema.py`, `schema_sql.py`, `test_state_store.py`, `test_workflow_state_store.py`, `test_workflow_engine.py`, `test_repl_health.py`, `test_create_schema.py`, `agent_03_03_...md`, and ADR-001 with the wfrecovery001 Plan: sequencing dependency (that Plan defines the attempt contract and atomic recovery; this Plan adds ownership fields and lease-based detection on top; Phase 1 here is independent; both amend INV-07 and the "Startup Recovery" section, and the later one reconciles the wording). `schema_sql.py` with dbmig001, toolexec001, ragcorpus001, wftaskapi001: sequencing dependency, all register through the dbmig001 workflow registry and edit different DDL regions (`attempts` columns here). `state_store.py` and `workflow_engine.py` with toolexec001, and the task files with wftaskapi001: compatible (different methods and regions).
- Schema version numbering (second-pass verification, 2026-10-30): this Plan, wfrecovery001, wflease001, wftaskapi001, and toolexec001 each bump `WORKFLOW_SCHEMA_VERSION` from `1.1.0`. Version numbers are not fixed in the Plans; they are assigned in landing order when the migration steps are registered, and each step's source version equals the previous step's target version (the dbmig001 registry records source and target versions per migration). Two Plans must not target the same version.
- Verification record (second pass, 2026-10-30): no Implementation Target Files row changed on `origin/master` since the merge base; every `path:line` citation lies within its file; `parse_iso_utc` does not collide with an existing name; recovery is the only reader of `attempts.started_at` outside the workflow package's own writers.
- The migration registration module is defined by the dbmig001 plan (`scripts/db/migrations_workflow.py`, absent today) and is added to this Plan by amendment when it lands (UNK-05).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether more than one agent process on one `workflow.sqlite` is a supported mode | No process lock exists; the owner answered only the lease question on 2026-10-30 (see UNK-02), not whether this mode is supported | Design is safe either way; record as a Needs Confirmation item in docs | False |
| UNK-02 | (Decided by the owner on 2026-10-30) No periodic lease renewal | Resolved: the owner chose the deadline lease without heartbeat | The engine enforces `timeout_sec`; a heartbeat would add event-loop DB writes (`BEGIN IMMEDIATE` waits up to 30000 ms under contention) | False |
| UNK-03 | Lease margin value and whether it should be configuration | No operational data | Default constant 30 s; promote to configuration if the owner asks | False |
| UNK-04 | Legacy-row age (3600 s) and handling of unparseable legacy rows | Production rows not inspected (`rules/ai-execution.md` Repository Tool Usage item 7) | Conservative default; unparseable rows reported and left for the documented manual path | False |
| UNK-05 | dbmig001 registry API and registration module | `scripts/db/migrations_workflow.py` planned, absent | Open dependency `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3; Phase 2 starts only after it; amend target files at procedure generation | False |
| UNK-06 | Landing order against wfrecovery001 | That Plan's rows are Pending | Open dependency `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`; Phases 2-3 here start after its Phase 3; Phase 1 is independent | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/json_utils.py` | Modify | Medium: shared helper module | 0 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | Modify | High: 84 test references in 7 files | 2 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/attempt_ops.py` | Modify | Medium | 0 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | Medium | 0 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_engine.py` | Modify | High: 54 test references in 3 files | 1 | High (single contributor) | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | Modify | High: version guards, sibling plans | 12 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/services/workflow_schema.py` | Modify | Medium: startup check, grade C (12) | 3 | High (single contributor) | not applicable (rsynced) |
| `tests/shared/test_json_utils.py` | Modify | Low | 1 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Low | 4 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_state_store.py` | Modify | Low | 0 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | Low | 2 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_stale_recovery_lease.py` | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low | 15 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/test_repl_health.py` | Modify | Low | 6 | High (single contributor) | not applicable (rsynced) |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Low | 23 | High (single contributor) | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Medium: Accepted ADR | 5 | High (single contributor) | not applicable (rsynced) |

## Design
- **Parser.** Alternatives: (a) a new shared `parse_iso_utc`; (b) reuse the local `fromisoformat(...replace("Z", "+00:00"))` in `scoring.py`. Chosen (a), strict (rejects naive input), so a malformed row cannot be silently read as a local time; (b) is not reusable from `agent.workflow` without a cross-module import of an unrelated module. `scoring.py` is left unchanged.
- **Lease without heartbeat.** Alternatives: (a) deadline lease `now + timeout_sec + margin`, no renewal; (b) a heartbeat task renewing a short lease. Chosen (a): `asyncio.wait_for` already bounds a normal stage, so a lease beyond that bound can only be reached by a dead or stuck owner; a stuck owner is fenced because its later conditional finish fails. (b) shortens takeover delay but adds event-loop writes that can wait up to the 30000 ms busy timeout under contention; it stays an option (UNK-02).
- **Owner identity.** One identifier per process (host, process ID, random suffix), created once; a bare PID can be reused, so the random part is required.
- **Detection.** `lease_expires_at` parsed and compared with the current UTC time; no lease column value means a legacy row, handled by REQ-008. The fixed 30-second rule is removed.
- **Interim safety.** Phase 1 fixes parsing and replaces the 30-second rule with the conservative legacy age, so recovery works in production without ever stealing a live attempt before leases exist.
- **Report API.** `recover_stale_attempts()` keeps returning the recovered count (18 test references in 2 files rely on it); a report object carries the other counts.
- **Migration.** Two nullable `ADD COLUMN` steps registered in the dbmig001 workflow registry after the wfrecovery001 steps; existing rows keep null values; rollback by the pre-migration backup.
- **Layering.** `parse_iso_utc` lives in `shared`, imported by `agent.workflow`; `lint-imports` baseline 6 kept, 0 broken (2026-10-30).

## Implementation steps
1. **Phase 1: Timezone-safe parsing and conservative detection (no schema change; independent)**
   - [ ] Add `parse_iso_utc` and its tests (REQ-001, REQ-009; `scripts/shared/json_utils.py`, `tests/shared/test_json_utils.py`).
   - [ ] Parse with it in `find_stale_running_attempts`, report unparseable rows, replace the 30-second rule with the legacy age (REQ-002, REQ-003, REQ-006, REQ-008; `scripts/agent/workflow/state_store.py`).
   - [ ] Replace naive seeds and mock-only tests; add `TZ` and malformed-row tests (REQ-002, REQ-003, REQ-009; `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`).
2. **Phase 2: Schema (starts after dbmig001 Phase 3 and wfrecovery001 Phase 2)**
   - [ ] Add `owner_id` and `lease_expires_at`, bump the version, extend required columns, and register the migration steps (REQ-004; `scripts/db/schema_sql.py`, `scripts/agent/services/workflow_schema.py`; registration module added by amendment, UNK-05).
   - [ ] Column, startup-check, and migration tests (REQ-004, REQ-009; `tests/db/test_create_schema.py`, `tests/agent/test_repl_health.py`).
3. **Phase 3: Ownership and lease-based recovery (after wfrecovery001 Phase 3)**
   - [ ] Record owner and lease at attempt start; engine passes the stage timeout and margin (REQ-005; `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/workflow_engine.py`).
   - [ ] Lease-based detection and conditional takeover (REQ-006, REQ-007; `scripts/agent/workflow/state_store.py`).
   - [ ] Tests: live lease, owner death, race, fencing, repeated recovery (REQ-005..REQ-009; `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`).
4. **Phase 4: Documentation and ADR**
   - [ ] Rewrite "Startup Recovery" and amend INV-07 under the ADR change protocol (REQ-010; `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`); run the docs and ADR checkers.
5. **Phase 5: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Prerequisite: the dbmig001 migration for the retained `/opt/llm/db/workflow.sqlite` has run with its backup gate; verify with the startup schema check and `uv run python tools/check_db_separation.py` (REQ-004; `scripts/db/schema_sql.py`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/json_utils.py` | Unit: parser cases | `uv run pytest tests/shared/test_json_utils.py -v` | All pass |
| `scripts/agent/workflow/` | Unit + multi-connection recovery | `uv run pytest tests/agent/workflow/ -v` | All pass; new tests fail on the pre-change code |
| Startup check and fixtures | Integration | `uv run pytest tests/agent/test_repl_health.py tests/db/ -v` | All pass; migration preserves rows |
| Schema ownership | Static | `uv run python tools/check_db_separation.py` | Pass |
| Source quality | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py` | Clean; 6 contracts kept; `state_store.py` (11164 B) stays under 20480 B |
| Changed-line coverage | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | at least 90% (baseline without threshold: no covered lines in the current diff, which contains only documents) |
| `docs/` and ADR | Static | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`, `check_adr_preservation.py` | Pass; each ADR change reported and explained |

Baselines recorded 2026-10-30: radon (grade C or worse in the scanned set): `workflow_schema.check_workflow_schema` C (12); `state_store.py` and `json_utils.py` none. vulture: 16 findings, none in these files. bandit: 0 medium or high repository-wide (51 low). Operational check: production database locks (`fuser`) not run; planning does not touch `/opt/llm/` (`rules/ai-execution.md` Repository Tool Usage item 7); `pip-audit` not applicable (no dependency change).

## Risks
- **Risk**: making recovery work in production for the first time could mark a legitimately running attempt `failed` → **Mitigation**: Phase 1 uses only the conservative legacy age (3600 s versus a 120 s stage), and leases protect live attempts from Phase 3 on; AC-4.
- **Risk**: wall-clock skew or a clock step makes a lease look expired → **Mitigation**: single-host assumption, margin, and fencing through the conditional finish.
- **Risk**: legacy rows with an unparseable `started_at` remain `running` → **Mitigation**: reported on every recovery and handled by the documented manual path (REQ-003, REQ-008, REQ-010).
- **Risk**: a stuck owner finishes after takeover → **Mitigation**: the wfrecovery001 conditional finish rejects it; AC-7.
- **Risk**: wide blast radius (`StateStore` 84 references in 7 test files; `recover_stale_attempts` 18 in 2; `schema_sql.py` 12 commits in 30 days with five Frozen Plans targeting it) exceeds the `rules/toolchain.md` Impact-radius threshold; recorded here → **Mitigation**: return type of `recover_stale_attempts` kept; sequencing recorded; each phase leaves the suite green.
- **Risk**: another plan's migration step claims the same target version → **Mitigation**: version numbers assigned in landing order (Assumptions).
- **Risk**: single-contributor files (bus factor High) → **Mitigation**: small, independently revertable phases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Timezone-safe parsing and conservative detection | Pending | — | — | Independent of the other phases |
| 2 | Phase 2: Schema | Pending | — | — | Starts after dbmig001 Phase 3 and wfrecovery001 Phase 2 |
| 3 | Phase 3: Ownership and lease-based recovery | Pending | — | — | After wfrecovery001 Phase 3 |
| 4 | Phase 4: Documentation and ADR | Pending | — | — | |
| 5 | Phase 5: Deployment & Verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-114516
- **Related target files**: `scripts/shared/json_utils.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/db/schema_sql.py`, `scripts/agent/services/workflow_schema.py`, `tests/shared/test_json_utils.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/db/test_create_schema.py`, `tests/agent/test_repl_health.py`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; Background (parser) | `scripts/shared/json_utils.py` | Phase 1 | AC-1 | `tests/shared/test_json_utils.py` | Confirmed by repository evidence |
| REQ-001 | Testing Expectations 1 | `tests/shared/test_json_utils.py` | Phase 1 | AC-1 | `uv run pytest tests/shared/test_json_utils.py` | Explicit in issue |
| REQ-002 | Implementation Intent 1; Acceptance Criteria 6 | `scripts/agent/workflow/state_store.py` | Phase 1 | AC-2 | `tests/agent/workflow/test_stale_recovery_lease.py` | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria 6 | `tests/agent/workflow/test_workflow_state_store.py` | Phase 1 | AC-2 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-003 | Required Changes 2; Acceptance Criteria 2 | `scripts/agent/workflow/state_store.py` | Phase 1 | AC-3 | `tests/agent/workflow/test_state_store.py` | Confirmed by repository evidence |
| REQ-003 | Testing Expectations 2 | `tests/agent/workflow/test_state_store.py` | Phase 1 | AC-3 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-004 | Required Changes 3; Constraints 1 | `scripts/db/schema_sql.py` | Phase 2 | AC-8 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 3 | `scripts/agent/services/workflow_schema.py` | Phase 2 | AC-8 | `tests/agent/test_repl_health.py` | Derived from confirmed evidence |
| REQ-004 | Testing Expectations 5 | `tests/db/test_create_schema.py` | Phase 2 | AC-8 | `uv run pytest tests/db/` | Explicit in issue |
| REQ-004 | Background (startup check) | `tests/agent/test_repl_health.py` | Phase 2 | AC-8 | `uv run pytest tests/agent/test_repl_health.py` | Derived from confirmed evidence |
| REQ-005 | Required Changes 3-4; Background (deadline) | `scripts/agent/workflow/attempt_ops.py` | Phase 3 | AC-5 | `tests/agent/workflow/test_workflow_engine.py` | Derived from confirmed evidence |
| REQ-005 | Required Changes 4 | `scripts/agent/workflow/idempotency_ops.py` | Phase 3 | AC-5 | `tests/agent/workflow/test_workflow_engine.py` | Derived from confirmed evidence |
| REQ-005 | Required Changes 4 | `scripts/agent/workflow/workflow_engine.py` | Phase 3 | AC-5 | `tests/agent/workflow/test_workflow_engine.py` | Derived from confirmed evidence |
| REQ-005 | Required Changes 4 | `tests/agent/workflow/test_workflow_engine.py` | Phase 3 | AC-5 | `uv run pytest tests/agent/workflow/` | Derived from confirmed evidence |
| REQ-006 | Required Changes 4; Acceptance Criteria 3 | `scripts/agent/workflow/state_store.py` | Phases 1, 3 | AC-4, AC-6 | `tests/agent/workflow/test_stale_recovery_lease.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes 5; Acceptance Criteria 4-5 | `scripts/agent/workflow/state_store.py` | Phase 3 | AC-6, AC-7 | `tests/agent/workflow/test_stale_recovery_lease.py` | Explicit in issue |
| REQ-007 | Testing Expectations 3-4 | `tests/agent/workflow/test_stale_recovery_lease.py` | Phase 3 | AC-6, AC-7 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-008 | Required Changes (manual recovery); Unresolved Questions | `scripts/agent/workflow/state_store.py` | Phase 1 | AC-7 | `tests/agent/workflow/test_stale_recovery_lease.py` | Derived from confirmed evidence |
| REQ-008 | Required Changes (manual recovery) | `tests/agent/workflow/test_stale_recovery_lease.py` | Phase 3 | AC-7 | `uv run pytest tests/agent/workflow/` | Derived from confirmed evidence |
| REQ-009 | Required Changes 6; Testing Expectations | `tests/agent/workflow/test_workflow_state_store.py` | Phases 1, 3 | AC-2..AC-7 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-009 | Testing Expectations 2 | `tests/agent/workflow/test_state_store.py` | Phase 1 | AC-3 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-010 | Documentation Impact | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 4 | AC-9 | docs checkers | Confirmed by repository evidence |
| REQ-010 | Documentation Impact | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 4 | AC-9 | `check_adr_preservation.py` | Confirmed by repository evidence |
