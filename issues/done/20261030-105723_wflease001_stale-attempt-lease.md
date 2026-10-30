# Make stale-attempt recovery timezone-safe and ownership-aware

## Priority
Medium

## Summary
Stale-attempt recovery cannot parse the timestamps production writes, so it recovers nothing, and its fixed 30-second threshold would steal a healthy long-running attempt once the parser works. Parse one canonical UTC format, report unparseable rows, and decide staleness from attempt ownership and a lease instead of elapsed time alone.

## Background
Source: `memo-issue.md` entry M-01 (consolidating M-01 and M-02). Re-checked against current source on 2026-10-30:

- Confirmed, and stronger than the memo states: `now_iso()` in `scripts/shared/json_utils.py` returns `YYYY-MM-DDTHH:MM:SSZ` (trailing `Z`), and the schema defaults in `scripts/db/schema_sql.py` use the same format. `StateStore.find_stale_running_attempts()` in `scripts/agent/workflow/state_store.py` parses with `time.strptime(started_at, "%Y-%m-%dT%H:%M:%S")`. Reproduced: `time.strptime("2026-10-30T10:00:00Z", "%Y-%m-%dT%H:%M:%S")` raises `ValueError: unconverted data remains: Z`, which the method swallows with `continue`. So every attempt written by production code is skipped, not only malformed rows.
- Confirmed: the tests seed `started_at` as `"2026-01-01T00:00:00"` (no `Z`) in `tests/agent/workflow/test_workflow_state_store.py`, and `tests/agent/workflow/test_state_store.py` mocks `find_stale_running_attempts`, so no test uses the production format.
- Confirmed: the parsed value goes through `time.mktime`, which interprets it as local time, while the stored value is UTC; on a non-UTC host the elapsed time is offset by the zone difference.
- Confirmed: `_STALE_GRACE_SEC = 30`, while `config/workflows/default.json` sets the `execute` stage `timeout_sec` to 120.
- Confirmed: recovery runs once, in `Orchestrator.__init__` (`scripts/agent/orchestrator.py`), and marks every `running` attempt older than the grace period as `failed`. `attempts` has no worker identity, lease, or heartbeat column (`scripts/db/schema_sql.py`).
- Related closed work: `issues/done/20261021-093421_turn001_task-idempotency-key-collides-across-restarts.md` is why a retained `workflow.sqlite` can hold `running` rows from earlier runs.

- Adversarial verification (issue-to-plan Step 2, 2026-10-30): `_STALE_GRACE_SEC` is referenced by no test (0 references), while `recover_stale_attempts` has 18 references in 2 test files. `scripts/shared/` has no ISO-8601 parser; the only other `Z` handling is a local `fromisoformat(created_at.replace("Z", "+00:00"))` in `scripts/agent/memory/scoring.py:25`, which is out of scope for this issue. The lease needs a heartbeat that runs while `asyncio.wait_for(fn(), timeout)` is awaiting in `WorkflowEngine._run_stage`; the engine runs on one event loop, so a periodic asyncio task is feasible there, but a blocking call inside the stage would starve it (not examined).
- Adversarial verification, design (Step 2, second finding): `WorkflowEngine._run_stage` enforces the stage deadline with `asyncio.wait_for(fn(), timeout=timeout_sec)`, so a stage that is running normally cannot outlive `timeout_sec`. A lease written at attempt start as `now + timeout_sec + margin` therefore needs no heartbeat in the normal path: by that time the attempt has finished, failed, or its owner is dead or stuck. A stuck owner is fenced by the conditional finish (a later `finish_attempt` finds the attempt no longer `running` and raises). The open question about a periodic renewal task is thereby narrowed to whether that stronger guarantee is wanted.
- Adversarial verification, scope: no worker or process identity exists in `scripts/` (the only `worker_id` is the session ID in `scripts/agent/audit_event_emitter.py:84`, unrelated), so an owner ID must be introduced; `attempts.started_at` is read only inside the workflow package; `scripts/agent/orchestrator.py:92` calls `recover_stale_attempts(get_connection())` and needs no change if the signature is kept, so it is a reference, not a target; `tests/shared/test_json_utils.py` already tests `now_iso` (`:383`) and is where parser tests belong; no test in `tests/` changes the process timezone yet (`tzset` finds none), so the timezone test is new technique.

## Problem
- With the current parser, an attempt left `running` by a crashed process is never recovered.
- If only the parser is fixed, a second agent process starting while another process is inside a legitimate execute stage longer than 30 seconds marks the first process's live attempt `failed`.
- A malformed `started_at` is silently ignored and the attempt stays `running` forever, with no log or diagnostic.

## Reason for Change
Parsing and liveness are one decision: fixing either alone leaves a wrong outcome (stuck rows, or stolen work). The first defect is in effect today and makes the existing recovery code and its warning logs dead in production. Medium because recovery output is currently not consumed by a production resume path (see `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`), so the visible impact is stale `running` rows, not wrong task results.

## Implementation Intent
- Use one timezone-aware UTC ISO-8601 parser for reads of what `now_iso()` writes; no `mktime`, no local time.
- Treat unparseable persisted timestamps as an observable condition (log and a distinct recovery outcome), not as "not stale".
- Record which worker owns a running attempt and until when (a lease, renewed while the stage runs). Staleness means the lease expired, not that N seconds elapsed. The stage timeout informs the lease duration.
- Take over an expired attempt with a conditional update on the expected owner and lease value so two recoverers cannot both win.
- Define the manual-recovery path for historic rows that cannot be parsed or have no lease.

## Target Files or Areas
- `scripts/agent/workflow/state_store.py` (`find_stale_running_attempts`, `recover_stale_attempts`, `_STALE_GRACE_SEC`)
- `scripts/shared/json_utils.py` (timestamp helpers; add a matching parser next to `now_iso`)
- `scripts/db/schema_sql.py` (`attempts` columns, `WORKFLOW_SCHEMA_VERSION`)
- `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py` (where the attempt row is created), `scripts/agent/workflow/workflow_engine.py` (lease renewal during a stage)
- `scripts/agent/orchestrator.py` (startup recovery call; reference only, no change expected)
- `config/workflows/default.json` and `scripts/agent/workflow/workflow_loader.py` (only if lease duration becomes configuration; not expected under the deadline-lease design)
- `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/shared/test_json_utils.py`, `tests/db/test_create_schema.py`
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` ("Startup Recovery")
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` (INV-07, if "interrupted Attempts" changes meaning)

## Required Changes
- Add one UTC ISO-8601 parser matching `now_iso()` (with `Z`) in `scripts/shared/json_utils.py`, reusing the approach of the existing local parse in `scripts/agent/memory/scoring.py` rather than adding a third variant, and use it for `started_at`; cover `Z`, explicit offset, fractional seconds, and malformed input.
- Report malformed `started_at` values instead of skipping them, and define their handling.
- Add worker identity and lease expiry (or heartbeat) to running attempts, set at attempt start and renewed during the stage.
- Replace the fixed 30-second rule with lease-expiry-based detection; keep the lease at least as long as the stage's `timeout_sec` plus a renewal margin.
- Make takeover a conditional update on the expected owner and lease value, requiring exactly one updated row.
- Change tests to seed production-format timestamps.
- Update the "Startup Recovery" section and, if the meaning of an interrupted attempt changes, ADR-001 INV-07 (ADR change protocol, `docs/00_governance/governance_01_documentation-policy.md`).
- Document manual recovery for rows without a lease.

## Constraints
- The schema change (new `attempts` columns) must use the forward-only migration mechanism, not recreation (see Dependencies).
- Persisted timestamps stay in the existing `YYYY-MM-DDTHH:MM:SSZ` text format; no mixed formats in `workflow.sqlite`.
- Fail-closed and audit behavior must not weaken; recovery must not mark a live attempt failed.
- Lease renewal must not make the engine depend on a new thread or process model without an owner decision (see Unresolved Questions).

## Acceptance Criteria
- Every `started_at` produced by `now_iso()` or the schema default is parsed by recovery without error; a test uses the literal production format.
- A malformed `started_at` produces a log record and an explicit recovery outcome, and does not remain silently `running`.
- An execute attempt that runs longer than 30 seconds and holds a valid lease is not recovered by a second process.
- An attempt whose owner stopped renewing becomes recoverable after the lease expires.
- Two recoverers racing on the same expired attempt produce exactly one takeover.
- Recovery results do not depend on the host's local timezone (tested with a non-UTC `TZ`).

## Testing Expectations
- Unit tests for the parser (the four timestamp cases above).
- Recovery tests with production-format timestamps; remove the mock-only coverage that hides the parser path.
- A multi-connection test: process A holds a lease on a long stage while process B runs startup recovery.
- A crash simulation: owner stops renewing, lease expires, recovery succeeds once, repeated recovery changes nothing further.
- Migration test for the new columns on a database with existing `running` rows.
- Run the sequence in `rules/toolchain.md` and `uv run python tools/check_db_separation.py`.
- Docs checkers per `routing.md` Tools: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, and `check_docs_japanese.py`; `check_needs_confirmation_inventory.py` if a Needs Confirmation marker is added.
- `uv run python tools/check_adr_preservation.py` if INV-07 is edited; each reported change must be intended and explained.

## Documentation Impact
Yes (intent, ownership semantics, and failure behavior only; no DDL or code restatement per `skills/DESIGN.md`):

- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` "Startup Recovery": currently says startup recovery marks active attempts `failed` and never changes task status; describe lease-based detection, the timestamp format contract, and manual recovery of unparseable rows.
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` INV-07 ("interrupted Attempts are recovered as `failed` at startup"): amend only if lease semantics change what counts as interrupted.
- Checked, not affected: `docs/41_db/db_02_architecture_and_schema-schema-reference.md` section 7 names tables only and must not gain a column list.
- Record the deployment-model assumption (single vs multiple agent processes) as a Needs Confirmation item if it stays unresolved.

## Out of Scope
- Attempt-number allocation, `processed_events` semantics, and task transition validation (`issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`).
- Retry policy and failure propagation (`issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md`).
- Changing `now_iso()`'s output format for other modules.

## Dependencies
- Depends on `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` for the `attempts` schema change.
- Should be ordered with `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`: both change the attempt row and stale recovery (`recover_stale_attempts`); land the state-machine contract first, then add the lease fields to it. Re-verify this issue against current source after that issue lands.

## Unresolved Questions
- 不明: whether running more than one agent process against one `workflow.sqlite` is a supported operating mode. Verified fact: no process lock or single-instance guard exists (`rg` for flock, pidfile, lockfile, fcntl under `scripts/agent` and `deploy/start_agent.sh` finds none), so nothing prevents it. This issue's multi-process criteria apply to that unprevented case.
- 不明: whether a periodic renewal is wanted at all. Verified: the deadline-lease design needs none because the engine enforces `timeout_sec`; a heartbeat would only shorten the takeover delay for a stuck stage at the cost of event-loop DB writes (`BEGIN IMMEDIATE` waits up to the 30000 ms busy timeout under contention).
- 不明: whether the lease duration should be derived from `timeout_sec` or configured separately.
- Assumption: historic `running` rows in retained databases are acceptable to mark failed once at migration time, after the manual-recovery rule is defined.

## AI Implementation Instruction
- Reproduce the `ValueError` with a production-format timestamp in a failing test before changing the parser.
- Do not choose the lease-renewal mechanism or the deployment assumption yourself; report them as open if unresolved.
- Keep changes limited to stale detection, timestamp parsing, and the attempt ownership fields; do not alter retry or status-transition logic.
- Report changed files, migration effects, commands run, and test results.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-105723
- **Related target files**: `scripts/agent/workflow/state_store.py`, `scripts/shared/json_utils.py`, `scripts/db/schema_sql.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/orchestrator.py`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`
