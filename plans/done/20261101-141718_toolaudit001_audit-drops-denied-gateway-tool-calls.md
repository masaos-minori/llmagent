## Goal
- Make `audit_tool_exec()` write a structured `tool_exec` event (with `error_type="denied"`) for every tool call that `RepositoryGateway` denies through its policy preflight, while a result that carries no request id, no source and no denial keeps producing no event.

## Priority
Medium

## Scope
- **In-Scope**:
  - Narrow the early-return guard in `audit_tool_exec()` (`scripts/agent/tool_audit.py`) so a result whose `error_type` is `"denied"` passes it even when `mcp_request_id` and `source` are both empty.
  - Unit tests for the narrowed guard in `tests/agent/test_tool_audit.py` (denial recorded, genuine no-op still skipped, event fields).
  - A regression test in `tests/agent/test_repository_gateway.py` that drives a write call denied by `check_preflight()` through a real `RepositoryGateway` and `execute_one_tool_call()` and asserts the audit sink receives the `tool_exec` record.
- **Out-of-Scope**:
  - `tool_approval.check_approval()`'s own gate and how workflow approval state is set or cleared (Issue Out of Scope).
  - Any change to the audit event schema or fields beyond ensuring a denial is recorded (Issue Constraint).
  - Removing or changing the free-text `gateway.policy_denied` log line, and any change to `_denied_result()` or `_gate_write()` (the Issue lists them as target areas, but the required change is the guard only; see Design).
  - The `gateway is None` branch of `tool_runner._execute_prepared_call`, which re-raises `PolicyViolationError` and never reaches `audit_tool_exec` (UNK-02).
  - Replacing the `assert ctx.workflow.workflow_id` precondition (assertaudit001) and the idempotency key (idemaudit001).
- **Dependencies**:
  - `plans/20261101-141314_assertaudit001_audit-assert-risks-post-execution-crash.md` (Frozen, `Pending`; source Issue archived at `issues/done/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md`): fix order, this Plan lands after it. That Plan replaces the `assert ctx.workflow.workflow_id` in `audit_tool_exec` with warn-and-skip placed after the existing early returns; this Plan only changes the early-return condition above it, so the two edits touch different statements. Landing this Plan first would let a denial with no `workflow_id` reach the `assert`, raise `AssertionError`, and `_recorded_call` would replace the denial text with a generic execution-failure row. The denial tests here use a non-empty `workflow_id`; one test with an empty `workflow_id` (REQ-004) is valid only once assertaudit001 has landed.
  - `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md` (open, not planned): also edits `audit_tool_exec` (the `idempotency_key` it records); no ordering requirement, the later change rebases.
  - `plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md` (Frozen, `Pending`): adds tests to `tests/agent/test_tool_audit.py`, no `tool_audit.py` edit; additions are disjoint, the later one rebases.
  - `implementations/done/20261030-102825_05_scripts_agent_tool_audit.py.md` (archived, applied): added `dedup_state` and `execution_snapshot_json`; the guard is unchanged by it.

## Background
Found in an adversarial review of the tool-execution and audit subsystem. `RepositoryGateway` is the write boundary: for a non-READ tool it runs `check_preflight()` and returns `_denied_result()` on `PolicyViolationError`. `execute_one_tool_call()` then calls `audit_tool_exec()` with the result's `request_id`, `error_type` and `source`.

## Problem
`audit_tool_exec()` begins with `if not mcp_request_id and not source: return` (after the audit-logger check). `_denied_result()` builds a `ToolCallResult` with `request_id=""`, `server_key=""`, `error_type="denied"` and the default `source=""`, so both values are falsy and no structured `tool_exec` event is written for a gateway preflight denial. The only trace is the ordinary-log line `gateway.policy_denied`. Corrections to the Issue (Step 2): (1) the `ctx.turn.pending_approval_id` denial path no longer exists; only the preflight denial remains. (2) In the production path the same `check_preflight()` already runs first in `check_approval()`, which writes a `tool_approval` event whose decision is the preflight code (for example `denied_root_jail`) and drops the call before it reaches the gateway, so the claim "no entry in the structured audit log" holds for the gateway path only (defense in depth, reached when the upstream gate is bypassed); see UNK-01. (3) Other empty-`request_id` error results are not dropped: `ToolExecutor` routing errors and transport/tool errors from `ToolTransportInvoker._error_result` carry `source="mcp"`, so denial is the only error class lost by the guard.

## Reason for Change
A write or delete that the gateway policy refuses (blocked path, repository or tool allowlist) is a security-relevant event, and the `tool_exec` stream is where later analysis expects every executed-or-refused tool call. Today the gateway refusal leaves no record in the `audit_logger` pipeline.

## Implementation Intent
Keep the guard, but let a denial through it: the early return remains for a result that has neither a request id nor a source and is not a denial. The event written for a denial is the ordinary `tool_exec` event (same fields), with `is_error` true, `error_type` `"denied"`, empty `mcp_request_id`, and `source` defaulted to `"agent"` by the existing fallback. No gateway change is needed because `_denied_result()` already sets `error_type="denied"`.

## Requirements
- `REQ-001`: `audit_tool_exec()` writes a `tool_exec` event when `error_type` is `"denied"`, even if `mcp_request_id` and `source` are both empty; the event carries the existing fields only (no schema change), with `error_type="denied"` and `is_error` as passed.
- `REQ-002`: The early return is preserved for a call with empty `mcp_request_id`, empty `source` and any `error_type` other than `"denied"` (the existing no-op case).
- `REQ-003`: A write call denied by `check_preflight()` inside a real `RepositoryGateway`, executed through `execute_one_tool_call()`, produces exactly one structured `tool_exec` audit record with `error_type="denied"`, and the `gateway.policy_denied` log line is still emitted and `_denied_result()` is unchanged.
- `REQ-004`: With assertaudit001 landed, a denial whose context has no `workflow_id` writes no event and does not raise (the warn-and-skip path); the test is added only after that Plan is implemented.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/tool_audit.py | Narrow the early-return condition in `audit_tool_exec` so `error_type == "denied"` passes it; name the denial value once (a module constant) and keep every other statement, the signature and the event schema unchanged | The guard `if not mcp_request_id and not source: return` drops a result built by `_denied_result` (empty `request_id`, default `source=""`) | REQ-001, REQ-002 / AC-1, AC-2 | `audit_tool_exec` holds the guard before the `assert ctx.workflow.workflow_id`; `radon cc` grades `audit_tool_exec` B (9) (checked in Step 3) | tests/agent/test_tool_audit.py, tests/agent/test_repository_gateway.py | Verified |
| tests/agent/test_tool_audit.py | Add unit tests: denied result with empty id and source is recorded with the expected fields; the same call with a non-denied `error_type` is still skipped; `source` becomes `"agent"` | `TestAuditToolExec` covers only the empty-id/empty-source skip (`test_skips_event_when_mcp_request_id_is_empty_and_source_is_empty`) and the `source="cache"` emit; no denial case | REQ-001, REQ-002 / AC-1, AC-2 | `TestAuditToolExec` and its `_make_ctx` helper (non-empty `workflow_id`) exist; the existing skip test passes `error_type` unset, so it stays valid (checked in Step 2) | tests/agent/test_tool_audit.py itself | Verified |
| tests/agent/test_repository_gateway.py | Add a regression test that runs a write call denied by a patched `check_preflight` through a real `RepositoryGateway` and `execute_one_tool_call`, asserting one `tool_exec` record with `error_type="denied"`; keep the existing `test_write_tool_blocked_by_policy` unchanged | `TestWritePolicy.test_write_tool_blocked_by_policy` asserts the denied result only, never the audit sink; its `_make_ctx` has `workflow_id=None`, so the new test needs its own context with a non-empty id | REQ-003, REQ-004 / AC-3, AC-4 | `TestWritePolicy` patches `agent.repository_gateway.check_preflight` with `PolicyViolationError("deny", "blocked")` and `classify_operation_type`; `_make_gateway` builds the gateway (checked in Step 2) | tests/agent/test_repository_gateway.py itself | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file.
- `Validation Status` is `Verified` or `Needs confirmation` per row.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/repository_gateway.py | `_denied_result()` (`error_type="denied"`, empty `request_id`, default `source`) and `_gate_write()` (the `gateway.policy_denied` warning); read-only, no change needed | REQ-001, REQ-003 |
| scripts/agent/tool_runner.py | `execute_one_tool_call()` calls `audit_tool_exec` with `result.request_id`, `result.error_type`, `source=result.source`; `_recorded_call` converts a raised exception into a failure row | REQ-003, REQ-004 |
| scripts/agent/tool_approval.py | `check_approval()` runs `check_preflight()` first and writes a `tool_approval` denial event upstream | REQ-001 (UNK-01) |
| scripts/shared/transport_dto.py | `ToolCallResult` fields and the `source=""` default | REQ-001 |
| scripts/shared/tool_executor.py | Routing-error results carry `source="mcp"` via `_error_result`, so they pass the guard | REQ-002 |
| scripts/agent/shared/models.py | `ToolExecEvent` schema that must stay unchanged | REQ-001 |
| tests/agent/test_tool_approval_preflight.py | `TestAuditToolExec.test_skips_when_mcp_request_id_is_empty` (non-denied, `error_type` unset) must still pass; shows how `execute_one_tool_call` tests build `PreparedToolCall` and context | REQ-002, REQ-003 |
| plans/20261101-141314_assertaudit001_audit-assert-risks-post-execution-crash.md | Sibling Plan replacing the `assert` below the guard | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): `audit_tool_exec(ctx, tool, args, True, "", "denied", source="")` writes one `tool_exec` record whose `error_type` is `"denied"`, `is_error` is true, `mcp_request_id` is empty, `source` is `"agent"`, and whose field set equals that of any other `tool_exec` record.
- AC-2 (REQ-002): The same call with `error_type` empty (or `"tool"`) and empty `mcp_request_id`/`source` writes nothing; all pre-existing tests in `tests/agent/test_tool_audit.py` and `tests/agent/test_tool_approval_preflight.py` pass unchanged.
- AC-3 (REQ-003): The gateway-driven test sees exactly one `tool_exec` audit record with `error_type` `"denied"` for a preflight-denied write, `executor.execute` is not awaited, and the `gateway.policy_denied` warning is captured.
- AC-4 (REQ-004): After assertaudit001, a denial with `workflow_id` `None` writes no event and does not raise.

## Tests
- Unit (REQ-001, REQ-002): new cases in `TestAuditToolExec` in `tests/agent/test_tool_audit.py`: denial with empty id/source recorded; non-denied empty-id/source skipped; `source` defaults to `"agent"` for a denial.
- Regression (REQ-003): in `tests/agent/test_repository_gateway.py`, a real `RepositoryGateway` with a patched `check_preflight` raising `PolicyViolationError`, run through `execute_one_tool_call`, with a `MagicMock` audit sink and a non-empty `workflow_id`; assert the one record and the unchanged log line (`caplog`).
- Conditional (REQ-004): denial with `workflow_id` `None` writes nothing and does not raise; added only after assertaudit001 is implemented.
- Run `tests/agent/test_tool_audit.py`, `tests/agent/test_repository_gateway.py`, `tests/agent/test_tool_approval_preflight.py`, `tests/agent/test_tool_runner.py`.

## Documentation Impact
N/A: the Issue states no operator-facing document describes this gap, and Step 2 confirmed it. `rg` over `docs/` found no statement about which results become `tool_exec` rows or about `gateway.policy_denied`; `agent_10_02` and `agent_10_03` describe only `args_preview` bounding and the workflow-context constraint (the latter edited by assertaudit001).

## Assumptions
- Only `error_type == "denied"` is added to the pass condition: the Issue asks that a denial always be recorded and that no other behavior change. Falsifiable by AC-2.
- No gateway change: `_denied_result()` already sets `error_type="denied"`, so guarding on `error_type` alone meets the Issue without a result-contract change (setting `source="agent"` in `_denied_result` would also pass the guard but would change a result field and would not cover a future denial that omits it). Falsifiable by AC-1/AC-3.
- The denial event's `source` is `"agent"` through the existing `source if source else "agent"` fallback; no new source value is introduced.
- Step 8b: `tools/check_plan_target_overlaps.py` names this Plan for `scripts/agent/tool_audit.py` (with assertaudit001 and `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`) and `tests/agent/test_tool_audit.py` (with those two and maskargs001). Judgements: assertaudit001 is a sequencing dependency (this Plan after it, see Scope Dependencies); wfrecovery001 is compatible (it changes `audit_stage_completed` to add `attempt_number` and adds a `stage_completed` test; this Plan changes only the `audit_tool_exec` guard); maskargs001 is compatible (append-only `args_preview` tests, no `tool_audit.py` edit). No finding names `tests/agent/test_repository_gateway.py`.
- Path A: three target files, no signature, schema or public-interface change (the event schema and `audit_tool_exec` signature are unchanged; only a result that was dropped is now written).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the owner still wants a `tool_exec` row for gateway denials now that `check_approval()` already writes a `tool_approval` denial event for the same preflight failure on the normal path (Needs confirmation) | No owner statement; the Issue asks for the row and treats the gap as absolute, but the upstream gate already records the decision | Default: proceed as the Issue requests (the gateway path is reached only when the upstream gate is bypassed, and the row is cheap); the owner may drop the Plan before implementation | False |
| UNK-02 | Whether the `gateway is None` branch of `_execute_prepared_call`, which re-raises `PolicyViolationError` and is converted into a failure row without any `tool_exec` event, should also be audited (Needs confirmation) | Issue names only the gateway path; the branch is documented as unreachable in production | Out of scope here; the owner may file a separate issue | False |
| UNK-03 | Landing order against assertaudit001, which is `Pending` (open dependency, `plans/20261101-141314_assertaudit001_audit-assert-risks-post-execution-crash.md`) | Plan not yet implemented | Implement assertaudit001 first (Scope Dependencies); this Plan is implementable without it, and only REQ-004's test and the production no-`workflow_id` behavior depend on it | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/tool_audit.py | Modify | Low: one caller (`tool_runner.execute_one_tool_call`); only the denial case changes, and it adds a row | N/A | N/A | None: `scripts/agent/` is deployed code with no new file, config key or service change; takes effect on the normal deploy |
| tests/agent/test_tool_audit.py | Modify | Low: shared test file, append-only | N/A | N/A | None: tests are not deployed |
| tests/agent/test_repository_gateway.py | Modify | Low: append-only | N/A | N/A | None: tests are not deployed |

## Design
Path A (Step 3): direct verification only. Imports of `agent.tool_audit` (rg): `tool_runner` and tests; the guard has one production caller, which passes `result.error_type`. Current behavior: with `mcp_request_id=""` and `source=""` the function returns before the `assert` and before any event is built. Decision: replace the condition with `if not mcp_request_id and not source and error_type != <denied value>: return`, keeping the position before the workflow check so assertaudit001's replacement of the `assert` applies unchanged to a denial. The denied value is named once as a module constant in `tool_audit.py` rather than a repeated literal; `ApprovalDecisionType.DENIED` is not reused because it names an approval decision, not a result `error_type`. The literal in `repository_gateway._denied_result` stays as is; the end-to-end test (REQ-003) pins the two values together. Alternatives rejected: removing the guard (the Issue forbids it; it also skips cache or empty results by design), and writing `source="agent"` in `_denied_result` (changes a result contract and leaves the audit function blind to a future denial without a source). Failure path: the added condition is a pure string comparison and cannot raise. Baseline (Step 5): `radon cc` grades `audit_tool_exec` B (9) and the gateway methods A; `vulture` shows nothing on the targets; `bandit` reports only the three pre-existing B101 `assert` findings in `tool_audit.py`, which assertaudit001 removes; the diff-cover baseline needs a full-suite run and is deferred to the implementation phase, which must reach the threshold in `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Add the unit tests for the denial and the preserved no-op, and confirm the denial test fails before Phase 2 (REQ-001, REQ-002; tests/agent/test_tool_audit.py)
   - [ ] Add the gateway-driven regression test with a non-empty `workflow_id` and confirm it fails before Phase 2 (REQ-003; tests/agent/test_repository_gateway.py)
   - [ ] Only if assertaudit001 has landed, add the denial-without-`workflow_id` test (REQ-004; tests/agent/test_repository_gateway.py)
2. **Phase 2: Core logic**
   - [ ] Add the denial constant and narrow the early-return condition in `audit_tool_exec`; touch nothing else (REQ-001, REQ-002; scripts/agent/tool_audit.py)
3. **Phase 3: Deployment & Verification**
   - [ ] Run the named test files, and the toolchain sequence in `rules/toolchain.md` (REQ-001..REQ-003; all three target files)
   - [ ] Deploy hand-off: after the change is committed and pushed, deploying is the user's decision under `skills/deploy/SKILL.md` (it has an approval gate); no `deploy.sh`, config or service change (REQ-001; scripts/agent/tool_audit.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/tool_audit.py | Unit: denial recorded, non-denied empty-id skipped, field set and `source` default | `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_approval_preflight.py` | New and existing tests pass |
| tests/agent/test_repository_gateway.py | Integration: preflight-denied write through a real gateway and `execute_one_tool_call` | `uv run pytest tests/agent/test_repository_gateway.py tests/agent/test_tool_runner.py` | One `tool_exec` denial record; gateway log line unchanged |
| scripts/agent/tool_audit.py | Format, lint, types, architecture, security | `uv run ruff format scripts/agent/tool_audit.py`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run bandit` per `rules/toolchain.md` | Clean (the B101 findings remain until assertaudit001) |
| Changed lines | Diff coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At or above the threshold |

## Risks
- **Risk**: Landing before assertaudit001 lets a denial without `workflow_id` hit the `assert`, and `_recorded_call` replaces the denial text with a generic failure row (likelihood Low in production, where `workflow_id` is set; Medium in tests whose context has `workflow_id=None`, such as the gateway test file's `_make_ctx`) → **Mitigation**: fix order in Scope Dependencies (assertaudit001 first); the new denial tests use a non-empty `workflow_id`.
- **Risk**: The denial now appears as both a `tool_approval` event (upstream) and a `tool_exec` event (gateway) only when the upstream gate is bypassed, so a consumer that counts denials by event type could see an uneven mix (likelihood Low) → **Mitigation**: the events have different `event` values and the Issue asks for exactly this record; no schema change; UNK-01 records the owner's option to drop it.
- **Risk**: The `"denied"` value is duplicated between `_denied_result` and the new constant, so a rename in one place silently drops denials again (likelihood Low) → **Mitigation**: the REQ-003 test drives the real gateway result into the audit function, so a mismatch fails.
- **Risk**: Sibling Plans edit `tests/agent/test_tool_audit.py` (maskargs001, assertaudit001, wfrecovery001) and `audit_tool_exec` (idemaudit001) (likelihood Medium) → **Mitigation**: append-only test additions; distinct statements in the function; the later change rebases.
- **Risk**: `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` also edits `tool_audit.py` (`audit_stage_completed`, adding `attempt_number`) and `tests/agent/test_tool_audit.py` (likelihood Low) → **Mitigation**: different function, no shared statement; compatible; the later change rebases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: denial and no-op unit tests, gateway-driven regression test (tests/agent/test_tool_audit.py, tests/agent/test_repository_gateway.py) | In Progress | — | — |  |
| 2 | Core logic: narrow the `audit_tool_exec` guard (scripts/agent/tool_audit.py) | In Progress | — | — |  |
| 3 | Deployment and verification: tests, toolchain, deploy hand-off (scripts/agent/tool_audit.py, tests/agent/test_tool_audit.py, tests/agent/test_repository_gateway.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-132702_02_tests_agent_test_tool_audit.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-132702_03_tests_agent_test_repository_gateway.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-132702_01_scripts_agent_tool_audit.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180330_toolaudit001_audit-drops-denied-gateway-tool-calls.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-141718
- **Related target files**: scripts/agent/tool_audit.py, tests/agent/test_tool_audit.py, tests/agent/test_repository_gateway.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 1; `audit_tool_exec` guard vs `_denied_result` | scripts/agent/tool_audit.py | 2 | AC-1 | Tests: unit denial | Confirmed by repository evidence |
| REQ-001 | Issue Acceptance Criteria 1 | tests/agent/test_tool_audit.py | 1 | AC-1 | Tests: unit denial | Confirmed by repository evidence |
| REQ-002 | Issue Acceptance Criteria 2; existing skip tests | scripts/agent/tool_audit.py | 2 | AC-2 | Tests: unit no-op preserved | Confirmed by repository evidence |
| REQ-002 | Issue Acceptance Criteria 2 | tests/agent/test_tool_audit.py | 1 | AC-2 | Tests: unit no-op preserved | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes 2; Testing Expectations; Constraints (keep log line) | tests/agent/test_repository_gateway.py | 1 | AC-3 | Tests: regression | Confirmed by repository evidence |
| REQ-004 | Issue Constraints (coordinate with assertaudit001); assertaudit001 Plan | tests/agent/test_repository_gateway.py | 1 | AC-4 | Tests: conditional | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-132702 -->