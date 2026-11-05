## Goal
- Make `Orchestrator._execute_turn` pass the chat session id to the workflow adapter instead of an empty string, so `tasks.session_id` matches what session diagnostics query (`REQ-001`: wire the real session id).

## Scope
**Release unit**: wfreview001-session-wiring
- One call site in `scripts/agent/orchestrator.py` and one import. `WorkflowEngineAdapter.execute_turn` keeps its signature.
- Member of unit `wfreview001-session-wiring` with procedure `_01_tests_agent_workflow_test_session_diagnostics_wiring.py.md`; the end-of-unit full-suite run happens after this member (corrected in Step 3b of `code-implementation`).

## Assumptions
- `ctx.session.session_id` is an `int | None` set by `ctx.session.start()` before the first turn on the only entry path; `format_session_id(int | None) -> str` returns `""` for `None`.
- Procedure `_01_tests_agent_workflow_test_session_diagnostics_wiring.py.md` has added the failing regression test before this change is made.

## Design decisions
- Reuse the existing `format_session_id` helper of `agent.audit_event_emitter` (the orchestrator already imports `AuditEventEmitter` from that module) instead of a new `str()` expression, so audit events and the `tasks` row use one format.
- Leave the read side (`SessionPersister`, `StateStore` getters) unchanged; `tasks.session_id` holds the chat session id.

## Alternatives considered
- Aggregating by task ids returned from the turn result: rejected because it changes the public return of `execute_turn` and leaves the column meaningless.
- Making the persister query `session_id=''`: rejected because it would cement the broken wiring.

## Implementation
### Target file
`scripts/agent/orchestrator.py`

### Procedure
1. Extend the existing import `from agent.audit_event_emitter import AuditEventEmitter` to also import `format_session_id`.
2. In `Orchestrator._execute_turn`, replace the third argument `""` of `self._workflow_adapter.execute_turn(...)` with `format_session_id(self._ctx.session.session_id)`.

### Method
- Keep the argument order `(line, turn_started_at, session_id)`.
- Run `uv run ruff format scripts/agent/orchestrator.py`; the call may stay on one line or wrap as the formatter decides.

### Details
- The adapter forwards the value to `create_task(..., session_id=...)` and to `audit_workflow_start` / `audit_stage_completed`; after this change those audit events carry the real id instead of `""`.
- Do not change `ctx.session` or the adapter.

## Compatibility considerations
- `execute_turn` signature and return are unchanged. Tests that call the adapter directly with `""` or `"sess-1"` bypass the orchestrator and stay valid.
- New `tasks` rows carry the session id as text; existing rows keep `''` and are never matched by a session filter, which is the status quo.
- Audit events for workflow start and stage completion now carry a non-empty `session_id`; the consumer scan found only tests that supply their own value.

## Security considerations
- The value is an integer row id, not a secret; it is already written to audit events by `AuditEventEmitter`.

## Rollback considerations
- Revert the commit. Rows written with the real id stay in `workflow.sqlite` and are harmless.

## Validation plan
- `uv run pytest tests/agent/workflow/test_session_diagnostics_wiring.py` passes.
- `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_session_persister.py tests/agent/workflow`.
- `uv run ruff check scripts/agent/orchestrator.py`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`.

## Completion criteria
- `rg 'execute_turn' -A2 scripts/agent/orchestrator.py` shows no `""` argument, and the regression test from procedure `_01` passes.

## Out of Scope
- The schema reference update (procedure `_03`), `SessionPersister`, `StateStore`, and the adapter.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import `format_session_id` and pass it to `execute_turn` | Completed | 20261105-094817 | 20261105-094911 | Changed: scripts/agent/orchestrator.py (import format_session_id; execute_turn gets format_session_id(ctx.session.session_id)). |
| 2 | Run the regression test and the existing orchestrator tests | Completed | 20261105-094911 | 20261105-094911 | Regression tests of _01 pass (3); targeted 278 passed (test_orchestrator, test_session_persister, tests/agent/workflow). |
| 3 | Run the validation sequence (`rules/toolchain.md`); deploy only as the user's decision per `skills/deploy/SKILL.md` | Completed | 20261105-094911 | 20261105-095915 | mypy, lint-imports, bandit -ll, module size, suppression check, gates pass; full suite and diff-cover at end of unit. End of unit: full suite 11512 passed, 7 skipped (-m 'not integration and not production_paths_allowed'); diff-cover 100% (orchestrator.py). Step 5/6: N/A, no docs/00_index.md task-scope mapping for the changed files. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (pass the chat session id to `execute_turn`)
- **Source issue**: issues/20261103-134147_wfreview001_workflow-diagnostics-empty-session-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-085618_wfreview001_workflow-diagnostics-empty-session-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092237
- **Related target files**: `scripts/agent/orchestrator.py`