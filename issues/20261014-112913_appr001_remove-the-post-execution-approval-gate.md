# Remove the post-execution approval gate

## Priority
High

## Summary
Remove the workflow's post-execution approval stage (`plan -> execute -> approval -> verify -> complete/failed` becomes `plan -> execute -> verify -> complete/failed`): `/approve`, `/reject`, the `approvals` table, the `pending_approval` task status, startup approval recovery, and the `require_approval` workflow key. Human approval stays tool-level, decided before a Tool executes; its decisions are traced through the existing `tool_approval` audit event. The Workflow Engine stays mandatory. Source: `memo2.md`, corrected by adversarial verification against current source, ADRs, docs, and checkers.

## Background
ADR-001 and ADR-008 define a mandatory approval stage after `execute` and persist pending approvals in `workflow.sqlite`. `memo2.md` proposes removing it. It was written without source access, so its names, line numbers, and claims were verified in this issue.

Verified facts (current source):
- Flow: stages run plan, execute, then `_gate_approval` when `require_approval`, then verify (`scripts/agent/workflow/workflow_engine.py`). Tools run inside `execute`, before the gate. The `verify` stage only emits the `turn_end` audit event and clears `ctx.turn.current_turn_id` (`workflow_engine_adapter.py`, `_handle_turn_end`). Nothing runs only after approval.
- `/reject` only resolves the approval record, sets the task to `halted`, and writes a `workflow_approval` audit event. `/approve` resolves the record, writes the same event, and sets `pending_approval_task_id`; nothing reads that field to resume, so an approved task stays `pending_approval` and the next turn creates a new task.
- While an approval is pending, `repository_gateway.py` (`_gate_write`, lines 98-111) denies every write operation, and the orchestrator blocks the next turn (`orchestrator.py:160-161`).
- `ApprovalDecisionType` is the tool-level enum in `scripts/agent/tool_enums.py:30` (AUTO, APPROVED, DENIED, DRY_RUN, PLAN_BLOCKED) used by `tool_approval.py`, `tool_audit.py`, `tool_models.py`, and `shared/enums.py`. It is not part of the gate.
- `WorkflowHaltError` and the `halted` status are also produced by retry exhaustion (`workflow_engine.py`) and by `WorkflowTimeoutError`; rejection is not the only source, and no other path (stop, cancel, plan mode) sets `halted`.
- The loader currently requires the opposite of the target: `workflow_loader.py:93-94` raises when `require_approval` is not true, and the repository `config/workflows/default.json` has `true`.
- Production runs an older revision: `/opt/llm/scripts/agent/workflow/workflow_loader.py` has no must-be-true check (`require_approval=bool(data.get("require_approval", False))`) and `/opt/llm/config/workflows/default.json` has `"require_approval": false`. The approval gate is therefore disabled in production today, and deploying the current repository state without this change would enable it. `deploy/deploy.sh` copies `config/workflows/` to `/opt/llm/config/workflows/` (line 157) after validating the repository file, so the next deploy replaces the production definition.
- Production `workflow.sqlite` (read-only check, schema version 1.0.0): tasks are 1 `completed` and 1 `running`, `approvals` holds 1 `approved` row, and no task is `pending_approval`. The UPDATE migration would change 0 rows and the DROP would delete that one historical approval record.
- `/audit turn <task_id>` (`scripts/agent/commands/cmd_audit.py:86`) filters events by `task_id == turn ID`, and `turn_start`, `tool_approval`, `tool_exec`, and `turn_end` all use the turn ID as `task_id`; only workflow stage events use `tasks.task_id`.
- `turn_end` is emitted twice per turn: by `verify_fn` (`workflow_engine_adapter._handle_turn_end`, which then clears `current_turn_id`) and by `AuditEventEmitter.emit_turn_end` (`orchestrator._execute_turn`), so the second event carries an empty `task_id` and an `elapsed_ms` computed from 0.0. This is confirmed by reading the code, is unrelated to the gate, and is unchanged by this issue.
- ADR-014 INV-01 says components other than the Workflow Engine, including `ToolExecutor`, do not decide "whether to approve"; after this change tool-level approval is decided by `tool_policy`/`tool_approval` on the tool path, so that clause no longer holds. ADR-014 line 56 lists the stage order and approvals, and its Out of Scope line says "Redesign of the approval policy".
- Past ADR `Decision Change` lines (ADR-001, -002, -004, -007, -008, -009) all use the form "Task-level approval decision (repository owner instruction) covering ...; individual reviewer names are not recorded." `governance_01` requires the record to name roles, not people, and forbids `pending`.
- `approvals` is a required table in `scripts/agent/services/workflow_schema.py:51` (`REQUIRED_WORKFLOW_TABLES`), `deploy/init_db.sh:43`, and `deploy/setup_services.sh:43`; the deploy scripts run `python -m agent.workflow.validate` on the workflow JSON and treat a missing table or a schema-version mismatch as fatal.
- Migrations are `_WORKFLOW_MIGRATIONS` entries of one SQL statement each (`scripts/db/schema_sql.py`), run on every `create_workflow_schema()` call; two statements in one entry raise `sqlite3.ProgrammingError`, which aborts startup. `WORKFLOW_SCHEMA_VERSION` is `"1.0.0"` and must be bumped with a new entry. Nothing references `approvals`, and there are no views or triggers on `workflow.sqlite`.
- `tool_approval` events (`tool_audit.audit_approval`) already carry `workflow_id`, are written only inside a workflow context (assertion), and cover auto, approved, denied, and dry-run decisions. Their `task_id` field is `ctx.turn.current_turn_id` (the turn ID), not the workflow `tasks.task_id`.
- The `/mdq` and `/skill` removals are complete; the `/mdq` guard used `COMPAT_PATTERNS`.

## Problem
- The gate cannot stop an operation: every Tool of the turn has already run, and rejection only marks the task `halted`.
- Nothing runs only after approval, and `/approve` does not actually resume anything (dead resume path).
- A per-turn approval trains operators to approve without reading, weakening tool-level approval.
- A pending approval blocks all writes and the next turn, and needs persistent state, startup recovery, and expiry handling.
- The audit log already records tool-level approval decisions and tool results with workflow context.

## Reason for Change
Align human approval with the one place it can prevent an operation (before a Tool runs), remove persistent pending-approval state and its recovery, and reduce operator burden. The change alters decisions in ADR-001 and ADR-008, so it needs the maintainer's recorded decision.

## Implementation Intent
Record the owner's decision, then land the ADR changes, code removal, migration, deployment scripts, tests, and docs together; the ADR Change Protocol (`governance_01`) forbids leaving the ADR text half-updated. Keep the Workflow Engine, tool-level approval, tool-level `ApprovalDecisionType`, `audit_approval`, and the audit log. Add no new table. Guard reintroduction with unregistered-command tests, a loader-rejection test, and `COMPAT_PATTERNS` entries for code identifiers only.

## Target Files or Areas
ADRs and index (`docs/10_adr/`): `adr_02_001_workflow-engine-mandatory.md`, `adr_02_008_sqlite-4db-separation.md`, `adr_02_014_agent-control-plane-responsibility-boundaries.md`, `adr_01_index.md`.

Code:
- `scripts/agent/commands/cmd_workflow.py` (delete), `command_defs_list.py`, `registry.py` (`_WorkflowMixin` import, base class, docstring)
- `scripts/agent/workflow/approval_ops.py` (delete), `workflow_engine.py`, `state_store.py` (`get_approval_count`), `models.py`, `workflow_loader.py`, `__init__.py`
- `scripts/agent/orchestrator.py`, `workflow_engine_adapter.py`, `repository_gateway.py`, `context.py`, `startup.py`, `startup_approval_recovery.py` (delete), `tool_output.py`, `output_tags.py`, `tool_audit.py` (`audit_approval_requested`), `session_persister.py` (`approval_events`)
- `scripts/agent/commands/cmd_context.py`, `cmd_config_stats.py`, `models.py`; `scripts/agent/services/context_view.py`, `models.py`, `workflow_schema.py`
- `scripts/db/schema_sql.py`, `scripts/db/create_schema.py` (docstring), `config/workflows/default.json`
- `deploy/init_db.sh`, `deploy/setup_services.sh`; production `/opt/llm/config/workflows/default.json` (operational step)

Tests: delete `test_startup_approval_recovery.py`, `test_approval_ops.py`, `test_cmd_workflow.py`, `test_cmd_workflow_approval.py`, `test_approval_race_condition.py` (5 files, 77 tests); edit `test_workflow_engine.py`, `test_workflow_state_store.py`, `test_workflow_loader.py`, `test_orchestrator.py`, `test_orchestrator_integration.py`, `test_orchestrator_bg_failure_threshold.py`, `test_repository_gateway.py`, `test_startup_rollback.py`, `test_agent_cmd_context.py`, `test_repl.py`, `test_tool_output.py`, `test_tool_runner.py`, `test_repl_health.py`, `tests/db/test_create_schema.py`, `test_command_registry_consistency.py`, `test_removed_commands.py`, `tests/tools/test_check_compat_shims.py`; add migration, INV-10, INV-11, and no-approval-stage tests.

Docs: `overview_01_02`, `agent_01`, `agent_02` (call-site row, lines about `handle_turn` rejection and approval recovery), `agent_03_01`, `agent_03_03` (including `ctx.turn.pending_approval_*` rows), `agent_04_03`, `agent_06_02`, `agent_06_03`, `agent_06_04` (rewrite), `agent_07_01`, `agent_07_03`, `agent_07_08`, `agent_07_09`, `agent_09_01`, `agent_09_03`, `agent_10_01` to `agent_10_05`, `agent_13` (regenerate), `db_01`, `db_02`, `db_03`, `db_07`, `db_08`, `deployment_01`, and the Known Issues ledger (`governance_03`, remove AGENT-010).

Tools: `tools/check_compat_shims.py` (`COMPAT_PATTERNS`), `tools/check_docs_structure.py` (`SIZE_EXCEPTIONS`, only if the ADR-008 text cannot be kept within its ceiling).

Checked and needing no change: `agent_04_01` (no approval content; the `pending_approval_*` rows are in `agent_03_03`), `rules/`, `skills/`, `prompts/`, `routing.md` (their "approval gate" mentions are unrelated), ADR-003 and ADR-004 (tool-level).

## Required Changes
1. Sign-off first: record the repository owner's decision for ADR-001, ADR-008, and ADR-014 INV-01 (a task-level approval decision per `governance_01` ADR Acceptance Evidence Standard; the channel per `rules/coding.md` Explicit sign-off gates is a maintainer statement on the plan entry; roles, not names; the real change date). Each of the three ADRs gets its own `Decision Change` line.
2. ADR-001: apply the Summary, Constraints, Decision Details 6, 9, and new 10, Scope, Rationale 1 and new 4, Consequences, Verification, Implementation Notes, and invariant changes (delete INV-04 and INV-09, add INV-10 and INV-11, leave gaps); rewrite Alternative D (its title, advantages, and disadvantages assume approval state persistence), fix the approval-state disadvantages in Alternatives A and B, and add Alternative E worded without the literal `/approve` and `/reject` forms; list `scripts/db/schema_sql.py` and `scripts/agent/tool_audit.py` in Implementation References. ADR-008: Decision 3, INV-03, Domain table, Recovery Policy Matrix, Implementation References, and a `Decision Change` line of 141 bytes or less (a 132-byte form such as "- **Decision Change (2026-10-14)**: Task-level approval decision (repository owner); approvals removed from Decision #3 and INV-03." fits; the memo's 276-byte form exceeds the ceiling by 135 bytes), so `SIZE_EXCEPTIONS` stays unchanged. ADR-014: Workflow Engine responsibility text (stage order and approvals), the Out of Scope line (make it "tool-level approval policy"), and remove "or whether to approve" from INV-01; mirror the INV-01 change in the `adr_01_index` row (remove "or approval"). `adr_01_index`: delete the ADR-001 INV-09 row, add INV-10 and INV-11 rows, change the Pipeline Mapping text "ADR-001 INV-01 and INV-08" to include INV-10 and INV-11; cite only tests in index rows.
3. Remove the gate code: `/approve` and `/reject` with `cmd_workflow.py` and the `_WorkflowMixin`, `approval_ops.py`, `_gate_approval`, the workflow-level approval statuses and expiry (`approved`, `rejected`, `pending`, `expired`, TTL), `WorkflowPendingApprovalError`, `ApprovalRecord`, `WorkflowDef.require_approval`, `get_approval_count` and the `approval_events` diagnostics key, `approval_pending` and `pending_approval_id` and `pending_approval_task_id` in all contexts and views, the write gate in `repository_gateway.py`, the orchestrator and adapter handling, `ApprovalRecovery` and `_recover_pending_approvals`, the `workflow_approval` and `approval_requested` audit events and the `workflow.approval` span and attributes, `OutputTag.APPROVAL_PENDING`, pending-approval notices and banners, and `pending_approval` from the task-status list.
4. Keep list (do not delete): `ApprovalDecisionType`, `ApprovalDecisionEvent`, `audit_approval`, `log_approval_decision`, `OutputTag.APPROVAL`, tool-level `require_approval_for`, `WorkflowHaltError`, `WorkflowTimeoutError`, and the `halted` status (retry exhaustion and timeout still use them).
5. Loader: replace the "require_approval must be true" check with a rejection of any definition that contains the key (any value), remove the `require_approval` field and the value copy, and remove the key from `config/workflows/default.json`; the deploy scripts that run `agent.workflow.validate` must pass.
6. Database: remove `approvals` from the base DDL; add two migration entries in this order (UPDATE `pending_approval` tasks to `failed`, then `DROP TABLE IF EXISTS approvals`); bump `WORKFLOW_SCHEMA_VERSION` (for example to 1.1.0); remove `approvals` from `REQUIRED_WORKFLOW_TABLES` in `workflow_schema.py`, `init_db.sh`, and `setup_services.sh`.
7. INV-11 wording: keep the current behavior (decided; see Unresolved Questions). The `tool_approval` event carries `workflow_id` and a `task_id` field holding the turn ID, for auto, approved, denied, and dry-run decisions, and `/audit turn` depends on that. Add a regression test; do not change the field.
8. Docs: update the documents above; fix `agent_03_03` where it says `halted` is reachable by an explicit stop operation (no such path exists); repair the two anchors that will break (`#approval-gates` from `overview_01_02` and `deployment_01`, `#restoration-of-pending-post-execution-approvals` from `agent_10_04`); regenerate `agent_13` (drops `audit_approval_requested`, `emit_approval_pending_notice`, `ApprovalRecovery`; keeps `ApprovalDecisionType`); remove AGENT-010 from the ledger; drop the unverified "H-2" task-list item.
9. Guard: add `\b`-bounded `COMPAT_PATTERNS` entries for `approval_ops`, `request_approval`, `_gate_approval`, `find_latest_pending_approval`, `find_all_pending_approvals`, `_recover_pending_approvals`, `WorkflowPendingApprovalError`, `ApprovalRecord`, `pending_approval_id`, `pending_approval_task_id`, `audit_approval_requested`, `emit_approval_pending_notice`, `handle_workflow_approval_pending`, `ApprovalRecovery`, `startup_approval_recovery`, `approval_requested`, `approval_pending` (non-`\b` form so it does not clash with `emit_approval_pending_notice`), and the command forms `/approve` and `/reject` with a lookbehind like the `/mdq` entry; add tests, and `/approve` and `/reject` unregistered-command tests. Do not register `require_approval` (guard it with the INV-10 test), `approvals`, `pending_approval`, `ApprovalDecisionType`, or the phrase "approval gate".
10. Operations: back up `/opt/llm/db/workflow.sqlite` before the first start after the upgrade (the DROP deletes 1 historical approval row; no `pending_approval` task exists today); `deploy.sh` replaces `/opt/llm/config/workflows/default.json` from the repository, so the production `require_approval` key disappears with the deploy, and `init_db.sh` (migration) must run before `setup_services.sh`; verify the table list and the schema version afterward; announce that `/approve` and `/reject` become unknown commands and that no per-turn approval remains.
11. Tests: delete and edit as listed; fix the inline workflow definitions in `test_repl_health.py` and the approvals DDL and assertions in `test_create_schema.py`; update the mixin-count test to 11 total and 9 direct; retarget `test_startup_rollback.py` away from `_recover_pending_approvals`.

## Constraints
- ADR-001 and ADR-008 decisions change: the recorded owner decision must exist before implementation, and the real change date must be used.
- The Workflow Engine stays mandatory; no workflow-disable mode and no direct execution path.
- Do not renumber ADR invariants; INV-04 and INV-09 stay as gaps.
- The migration must be idempotent and use one SQL statement per entry.
- ADR-008 is 33636 bytes against a 33647-byte ceiling in `SIZE_EXCEPTIONS`; the five text removals save 130 bytes, which leaves room for a `Decision Change` line of at most 141 bytes (measured by applying the edits to a copy). ADR-014 is 15665 bytes against the 24576-byte limit and needs no exception.
- `ApprovalDecisionType` and the tool-level approval modules are out of the deletion list.
- Production must drop `require_approval` before or with the deploy, or startup fails by design.
- `COMPAT_PATTERNS` scans code and docs; every retained mention of a registered name needs a file allowlist, so register only names that will not remain.

## Acceptance Criteria
- A turn that runs a write Tool completes without `/approve`; pending state never blocks writes or the next turn.
- `/approve` and `/reject` are unknown commands (unregistered-command tests).
- A definition containing `require_approval` (any value) is rejected at load time; the repository and production definitions no longer contain it.
- Tool-level approval decisions appear in the audit log as `tool_approval` events with `workflow_id` and the turn-ID `task_id` (regression test).
- A new `workflow.sqlite` has no `approvals` table; migration marks `pending_approval` tasks `failed`, drops the table, and can run twice; the schema-version check and deploy table checks pass.
- `WorkflowHaltError` handling for retry exhaustion and timeout still passes its tests.
- No registered removed name remains in code or docs except allowlisted files; `check_compat_shims.py` (default) is clean; `--check-removed-names` shows no new finding versus its baseline of 2.
- The ADR, index, and docs checkers pass, including the ADR-008 size check and the invariant-matrix and reference checks.
- ADR-014 INV-01 and its `adr_01_index` row no longer assign approval decisions away from the tool path, and each changed ADR has a `Decision Change` line with role-based wording and the real date.
- A production-like upgrade check passes: starting from a copy of the production `workflow.sqlite` (schema 1.0.0, 1 approved `approvals` row), the migration leaves no `approvals` table, version 1.1.0 (or the chosen bump), and unchanged `tasks` rows.
- All tests, mypy, import-linter, and the docs checkers pass; the only failures allowed are the pre-existing ones recorded in the plan baseline.

## Testing Expectations
- `uv run pytest` (full), `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run ruff check`.
- `check_compat_shims.py` (default) and `--check-removed-names`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_structure.py`, `check_known_deviation_sync.py`, `check_docs_structure.py`, `check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_consistency.py` for each domain.
- New tests: INV-10 loader rejection, a write-tool turn completing without approval, the `tool_approval` audit record (existing `tests/agent/test_tool_audit.py` may host it; the memo's `tests/agent/test_tool_approval_audit.py` does not exist), migration (old DB with `pending_approval` rows, second run, new DB), and unregistered commands.
- Measure the impact first: `rg -l "approval_pending|pending_approval|approval_ops|ApprovalRecord" tests | wc -l` before editing.

## Documentation Impact
Yes: three ADRs and the index, the Agent, DB, and deployment documents listed above, the generated reference, the Known Issues ledger, and upgrade notes. ADR text must follow the ADR Change Protocol (same-change updates, approval record with roles and a real date). Docs stay in English; current specs must not keep the removed stage's syntax or history notes beyond the ADR's rationale and alternative.

## Out of Scope
- Redesign of the tool-level approval policy (risk rules and safety tiers in `agent/tool_policy.py`).
- Removing the Workflow Engine, `WorkflowHaltError`, or the `halted` status.
- Correlating the audit `task_id` with `tasks.task_id` (needs a maintainer decision).
- The duplicate `turn_end` emission (confirmed by reading the code; file a separate issue).
- `rules/`, `skills/`, and `prompts/` "approval gate" wording (unrelated).

## Dependencies
- The repository owner's recorded decision on ADR-001 and ADR-008 gates all implementation (sign-off channel: a maintainer statement recorded on the plan entry, per `rules/coding.md`).
- The `/skill` and `/mdq` removals are merged; the registry mixin-count test starts from 12 total and 10 direct.
- Open issues under `issues/` that touch these files: none known (checked 20261014).
- Deploy order: `init_db.sh` (migration) before `setup_services.sh`.

## Unresolved Questions
Resolved by investigation:
- `task_id` of `tool_approval`: keep the turn ID. `/audit turn <task_id>` and the other turn events (`turn_start`, `tool_exec`, `turn_end`) use the turn ID, so switching only this event would drop it from that view. Correlating with `tasks.task_id` stays out of scope (the maintainer may override at sign-off).
- ADR-008 size: keep the `Decision Change` line within 141 bytes; no checker change is needed. Re-recording the ceiling (as done for ADR-003, -004, and -006) is only the fallback if a fuller line is wanted.
- Production start: production runs an older loader (no must-be-true check) with `require_approval: false`, so it starts today with the gate off; the repository's mandatory-true loader and `true` config were never deployed. This change makes the production behavior official, and the next deploy replaces the production definition.
- "H-2": no slash-command task list exists in the repository (the `H-2` matches are unrelated plans and issues). Drop that memo item; it belongs to a document outside the repository.
- ADR-014 INV-01 and the index wording: reword (see Required Changes 2), because tool-level approval is now decided on the tool path; treat it as part of the same owner decision.
- `turn_end` duplication: confirmed by code reading, outside this issue (see Out of Scope).

Still open:
- The repository owner's decision on ADR-001, ADR-008, and ADR-014 INV-01 (a precondition, not something investigation can supply).
- Whether to keep the 1 historical `approved` approval row outside the database (for example in an exported backup) before the DROP; this issue assumes a database backup is enough.

## AI Implementation Instruction
Do not start implementation until the recorded owner decision exists. Keep changes to the listed targets and the keep list; if another file needs changes, report it as an additional target before editing. Do not delete anything on the keep list. Do not renumber ADR invariants or touch the tool-level approval policy. Edit mixed test files by test name and compare collected counts before and after. Do not commit unless asked.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261014-112913
- **Related target files**: see Target Files or Areas
