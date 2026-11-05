## Goal
- Make `tasks.session_id` carry the chat session id so that `SessionPersister.persist_session_diagnostics()` reports real workflow counts and artifact URIs, proven by a real-DB regression test covering the orchestrator write path and the persister read path together.

## Priority
High

## Scope
- **In-Scope**: pass the chat session id from `Orchestrator._execute_turn` into `WorkflowEngineAdapter.execute_turn`; add a real-DB regression test (write path + read path); restate the meaning of `tasks.session_id` in the schema reference.
- **Out-of-Scope**: `processed_events`, attempt recovery, and task-status semantics; renaming or removing `tasks.session_id`; chat-log and history session handling; the `SessionPersister` `StateStore()` connection lifecycle (wfreview002).
- **Dependencies**: both dependencies named by the Issue are already closed (`issues/done/20261030-105723_wftaskapi001_consolidate-task-persistence.md`, `plans/done/20261030-113553_wftaskapi001_consolidate-task-persistence.md`), so no open dependency. Sequencing note: wfreview002 edits the same read path in `scripts/agent/session_persister.py`; this Plan does not touch that file, so the two are independent.

## Background
Adversarial review of `scripts/agent/workflow/` (2026-11-03) found that `Orchestrator._execute_turn` hardcodes an empty `session_id` when calling the workflow adapter. The adapter writes it unchanged into `tasks.session_id`, while the diagnostics read side filters `tasks` by the real chat session id.

## Problem
Verified in Step 2: `scripts/agent/orchestrator.py` passes `""` as the third argument of `execute_turn(...)`; `scripts/agent/workflow_engine_adapter.py` `_init_workflow_task` calls `create_task(..., session_id=session_id, ...)`; `scripts/agent/session_persister.py` `persist_session_diagnostics` calls `get_task_count`, `get_workflow_count`, `get_execute_attempt_count`, `get_artifact_uris` with `str(ctx.session.session_id)`; all four filter `WHERE session_id=?` on `tasks`. Every `tasks` row written in production has `session_id=''`, so every count is 0 and the artifact list is empty. The same empty value also flows into the `session_id` field of `audit_workflow_start` and `audit_stage_completed`.

## Reason for Change
Zero counters are indistinguishable from "no workflow work happened". `tasks.session_id` is a real column used by four queries, so any future per-session workflow query inherits the same broken wiring.

## Implementation Intent
Decision (Issue's open question): `tasks.session_id` holds the chat session id (`ctx.session.session_id`, formatted as text). Rejected alternative: aggregating by task ids returned from the turn result, which would add a return value to `execute_turn` (a public signature change) and leave the column meaningless. The orchestrator is the only caller on the production path, so the fix is one call-site change using the existing `format_session_id` helper in `scripts/agent/audit_event_emitter.py`. The read side is unchanged. The regression test drives `Orchestrator._execute_turn` against a real `workflow.sqlite` fixture and then calls `SessionPersister.persist_session_diagnostics()`.

## Requirements
- `REQ-001`: `Orchestrator._execute_turn` passes the chat session id (text form of `ctx.session.session_id`) to `execute_turn()` instead of `""`.
- `REQ-002`: A regression test runs a turn through `Orchestrator._execute_turn` against a real workflow database, then runs the persister aggregation and asserts non-zero `task_count` and `workflow_count`; it fails against the pre-fix code.
- `REQ-003`: The schema reference states that `tasks.session_id` holds the chat session id and that session diagnostics aggregate workflow activity by it.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/agent/workflow/test_session_diagnostics_wiring.py` | Regression test | New file: real-DB test of orchestrator write path + persister read path | REQ-002 / AC-2 | New file; `tests/agent/workflow/` exists; existing getter tests hand-seed ids in `tests/agent/workflow/test_workflow_state_store.py` (checked in Step 2) | itself | Verified |
| `scripts/agent/orchestrator.py` | Turn entry point | Replace the hardcoded `""` argument of `execute_turn(...)` with the formatted chat session id | REQ-001 / AC-1 | `Orchestrator._execute_turn` passes `""` as third argument (checked in Step 2) | `tests/agent/workflow/test_session_diagnostics_wiring.py` | Verified |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Schema reference | Section 7 says `session_id` is "recorded metadata only"; state its value and its use by diagnostics | REQ-003 / AC-3 | Section 7 paragraph on `task_nonce` (checked in Step 2) | `tools/check_docs_consistency.py --domain db` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/audit_event_emitter.py` | Provides `format_session_id(int \| None) -> str` to reuse | `scripts/agent/orchestrator.py` / REQ-001 |
| `scripts/agent/workflow_engine_adapter.py` | `execute_turn` and `_init_workflow_task` write `session_id` into `tasks` and audit events; unchanged | REQ-001 |
| `scripts/agent/session_persister.py` | Read side; unchanged | REQ-002 |
| `scripts/agent/workflow/state_store.py` | Diagnostic getters; unchanged | REQ-002 |
| `scripts/agent/workflow/task_ops.py` | `create_task`, `get_task_count`, `get_workflow_count`; unchanged | REQ-002 |
| `scripts/agent/session.py` | `session_id: int \| None`, set by `start()` | REQ-001 |
| `tests/agent/test_orchestrator.py` | Fixtures for building an `Orchestrator` with a real adapter; existing tests pass `""` directly to the adapter and stay valid | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): a turn executed through `Orchestrator._execute_turn` creates a `tasks` row whose `session_id` equals `str(ctx.session.session_id)`.
- AC-2 (REQ-002): the regression test asserts `task_count >= 1` and `workflow_count >= 1` from the persister aggregation, fails on the pre-fix code, and passes after the fix.
- AC-3 (REQ-003): the schema reference no longer describes `session_id` as unused metadata and states the diagnostics use.
- AC-4 (all): `uv run pytest tests/agent/workflow tests/agent/test_session_persister.py tests/agent/test_orchestrator.py`, ruff, mypy, and the import-contract checks pass.

## Tests
- `REQ-001`, `REQ-002`: `tests/agent/workflow/test_session_diagnostics_wiring.py` — real workflow DB, orchestrator turn, then persister aggregation; plus a case where `ctx.session.session_id` is `None` and the stored value is `''` (documented, not asserted as desired behavior).
- `REQ-003`: docs checkers listed under Validation plan.

## Documentation Impact
Update the workflow database section of the schema reference (see `docs/00_index.md` "Document References by Task", DB tasks); drives REQ-003. The agent persistence doc named by the Issue (`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`) has no `tasks.session_id` statement (checked in Step 2), so it needs no change.

## Assumptions
- `ctx.session.start()` runs before the first turn on the REPL path (`scripts/agent/repl_input_loop.py`); `Orchestrator` is built only by `startup_component_init.py` (checked in Step 3), so no batch entry point exists.
- Chat session ids are SQLite autoincrement integers; a retained `workflow.sqlite` paired with a recreated `session.sqlite` could reuse an id and merge counts across runs. This is accepted as out of scope here.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Behavior when `ctx.session.session_id` is `None` at turn time | Not reachable on the REPL path per Step 3, but no guard test exists | Test records the `''` fallback via `format_session_id`; revisit if a second entry point appears | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/orchestrator.py` | Modify | Low | N/A | N/A | Runtime code under `scripts/`; copied by deploy, no schema or config change |
| `tests/agent/workflow/test_session_diagnostics_wiring.py` | Create | Low | N/A | N/A | None (tests are not deployed) |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Modify | Low | N/A | N/A | None (docs are not deployed) |

## Design
Path A (3 target files, no interface or schema change). Direction chosen: wire the real id (see Implementation Intent). `execute_turn` keeps its signature. Audit events (`audit_workflow_start`, `audit_stage_completed`) now carry the real session id instead of `""`, which is the intended value of their `session_id` field. Consumer scan (`tools/scan_change_consumers.py --seed session_id --seed execute_turn`): the candidates are tests that call `execute_turn` directly with `""` or `"sess-1"` (`tests/agent/test_orchestrator.py`, `tests/integration/test_orchestrator_integration.py`); they bypass the orchestrator and stay valid — not affected: they pass their own value.

## Implementation steps
1. **Phase 1: Regression test first**
   - [ ] Add `tests/agent/workflow/test_session_diagnostics_wiring.py` and confirm it fails on current code (REQ-002; `tests/agent/workflow/test_session_diagnostics_wiring.py`)
2. **Phase 2: Wiring fix**
   - [ ] Pass `format_session_id(self._ctx.session.session_id)` to `execute_turn` (REQ-001; `scripts/agent/orchestrator.py`)
3. **Phase 3: Documentation**
   - [ ] Update section 7 of the schema reference (REQ-003; `docs/41_db/db_02_architecture_and_schema-schema-reference.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] Hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first; deploying is the user's decision (approval gate). Run the checkers under Validation plan (REQ-001; `scripts/agent/orchestrator.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/workflow/test_session_diagnostics_wiring.py` | Integration, real workflow DB | `uv run pytest tests/agent/workflow/test_session_diagnostics_wiring.py` | Fails before Phase 2, passes after |
| `scripts/agent/orchestrator.py` | Regression of existing orchestrator tests | `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_session_persister.py tests/agent/workflow` | Pass |
| `scripts/agent/orchestrator.py` | Lint, type, security, size | `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run python tools/check_module_size.py` | No new findings (baseline: radon and vulture not installed — Not available; bandit baseline High 42 pre-existing) |
| `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Docs checkers | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain db` | Pass |

## Risks
- **Risk**: Audit log consumers that matched on `session_id == ""` for workflow events → **Mitigation**: the consumer scan found only tests that pass their own value; Step 3 found no production matcher.
- **Risk**: Session id reuse against a retained `workflow.sqlite` merges counts across runs → **Mitigation**: recorded in Assumptions; out of scope, and `tasks.created_at` remains available for a later time-bounded filter.
- **Risk**: The new test depends on heavy orchestrator fixtures and becomes brittle → **Mitigation**: reuse the fixtures of `tests/agent/test_orchestrator.py`; keep one end-to-end case.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add failing real-DB regression test | Completed | — | 20261105-095922 |  |
| 2 | Wire the session id in the orchestrator | Completed | — | 20261105-095922 |  |
| 3 | Update the schema reference | Completed | — | 20261105-102405 |  |
| 4 | Deploy hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-092237_01_tests_agent_workflow_test_session_diagnostics_wiring.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261105-092237_02_scripts_agent_orchestrator.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261105-092237_03_docs_41_db_db_02_architecture_and_schema-schema-reference.md.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261103-134147_wfreview001_workflow-diagnostics-empty-session-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-085618
- **Related target files**: `scripts/agent/orchestrator.py`, `tests/agent/workflow/test_session_diagnostics_wiring.py`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 2; `orchestrator.py` call site | `scripts/agent/orchestrator.py` | Phase 2 | AC-1 | `test_session_diagnostics_wiring.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes 3, Testing Expectations | `tests/agent/workflow/test_session_diagnostics_wiring.py` | Phase 1 | AC-2 | pytest command in Validation plan | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes 4, Documentation Impact | `docs/41_db/db_02_architecture_and_schema-schema-reference.md` | Phase 3 | AC-3 | docs checkers | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-092237 -->
