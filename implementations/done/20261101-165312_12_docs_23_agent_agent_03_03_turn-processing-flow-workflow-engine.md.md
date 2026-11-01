## Goal

Update `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`: Task Status Transitions table, Retry Mechanism, and Operational Notes to describe the configured retry kinds, the timeout classification, the typed failure contract, and the side-effect rule (REQ-010 / AC-10).

## Scope

- Task Status Transitions table (`:74-94` region, re-verified 2026-11-01): the `halted` rows stay, with the halt now described as 'kind not in `retry_on`, budget exhausted, or side-effect-flagged failure'; add the turn-level `error_kind` values `workflow_halted` / `workflow_timeout` to the turn-outcome description.
- Retry Mechanism section (`:119-129` region): state that retry eligibility is `retry_policy.retry_on` (`exception` / `timeout` / `llm_failure`, shipped default `["exception"]`), every failed attempt consumes one `max_attempts` unit, and deadline expiry is distinguished from a callback-raised `TimeoutError`.
- Operational Notes (`:149-150` region): keep the `halted` terminal-state bullets; add the side-effect rule sentence (a retry never follows an attempted non-READ tool call) and the LLM-failure status path (`failed` written once).
- Intent and failure behavior only; no code restatement (Plan Documentation Impact). UNK-01/UNK-02 are settled owner decisions, so no Needs-Confirmation marker is required; the conservative side-effect rule is described as current behavior, with relaxation deferred to a future owner decision (UNK-06).

## Assumptions

- Plan `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.
- Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `["exception"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).
- Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).
- Landing order (Plan Assumptions 'Re-verification record'; updated by the 2026-11-02 execution verification): wftaskapi001 `20261101-140834` and wflease001 `20261101-163219` have landed on `master` (wflease001 registered migration code 4 / "1.4.0"); the wfrecovery001 `20261101-145309` procedures remain Pending and this batch lands ahead of them by owner decision, so those Pending procedure docs must be re-verified against the landed source before their own execution. Shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.
- Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.
- This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, landed HEAD code 4 / "1.4.0") is not a target row and needs no change here.
- The table is shared with wfrecovery001 (`20261101-145309_24`) and wflease001 (`20261101-163219_15`) procedures that land earlier; Plan Assumptions: different sections, and the later change reconciles the transitions rows — this document reconciles last.

## Design decisions

- Docs describe the configuration-driven policy (readable from `config/workflows/default.json`) instead of restating code.

## Alternatives considered

- A new docs page — rejected: REQ-010 names the three passages of this file.

## Implementation
### Target file
`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure
1. Edit the three passages listed in Scope.
2. Run the docs checkers (Plan Validation plan).

### Method
Markdown section edits.

### Details
- Docs language policy: English file content (repo convention), verified by `check_docs_japanese`.
- `docs/10_adr/adr_02_02_001...md` decision 6 stays true under the shipped configuration and is not a target (Plan Documentation Impact).

## Compatibility considerations

- `docs/00_index.md` task-scope mapping applies (file is located through 'Document References by Task', Plan Documentation Impact).

## Security considerations

- No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.

## Rollback considerations

- Revert the document edits; code and docs land as one chain but each doc edit is independently revertable.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py` (Plan Validation plan).

## Completion criteria

- AC-10: the passages describe the implemented policy and contract and pass the docs checkers.

## Out of Scope

- ADR amendment (Plan Documentation Impact; only if the owner changes the outcome).
- Startup Recovery section (`:143+`, owned by wfrecovery001/wflease001 rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Edited the three in-scope passages plus two direct consequences: Task Status Transitions (typed turn-result intro, halted-row reword to kind-not-in-retry_on/deadline/budget/side-effect, llm_failure single-write failed row, removed the superseded adapter soft-error row and the adapter best-effort-log bullet, cancellation-is-the-only-adapter-write and propagating-status-fault bullets); Retry Mechanism (retry_on kinds list with shipped default, per-failed-attempt budget consumption, deadline-vs-inner-TimeoutError classification, attempt-kinds-vs-outward-kinds); Workflow Loader Validation Rules (retry_on validation rule); Operational Notes (halted reword, side-effect rule sentence with UNK-06 relaxation deferred, LLM-failure failed-written-once path); Turn State Mutation Reference (ctx.turn.attempt_side_effect row). Intent/failure behavior only, no code restatement. |
| 2 | Add or update tests per Validation plan | Completed | — | — | Test-only change not applicable; behavior is pinned by procedures 08-11. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_consistency --domain agent, check_docs_japanese all clean. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | This procedure IS the documentation update; no other docs in scope (ADR amendment out of scope, Startup Recovery owned by wfrecovery001/wflease001 rows). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 5 (Documentation)
- **Requirement ID**: `REQ-010`
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-165312
- **Related target files**: `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `config/workflows/default.json`