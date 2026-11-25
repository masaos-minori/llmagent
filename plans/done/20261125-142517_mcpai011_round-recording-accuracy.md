## Goal
- Make the Agent round execution record (`round_exec` audit event) report the scheduling mode the plan actually ran with and whether the round contained a write call, instead of a constant `mode="parallel"` and a side-effect flag inferred from the presence of a serialization event. Verified by plan-shape tests that run the real scheduler and read the logged record.

## Priority
Medium

## Scope
- **In-Scope**:
  - Derive `mode` from the execution plan (`ExecutionPlan.batches`), and make `scheduling_mode` use the same derivation.
  - Derive `has_side_effect` from `PreparedToolCall.spec.is_write` of the approved calls.
  - Keep `trigger_tool` and `serial_reason` as serialization-event diagnostics.
  - Add plan-shape tests in a new test file.
- **Out-of-Scope**:
  - Scheduler behavior and resource scopes (`scripts/agent/tool_scheduler.py`; resource-scope refinement is the separate GitHub resource-scope issue, mcpai013).
  - The `_serialization_stats` counters and `get_serialization_stats()` read by `commands/cmd_mcp.py`; they keep their meaning.
  - The `ctx.stats.stat_serialization_events` entries and the `save_serialization_event` diagnostics rows.
  - The signature and payload keys of `write_round_exec` in `scripts/agent/tool_audit.py`.
  - The debug log line in `scripts/agent/tool_runner.py::_run_plan_batches` (see UNK-02).
- **Dependencies**: Independent. The logical idempotency key work (mcpai004) is closed; its pending implementation procedures change `PreparedToolCall` construction in `scripts/agent/tool_preparation.py`, so re-run the new tests after them (Risks). The archived round-completion cancellation-window issue (toolrun001) was re-verified: it concerns `finish()` in the cancellation handler of `execute_all_tool_calls`, not the recorded fields. This Plan is a recommended input for validating the mcpai013 resource-scope issue, not a prerequisite of it.

## Background
`scripts/agent/tool_run_recorder.py` records one `round_exec` audit event per execution round through `write_round_exec`. Current code (checked in Step 2): `_record_round_exec` passes `mode="parallel"` unconditionally and `has_side_effect=first_event is not None`, and `_scheduling_mode` labels a round `dag_concurrent` only when some batch holds more than one group.

## Problem
1. `mode` is always `parallel`, so a sequential round (for example two conflicting writes in one conflict group, or a forced-serial round) is recorded as parallel.
2. `has_side_effect` is true only when the scheduler emitted a serialization event. A single write with no conflict produces no event, so it is recorded as having no side effect.
3. `_scheduling_mode` misclassifies a round of several read-only calls: `_build_phase_batch` pools un-conflicted calls into one non-sequential group inside one batch, and `_run_group_calls` gathers that group concurrently, but `len(batch.groups) > 1` is false, so the round is recorded `dag_sequential` (Needs confirmation in the Issue; confirmed here by reading the scheduler and the runner, and by the plan-shape tests this Plan adds).

## Reason for Change
Operational telemetry and incident-review accuracy. Observability only; no data-integrity risk.

## Implementation Intent
Add one helper that answers "did any part of this plan run concurrently" from the plan's batches and groups, as the executor runs them (`_run_plan_batches` gathers the groups of a batch, and `_run_group_calls` gathers a non-sequential group). Use it for both `mode` and `scheduling_mode`. Compute `has_side_effect` from the approved calls' `spec.is_write`. Leave the serialization-event path untouched as diagnostics.

## Requirements
- `REQ-001`: The recorded `mode` MUST be `parallel` when the plan runs any calls concurrently (a batch with more than one group, or a non-sequential group with more than one call) and `serial` otherwise (including an empty plan and a single call).
- `REQ-002`: `scheduling_mode` MUST be derived from the same helper as `mode`: `dag_concurrent` exactly when `mode` is `parallel`, `dag_sequential` otherwise.
- `REQ-003`: `has_side_effect` MUST be true exactly when at least one approved call has `spec.is_write` true, independent of whether a serialization event occurred; a forced-serial read-only plan MUST NOT be marked as a write.
- `REQ-004`: `trigger_tool` and `serial_reason` MUST remain the first serialization event's values (or `None`), `affected_tools` MUST remain every approved call's name, and the `_serialization_stats` counters and `get_serialization_stats()` MUST keep their meaning.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_run_recorder.py` | Add the plan-concurrency helper, derive `mode`, `scheduling_mode`, and `has_side_effect` in `_record_round_exec` | `_record_round_exec` hard-codes `mode="parallel"` and sets `has_side_effect=first_event is not None`; `_scheduling_mode` tests `len(batch.groups) > 1` only | REQ-001, REQ-002, REQ-003, REQ-004; AC-1, AC-2, AC-3, AC-4, AC-5 | `tool_run_recorder.py:121-125` (`_scheduling_mode`), `:128-149` (`_record_round_exec`); `tool_scheduler.py:_build_phase_batch` puts un-conflicted calls in one `sequential=False` group; `tool_runner.py:_run_group_calls` gathers it (checked in Step 2) | `tests/agent/test_tool_run_recorder.py` | Verified |
| `tests/agent/test_tool_run_recorder.py` | Create: the plan-shape tests, consistency test, and counter-unchanged test | No test file covers `_record_round_exec` or `_scheduling_mode`; `tests/agent/test_tool_runner.py:3141` only patches `_record_round_exec` | REQ-001, REQ-002, REQ-003, REQ-004; AC-1, AC-2, AC-3, AC-4, AC-5 | New file; `tests/agent/` exists; `rg -n "_scheduling_mode\|_record_round_exec" tests` finds only the patch in `test_tool_runner.py` (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/tool_scheduler.py` | Defines `ExecutionPlan`, `ScheduledBatch`, `ScheduledGroup`, `build_execution_groups`, and the forced-serial plan | REQ-001, REQ-002 |
| `scripts/agent/tool_runner.py` | Calls `_record_round_exec` and defines how groups execute (`_run_plan_batches`, `_run_group_calls`) | REQ-001, REQ-004 |
| `scripts/agent/tool_audit.py` | `write_round_exec` builds the `round_exec` payload; its signature stays | REQ-004 |
| `scripts/shared/tool_spec.py` | `ToolSpec.is_write` is the side-effect metadata | REQ-003 |
| `scripts/agent/tool_preparation.py` | `PreparedToolCall.spec` is the recorder input | REQ-003 |
| `scripts/agent/commands/cmd_mcp.py` | Reads `get_serialization_stats()` and `ctx.stats.stat_serialization_events` | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): A concurrent read-only plan (several reads) is recorded `mode="parallel"`, `scheduling_mode="dag_concurrent"`.
- AC-2 (REQ-001, REQ-002): A sequential write plan (conflicting writes in one sequential group) is recorded `mode="serial"`, `scheduling_mode="dag_sequential"`, not parallel.
- AC-3 (REQ-003): A single write with no conflict is recorded `has_side_effect=true` although no serialization event occurred.
- AC-4 (REQ-001, REQ-003): A forced-serial read-only plan is recorded `mode="serial"` and `has_side_effect=false`.
- AC-5 (REQ-002, REQ-004): The recorded `mode` matches the scheduler's plan (`parallel` if and only if `scheduling_mode` is `dag_concurrent`), and `get_serialization_stats()` and the serialization-event entries are unchanged.

## Tests
- Write the four plan-shape tests first, before the change, using `build_execution_groups` for real plans and reading the JSON that `_record_round_exec` logs through a mocked audit logger (REQ-001, REQ-002, REQ-003): concurrent read-only plan, sequential write plan, single write without conflicts, forced-serial read-only plan.
- Add a mixed case (one write plus reads without a scope conflict: `parallel`, `has_side_effect` true) and an empty plan (`serial`, `has_side_effect` false) (REQ-001, REQ-003).
- Add a consistency test over all shapes (`mode == "parallel"` if and only if `scheduling_mode == "dag_concurrent"`) (REQ-002).
- Add a counter test: `_record_serialization_stats` and `get_serialization_stats()` behave as before (REQ-004).
- Run `ruff`, `mypy`, and the full test suite.

## Documentation Impact
N/A: no `docs/*.md` page describes the `round_exec` fields (`rg -n "round_exec|has_side_effect|dag_sequential" docs` outside the generated reference finds nothing), and the generated reference lists `write_round_exec`, whose signature is unchanged, and only the public `get_serialization_stats` from the recorder (`docs/23_agent/agent_13_reference-api-generated.md`). If the helper is added as a public function, regenerate with `uv run python tools/generate_reference_table.py --check`; a private helper needs no regeneration.

## Assumptions
- Mode vocabulary: `parallel` and `serial` are reused, because `write_round_exec` callers and tests already use them and the per-event diagnostics use `serial`. `scheduling_mode` keeps `dag_concurrent` and `dag_sequential`. This is a judgment call (UNK-01).
- No repository consumer reads the `round_exec` `mode` or `has_side_effect` values (`rg` over `scripts/`, `tools/`, `docs/`, `tests/` finds only the writer and its tests); consumers outside the repository are unknown (UNK-01).
- The scheduler's plan is the authority for "actual" execution because the runner executes exactly that plan's batches and groups (`_run_plan_batches`); this Plan does not change either.
- The Issue's `PreparedToolCall.spec.is_write` is the "approved tool metadata": `approved_calls` holds `PreparedToolCall` objects after approval.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Consumers of the `round_exec` `mode` and `has_side_effect` values outside this repository (dashboards, log queries), and whether the existing value vocabulary `parallel`/`serial` is the one they expect. | Not enumerable from the repository. | Owner confirms; the keys and the value vocabulary are unchanged, only the values become accurate. | False |
| UNK-02 | `scripts/agent/tool_runner.py::_run_plan_batches` logs `concurrently`/`sequentially` with the same `len(batch.groups) > 1` inference, so its debug line misreports a pure concurrent group. | Whether the owner wants the debug label aligned; the Issue limits the change to the recorder and its tests. | Out of scope here; file a follow-up Issue after this Plan lands if the label matters. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_run_recorder.py` | Modify | Low (the one private recorder function has one caller, `tool_runner.py`; the counters read by `cmd_mcp.py` are untouched) | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_run_recorder.py` | Create | Low | N/A | N/A | not applicable (rsynced) |

## Design
**Classification**: Path A (2 target files; no public code interface change; no database schema change). The audit payload keys and the value vocabulary are unchanged, and no consumer of the values was found in the repository.

**Corrected understanding of the Issue** (Step 2 adversarial verification):
- Confirmed: `mode="parallel"` is a constant and `has_side_effect=first_event is not None` is inferred from serialization events (`tool_run_recorder.py:142-143`).
- Not in the Issue, found here: `_scheduling_mode` also misreports a round of several un-conflicted calls as `dag_sequential`, because that round is one batch with one non-sequential group. The Issue's "keep scheduling and display modes consistent" requires fixing it together with `mode`.
- Confirmed: a forced-serial read-only plan emits no serialization event today (`_build_forced_serial_plan` emits one only when a write exists), so its `has_side_effect` is already false by inference; after the change it is false by metadata, and the test pins it.

**Decisions**: one helper decides concurrency from the plan, and both `mode` and `scheduling_mode` read it, so the two cannot drift. It counts a batch with more than one group, or a non-sequential group with more than one call, as concurrent. `has_side_effect` is `any(pc.spec.is_write for pc in approved_calls)`. The serialization-event arguments stay as diagnostics. Alternative rejected: deriving `mode` from whether serialization events exist, which repeats the original inference.

**Predictable fallout check**: module size — `tool_run_recorder.py` is 5541 B of 24576 B, so the gate holds. Pinned counts — no test pins the recorder's outputs. Tool inventory — no `tools/*.py` change. Generated blocks — none for a private helper (Documentation Impact). Consumer scan — no persisted schema, public API, or shared constant changes, and `_scheduling_mode` and `_record_round_exec` are private with one caller each (`tool_runner.py:548`), so `tools/scan_change_consumers.py` is not required.

**Validation quality baseline** (Step 5): `radon cc scripts/agent/tool_run_recorder.py -s`: every function rank A (`_dag_bucket_label` A(5), `_record_round_exec` A(4)); `vulture scripts/agent/tool_run_recorder.py --min-confidence 80`: no findings (exit 0, file exists); `bandit scripts/agent/tool_run_recorder.py -c pyproject.toml`: no findings (exit 0, file exists); `diff-cover`: not run in this phase (a full coverage run was not performed); the Plan requires at least 90% on changed lines per `rules/toolchain.md` Completion checklist.

## Implementation steps
1. **Phase 1: Plan-shape tests first**
   - [ ] Create the four plan-shape tests plus the mixed, empty, consistency, and counter tests; the mode and side-effect assertions fail before Phase 2 (REQ-001, REQ-002, REQ-003, REQ-004; `tests/agent/test_tool_run_recorder.py`)
2. **Phase 2: Derive mode and side effect**
   - [ ] Add the plan-concurrency helper, use it in `_scheduling_mode` and for `mode`, and derive `has_side_effect` from `spec.is_write` (REQ-001, REQ-002, REQ-003, REQ-004; `scripts/agent/tool_run_recorder.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] Run the full validation sequence; hand off to `skills/deploy/SKILL.md` because `scripts/` changes (prerequisite: the change is committed and pushed first, and deploying is the user's decision, which has an approval gate) (REQ-001, REQ-002, REQ-003, REQ-004; `scripts/agent/tool_run_recorder.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_run_recorder.py` | Unit: four plan shapes plus mixed, empty, consistency, counters, against the real scheduler | `uv run pytest tests/agent/test_tool_run_recorder.py` | All pass; AC-1 to AC-5 hold |
| `scripts/agent/tool_runner.py` callers | Regression: runner and audit tests | `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_audit.py tests/agent/commands/test_cmd_mcp.py` | Pass; counters and events unchanged |
| Changed files | Format, lint, type, architecture, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml` | No findings |
| Full suite and coverage | Regression | `uv run python tools/run_validation_gates.py --full` (diff-cover at least 90%) | Pass |

## Risks
- **Risk**: The pending implementation procedures of the logical idempotency key Plan (mcpai004) change `PreparedToolCall` construction, which could change the recorder's inputs (likelihood: low) → **Mitigation**: the recorder reads only `pc.name` and `pc.spec`; re-run `tests/agent/test_tool_run_recorder.py` after those procedures are executed, as the Issue asks.
- **Risk**: A dashboard outside the repository keys on the old constant `parallel` (likelihood: unknown, UNK-01) → **Mitigation**: keys and vocabulary are unchanged; only values become accurate.
- **Risk**: The concurrency helper disagrees with how the runner really executes groups (likelihood: low) → **Mitigation**: the helper mirrors `_run_plan_batches` and `_run_group_calls`, and the consistency test runs the real scheduler's plans.
- **Risk**: The runner's debug label keeps the old inference (likelihood: certain, debug-only) → **Mitigation**: recorded as UNK-02, out of scope per the Issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Plan-shape tests first | Completed | — | 20261125-152456 |  |
| 2 | Phase 2: Derive mode and side effect | Completed | — | 20261125-152456 |  |
| 3 | Phase 3: Deployment & Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261125-142934_01_scripts_agent_tool_run_recorder.py.md | 1, 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140518_mcpai011_round-recording-accuracy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-142517
- **Related target files**: `scripts/agent/tool_run_recorder.py`, `tests/agent/test_tool_run_recorder.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Implementation Intent; `tool_run_recorder.py:142` | `scripts/agent/tool_run_recorder.py` | Phase 2 | AC-1, AC-2, AC-4 | `tests/agent/test_tool_run_recorder.py` | Confirmed by repository evidence |
| REQ-001 | Testing Expectations (four plan shapes) | `tests/agent/test_tool_run_recorder.py` | Phase 1 | AC-1, AC-2, AC-4 | `uv run pytest tests/agent/test_tool_run_recorder.py` | Explicit in issue |
| REQ-002 | Required Changes ("keep scheduling and display modes consistent"); `_scheduling_mode` misclassifies a pooled concurrent group | `scripts/agent/tool_run_recorder.py` | Phase 2 | AC-1, AC-2, AC-5 | `tests/agent/test_tool_run_recorder.py` | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria ("Recorded mode matches the scheduler's plan") | `tests/agent/test_tool_run_recorder.py` | Phase 1 | AC-5 | `uv run pytest tests/agent/test_tool_run_recorder.py` | Explicit in issue |
| REQ-003 | Implementation Intent (`PreparedToolCall.spec.is_write`); `tool_run_recorder.py:143` | `scripts/agent/tool_run_recorder.py` | Phase 2 | AC-3, AC-4 | `tests/agent/test_tool_run_recorder.py` | Confirmed by repository evidence |
| REQ-003 | Acceptance Criteria (single write; forced-serial read-only) | `tests/agent/test_tool_run_recorder.py` | Phase 1 | AC-3, AC-4 | `uv run pytest tests/agent/test_tool_run_recorder.py` | Explicit in issue |
| REQ-004 | Constraints (counters keep their meaning); Required Changes (serialization events stay diagnostics) | `scripts/agent/tool_run_recorder.py` | Phase 2 | AC-5 | `tests/agent/commands/test_cmd_mcp.py` | Explicit in issue |
| REQ-004 | Constraints | `tests/agent/test_tool_run_recorder.py` | Phase 1 | AC-5 | `uv run pytest tests/agent/test_tool_run_recorder.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261125-142934 -->
