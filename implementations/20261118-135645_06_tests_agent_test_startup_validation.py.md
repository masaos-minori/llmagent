## Goal
Add the tests the Acceptance Criteria require (`REQ-001`, `REQ-002`, `REQ-004`): a real drifted tool, a safety-tier gap, and the RAG fallback entry.

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: new tests in `TestCheckConfigStage` and `TestRagConsistencyTimeout` of this file; no production code.
- This file is named by two code rows (`startup_validation.py`, `routing_drift.py`), so it keeps its own procedure instead of being a companion.

## Assumptions
- `_run_check_config(ctx, **overrides)` patches `agent.startup_validation` names, so passing the real `check_routing_drift` (imported from `agent.services.routing_drift`) as an override runs the real check (checked in Step 3a).
- `shared.tool_registry.get_registry()` knows the server keys; a config entry with a registered server key and an unregistered tool name is drift.

## Design decisions
- Use the real `check_routing_drift` and `check_routing_safety_tiers` with real config-shaped input, not mocks, so the acceptance cases exercise the shipped code.

## Alternatives considered
N/A: the helper already supports overrides.

## Implementation
### Target file
`tests/agent/test_startup_validation.py`

### Procedure
1. Add `test_unregistered_routed_tool_is_fatal` (new): `ctx.cfg.mcp.mcp_servers` holds one server (a key from `get_registry()`) whose `tool_names` is `["unregistered_tool_x"]`; run `_run_check_config` with `check_routing_drift` overridden by the real function; assert one FATAL `routing_drift` outcome and `result.has_fatal`.
2. Add `test_tool_missing_from_safety_tiers_is_fatal` (new): `ctx.cfg.approval.tool_safety_tiers` is a non-empty dict that lacks one registered tool name; override `check_routing_safety_tiers` with the real function (it resolves the default registry); assert a FATAL `routing_safety_tiers` outcome and no WARNING outcome for that source.
3. Add `test_inconsistent_rag_result_without_findings_is_fatal` (new): `rag_service.consistency.return_value = MagicMock(is_consistent=False, findings=())`; run `_run_check_services`; assert the `rag_consistency` outcomes are `[StartupCheckStatus.FATAL]`.
4. Add `test_unverified_probe_finding_is_a_warning` (new): `consistency.return_value` carries one DEGRADED `ConsistencyFinding` (message of an unverified-FK finding, `repair_action="rerun_check"`); assert `[StartupCheckStatus.WARNING]` and not `has_fatal`.

### Method
- Build `ConsistencyFinding` and `FindingSeverity` from `db.models` (both already imported in this file).
- Keep the assertions on `StartupCheckStatus` values as the neighbouring tests do.

### Details
- Do not change existing tests; the two pinned safety-tier tests live in the companion files of procedure 04.

## Compatibility considerations
N/A: tests only.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_validation.py`; ruff and mypy per `rules/toolchain.md`; diff-cover 100% for procedure 04's new lines.

## Completion criteria
- The four tests pass and fail against the pre-change code for cases 1-3 where applicable (case 2 and 3 fail before procedure 04; case 1 passes already and pins the behavior).

## Out of Scope
- Production code; the companion tests of procedures 02 and 04.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the four tests (Implementation > Procedure) | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20261117-123005_adrchk005_startup-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-134945_adrchk005_startup-fail-closed.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-135645
- **Related target files**: `tests/agent/test_startup_validation.py`
