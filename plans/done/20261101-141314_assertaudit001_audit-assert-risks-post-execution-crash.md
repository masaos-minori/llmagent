## Goal
- Replace the three bare `assert ctx.workflow.workflow_id` preconditions in `audit_tool_exec()`, `audit_approval()` and `log_approval_decision()` with one explicit, handled failure mode (a warning log and no event written, never an `AssertionError`, identical with and without `python -O`), and correct the two documents that currently describe the assertion error as intended behavior.

## Priority
Medium

## Scope
- **In-Scope**:
  - One private helper in `scripts/agent/tool_audit.py` that returns the workflow id or logs a warning and signals "skip"; the three writers call it in place of their `assert`, after their existing early returns, so the order of the current guards is unchanged.
  - Tests for each of the three writers with `workflow_id` `None` and `""`, plus a guard that the module contains no `assert` statement.
  - Update the two documentation sentences that state "results in an assertion error".
  - Record the raise-vs-skip decision and the `log_approval_decision` keep-vs-remove decision as owner-confirmable defaults.
- **Out-of-Scope**:
  - `scripts/agent/workflow_engine_adapter.py` per-turn wrapping and activation/deactivation (Issue Constraint and Out of Scope); this Plan only reads it.
  - Audit record content or schema beyond this precondition (Issue Out of Scope).
  - Removing `log_approval_decision` (it is listed in `registry/manifests/agent_api.yaml` and the generated API reference; removal is a separate decision, UNK-02).
  - Narrowing `audit_tool_exec`'s `if not mcp_request_id and not source` guard (toolaudit001) and the idempotency key (idemaudit001).
  - Resume of an existing workflow task with an empty `workflow_id` (adapter behavior; UNK-03).
- **Dependencies**:
  - Fix order: this Plan is first among the siblings that edit `audit_tool_exec`. `issues/20261003-180330_toolaudit001_audit-drops-denied-gateway-tool-calls.md` (open, not planned yet) narrows the early-return guard so a denied call (empty `mcp_request_id` and `source`) reaches the workflow check; it should land after this Plan so that path meets the explicit skip instead of an `assert`, and its denial test should run with a non-empty `workflow_id`. `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md` (open) also edits `audit_tool_exec`; no ordering requirement, the later change rebases.
  - `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (Frozen, rows `Pending`) edits `scripts/agent/tool_audit.py` (`audit_stage_completed`) and `tests/agent/test_tool_audit.py`: different function, add-only tests; compatible, no order needed.
  - `plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md` (Frozen, `Pending`) adds tests to `tests/agent/test_tool_audit.py` and does not edit `tool_audit.py`; compatible. It reuses `_args_preview_after_write`, whose context helper keeps a non-empty `workflow_id`; this Plan must not change that helper's default.
  - `plans/done/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` is completed: its `execution_snapshot_json` and `dedup_state` additions are already in `audit_tool_exec` and unchanged here.

## Background
`audit_approval`, `log_approval_decision` and `audit_tool_exec` each start with an `audit_logger is None` early return (and `audit_tool_exec` also returns early when both `mcp_request_id` and `source` are empty), then `assert ctx.workflow.workflow_id`. `WorkflowState.workflow_id` defaults to `None`. `WorkflowEngineAdapter.execute_turn()` calls `_init_workflow_task()` then `_activate_workflow()` for every turn, which sets it; `_deactivate_workflow()` resets it to `None`. The project coding constraint (`skills/DESIGN.md`) forbids `assert` in business logic. Two operations documents state the assertion error as documented behavior.

## Problem
Verified in Step 2. (1) The three asserts exist exactly as the Issue says, and they are stripped under `python -O`, which lets an empty `workflow_id` into a persisted event. (2) Only `audit_tool_exec` runs after a tool has executed (`execute_one_tool_call` calls it after `_execute_prepared_call`, outside the per-call exception boundary); `audit_approval` runs inside `check_approval`, before execution, from `run_approval_checks`. So the "post-execution crash" applies to `audit_tool_exec` alone. (3) The Issue's Documentation Impact (`N/A`) is wrong: `agent_10_02` and `agent_10_03` both say that calling the writers outside a workflow context "results in an assertion error". (4) The Issue contradicts itself on the fix: Implementation Intent says log a warning and skip, the AI Implementation Instruction says prefer raising; raising inside `audit_tool_exec` would reproduce the post-execution abort the Issue complains about.

## Reason for Change
An `assert` makes the failure mode accidental and build-dependent: under `-O` an event with an empty `workflow_id` is persisted; without `-O` an `AssertionError` aborts the tool batch after side effects have occurred and drops sibling results. The behavior should be deliberate and the documentation should state it.

## Implementation Intent
Add one private helper in `tool_audit.py` that reads `ctx.workflow.workflow_id`, and when it is falsy (`None` or `""`) logs a single warning through a module logger and tells the caller to skip writing the event. The three writers call it where the `assert` was. The warning names the writer and the tool or decision tool name only, never the arguments. Skip rather than raise is the recorded default (Design, UNK-01).

## Requirements
- `REQ-001`: None of `audit_tool_exec`, `audit_approval`, `log_approval_decision` (nor any other code in `tool_audit.py`) uses `assert` for the `workflow_id` precondition; when `ctx.workflow.workflow_id` is `None` or `""`, each writes no event, raises nothing, and logs exactly one warning that names the writer and the tool, without arguments; behavior is identical under `python -O`.
- `REQ-002`: Behavior when `workflow_id` is present is unchanged, and the existing guards keep their order and precedence: no `audit_logger` returns silently with no warning, and `audit_tool_exec`'s empty `mcp_request_id` and `source` early return still happens before the workflow check.
- `REQ-003`: Unit tests cover each of the three writers with `workflow_id` `None` and `""`, asserting no event, no exception, and the warning; and a test pins that `tool_audit.py` contains no `assert` statement.
- `REQ-004`: `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` and `docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md` no longer claim an assertion error; each states the skip-and-warn behavior.
- `REQ-005`: `log_approval_decision` is kept and given the same fix (default), with removal left to the owner (UNK-02); no signature, docstring first line, or registry change.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/tool_audit.py | Add a module logger and a private workflow-id helper that logs one warning and signals skip; replace the three `assert` statements in `audit_approval`, `log_approval_decision`, `audit_tool_exec` with calls to it; keep every other statement, signature and docstring first line unchanged | Each of the three functions holds an `assert ctx.workflow.workflow_id, ...` after its early returns; the module has no `logging` import today | REQ-001, REQ-002, REQ-005 / AC-1, AC-2, AC-5 | `rg -n assert scripts/agent/tool_audit.py` shows exactly three asserts, one in each of the three functions; `radon cc` grades `audit_tool_exec` B (9), the others A (checked in Step 3) | tests/agent/test_tool_audit.py | Verified |
| tests/agent/test_tool_audit.py | Add tests for the three writers with `workflow_id` `None` and `""` (no event, no exception, one warning via `caplog` on logger `agent.tool_audit`), a guard that no `ast.Assert` node exists in `tool_audit.py`, and an unchanged-behavior check that no warning is emitted when the logger is `None` | No test passes a falsy `workflow_id`; `_make_ctx` hardcodes `wf-test-id`; `TestLogApprovalDecision`, `TestAuditApprovalInv11` and `TestAuditToolExec` cover only the present-id path | REQ-001, REQ-002, REQ-003, REQ-005 / AC-1, AC-2, AC-3, AC-5 | `rg -n "workflow_id" tests/agent/test_tool_audit.py` finds only the `_make_ctx` assignment and INV-11 assertions of `wf-test-id`; `_make_ctx` is reusable by setting `ctx.workflow.workflow_id` per test (checked in Step 2) | itself | Verified |
| docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md | Replace the Key Constraints sentence that outside-workflow calls "result in an assertion error" with the skip-and-warn behavior | The sentence states the old behavior as a constraint (the Issue's "N/A: no operator-facing documentation describes this precondition" is wrong) | REQ-004 / AC-4 | Key Constraints bullet: "Calling writing functions for `tool_approval` / `tool_exec` outside of a workflow context will result in an assertion error." (checked in Step 2) | N/A: documentation; docs checkers in the Validation plan | Verified |
| docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md | Replace the same Key Constraints sentence with the skip-and-warn behavior | Same stale statement, second copy | REQ-004 / AC-4 | Key Constraints bullet: "Calling writing functions for `tool_approval` / `tool_exec` outside of a workflow context results in an assertion error." (checked in Step 2) | N/A: documentation; docs checkers in the Validation plan | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/context.py | `WorkflowState.workflow_id: str | None = None` is the field being checked | REQ-001 |
| scripts/agent/workflow_engine_adapter.py | `_activate_workflow` / `_deactivate_workflow` set and clear the field per turn; out of scope, must not change | REQ-001, UNK-03 |
| scripts/agent/tool_runner.py | `execute_one_tool_call` calls `audit_tool_exec` after execution, outside the per-call exception boundary | REQ-001 |
| scripts/agent/tool_approval.py | `check_approval` calls `audit_approval` before execution; the five call sites have no exception handler | REQ-001 |
| scripts/agent/tool_exceptions.py | `AuditUnavailableError` docstring records "silent return is the policy" when the audit logger is not configured, the precedent for skip over raise | REQ-001 |
| tests/agent/test_tool_runner.py | Its `_make_ctx` hardcodes a non-empty `workflow_id`; context for the call-chain tests | REQ-003 |
| tests/agent/test_audit_log_format.py | Calls `audit_tool_exec` with a mock context; must keep passing unchanged | REQ-002 |
| registry/manifests/agent_api.yaml | Lists the three writers' signatures and summaries; must stay valid, so signatures and docstring first lines do not change | REQ-005 |
| docs/23_agent/agent_13_reference-api-generated.md | Generated API table of the same signatures and summaries; drift check | REQ-005 |
| skills/DESIGN.md | The "explicit exceptions instead of `assert` in business logic" constraint | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): `tool_audit.py` contains no `assert` statement (bandit B101 findings on it drop from three to zero), and each of the three writers, called with `workflow_id` `None` or `""`, writes no event, raises nothing, and logs one warning naming the writer and tool (no arguments).
- AC-2 (REQ-002): With a non-empty `workflow_id`, all pre-existing tests in `tests/agent/test_tool_audit.py`, `tests/agent/test_audit_log_format.py`, `tests/agent/test_tool_approval_preflight.py` and `tests/agent/test_tool_runner.py` pass unchanged; with no audit logger, no warning is logged.
- AC-3 (REQ-003): The new tests fail against the current code (`AssertionError`) and pass after the change.
- AC-4 (REQ-004): Neither `agent_10_02` nor `agent_10_03` mentions an assertion error for these writers; each describes the skip-and-warn behavior; the docs checkers pass.
- AC-5 (REQ-005): `log_approval_decision` still exists with the same signature and summary line; the generated reference check passes.

## Tests
- REQ-001, REQ-003: parametrize over the three writers and over `workflow_id` in (`None`, `""`): assert the audit logger mock is not called, no exception, and `caplog` holds one `WARNING` on `agent.tool_audit` containing the writer name and tool name but no argument value. Add an `ast`-based test that `tool_audit.py` has no `ast.Assert` node (so the guarantee does not depend on how the tests are run).
- REQ-002: with a non-empty id, the existing tests stay unchanged; add one test that with `audit_logger = None` and `workflow_id = None` no warning is logged; and one that `audit_tool_exec` with empty `mcp_request_id` and `source` and `workflow_id = None` logs no warning (early return first).
- REQ-005: the `log_approval_decision` case is part of the parametrization.

## Documentation Impact
Required (REQ-004; the Issue's `N/A` is incorrect). Update the Key Constraints bullet in both `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` and `docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md` (the audit and observability pair reached via `docs/00_index.md` "Document References by Task"). State that these writers skip the event and log a warning when no workflow context is active, in operator terms and without naming code symbols beyond those already in the bullet. `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` INV-11 describes only the present-id behavior and needs no edit.

## Assumptions
- Skip-and-warn is the recorded default for all three writers: the Issue's own Reason for Change names the post-execution abort as the harm, which a raise inside `audit_tool_exec` would keep; the `AuditUnavailableError` docstring already establishes that silent return is the policy for a missing audit logger. Falsifiable by the REQ-001 tests; the owner may overrule in UNK-01.
- One consistent behavior for the three writers (rather than raise before execution, skip after) keeps the audit module's failure mode single and documented. Falsifiable by the shared parametrized test.
- A falsy-but-not-`None` value (`""`) is treated the same as `None`, because the existing `assert` rejected both and `TaskRecord.workflow_id` defaults to `""`.
- `log_approval_decision` has no caller under `scripts/` (only tests, confirmed by `rg` in Step 2), yet it stays because the registry manifest and the generated API reference list it; the fix is two lines and removing it widens scope to four more files.
- The warning must not include `args` (secret content; maskargs001 is hardening exactly that path); the tool name is already present in the event and in ordinary logs.
- Step 8b: `tools/check_plan_target_overlaps.py` names this Plan for `scripts/agent/tool_audit.py` (with wfrecovery001) and `tests/agent/test_tool_audit.py` (with wfrecovery001 and maskargs001); all judged compatible, see Scope Dependencies. No finding names the two documentation rows.
- Path B: four target files (more than 3), no public interface change; classification recorded in Step 3.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a missing `workflow_id` should raise or skip-and-warn (Issue Unresolved Questions; the Issue's Intent and AI Instruction disagree) | No owner decision; no legitimate call path outside a workflow was found, so neither choice is forced | Default: skip-and-warn (Assumptions). If the owner prefers raising for `audit_approval` and `log_approval_decision` (pre-execution), amend REQ-001 and the tests before implementation; `audit_tool_exec` stays skip because it runs after side effects | False |
| UNK-02 | Whether `log_approval_decision` should be removed instead of fixed (no caller under `scripts/`) | Owner decision; removal also touches `registry/manifests/agent_api.yaml`, the generated reference, and `tests/agent/test_tool_audit.py` | Default: keep and fix (REQ-005). If removal is chosen, file a separate issue or amend this Plan with those rows | False |
| UNK-03 | `_activate_workflow` copies `task.workflow_id` to the context, while `_init_workflow_task` substitutes a new uuid only for its returned value when a resumed task has none, so a resumed task with an empty stored `workflow_id` would leave the context empty (reaching these writers) | `existing_task_id` has no caller under `scripts/` today, so the path is unexercised; whether it is intended to be reachable is not stated | Out of scope here (adapter is excluded by the Issue). After this Plan the symptom is a warning and a missing audit event, not a crash; the owner may file a separate issue | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/tool_audit.py | Modify | Medium (imported by `tool_approval`, `tool_runner`, `tool_run_recorder` and `workflow_engine_adapter`; the three writers sit on every tool call) | 3 commits (30d) | High (single contributor) | Deployed runtime file under `scripts/agent/`: takes effect only after a deploy (hand-off to `skills/deploy/SKILL.md`) |
| tests/agent/test_tool_audit.py | Modify | Low (shared with wfrecovery001 and maskargs001 additions) | 4 commits (30d) | High (single contributor) | None: tests are not deployed |
| docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md | Modify | Low | 11 commits (30d) | High (single contributor) | None: docs are not deployed |
| docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md | Modify | Low | 7 commits (30d) | High (single contributor) | None: docs are not deployed |

## Design
- Path B (Step 3): four target files. Architecture: `tool_audit` imports `shared.*`, `agent.shared.models`, `agent.tool_enums`, `agent.tool_models`, `agent.tool_policy`, `agent.tool_result_formatter`; the change adds only the standard-library `logging` import, so no layer-contract or cycle change (`lint-imports`: 6 kept, 0 broken). Callers (rg over `scripts/`): `audit_tool_exec` from `tool_runner` only; `audit_approval` from `tool_approval` (five sites, before execution); `log_approval_decision` from no module under `scripts/`; `audit_workflow_start`, `audit_stage_completed` (the adapter) and `write_round_exec` (`tool_run_recorder`) are untouched.
- Decision 1, raise vs skip. Alternatives: (a) raise an explicit exception: safe only before execution, and inside `audit_tool_exec` it reproduces the abort-after-side-effects the Issue describes (the call site has no handler); (b) skip with a warning (chosen): one deliberate, documented failure mode, matches the module's existing "no logger, silent return" policy, and the warning keeps a trace; (c) write the event with an empty `workflow_id`: rejected, it persists the invalid record the Issue wants to avoid. Compatibility: callers see no new exception type; only the previously impossible case changes. Open as UNK-01.
- Decision 2, shape. A private helper returning `str | None` (the id, or `None` after logging) so each writer reads `workflow_id = ...; if workflow_id is None: return`; this removes the third copy of the same guard text and keeps `audit_tool_exec`'s complexity unchanged. The helper takes the writer name for the warning. The existing `ctx.workflow.workflow_id` uses in the events switch to the returned local value.
- Decision 3, `log_approval_decision` (dead code under `scripts/`): keep and fix (REQ-005, UNK-02).
- Failure path: the helper cannot raise (a `getattr`-free attribute read on the context and one `logger.warning`). Logging uses the module logger `agent.tool_audit` through `logging.getLogger(__name__)`, as `tool_runner` does. No data written, no state changed.
- Baseline (Step 5): `radon cc scripts/agent/tool_audit.py -s` grades `audit_tool_exec` B (9), `audit_approval` and `log_approval_decision` A (5); `vulture scripts/ --min-confidence 80` reports nothing on the target (its three findings are in other modules); `bandit` on the target reports exactly three Low/High-confidence B101 (assert_used) findings, one per writer, which this change removes (a clean `bandit` run on the target is part of AC-1); the diff-cover number needs a full-suite run and is deferred to the implementation phase, which must reach the threshold in `rules/toolchain.md`.
- Module size: `tool_audit.py` is 8317 bytes against the 20480 gate; no growth concern.

## Implementation steps
1. **Phase 1: Tests first (revertable alone)**
   - [ ] Add the parametrized skip-and-warn tests for the three writers with `workflow_id` `None` and `""`, the no-`ast.Assert` guard, and the two unchanged-order tests; confirm they fail with `AssertionError` before Phase 2 (REQ-001, REQ-002, REQ-003, REQ-005; tests/agent/test_tool_audit.py)
2. **Phase 2: Core logic**
   - [ ] Add `import logging`, the module logger, and the private workflow-id helper; replace the three asserts with helper calls placed after the existing early returns, and use the returned id in the events; leave signatures and docstring first lines unchanged (REQ-001, REQ-002, REQ-005; scripts/agent/tool_audit.py)
3. **Phase 3: Documentation**
   - [ ] Replace the assertion-error sentence in both Key Constraints lists with the skip-and-warn behavior (REQ-004; docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md, docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md)
4. **Phase 4: Deployment & Verification**
   - [ ] Run the validation sequence in the Validation plan, including the regression modules; hand off to `skills/deploy/SKILL.md` for the `scripts/` change (prerequisite: the change is committed and pushed first; deploying is the user's decision) (REQ-001..REQ-005; scripts/agent/tool_audit.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/tool_audit.py, tests/agent/test_tool_audit.py | Unit | `uv run pytest tests/agent/test_tool_audit.py` | New and existing tests pass |
| Audit writers' callers | Integration (regression) | `uv run pytest tests/agent/test_audit_log_format.py tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_runner.py` | Pass unchanged (AC-2) |
| scripts/agent/tool_audit.py | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml` per `rules/toolchain.md` | Clean |
| scripts/agent/tool_audit.py | Size gate | `uv run python tools/check_module_size.py` | Pass |
| scripts/agent/tool_audit.py | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` per `rules/toolchain.md` | At or above threshold |
| scripts/agent/ | Generated reference drift | `uv run python tools/generate_reference_table.py --check` | Pass (docstring first lines unchanged) |
| docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md, docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md | Docs checks | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` | Pass |
| scripts/agent/tool_audit.py | Behavior under `-O` | `uv run python -O -m pytest tests/agent/test_tool_audit.py -k workflow_id` (one-off check of the new tests) | Same outcome as without `-O` |

## Risks
- **Risk**: Skip-and-warn drops the audit record for a call that did execute (likelihood Low: no call path outside a workflow was found) → **Mitigation**: the warning names the writer and tool, so the loss is visible; the owner can choose raising for the pre-execution writers (UNK-01).
- **Risk**: The warning leaks argument secrets (likelihood Low) → **Mitigation**: REQ-001 forbids arguments in the message and the test asserts their absence.
- **Risk**: toolaudit001 lands first and its denial test reaches the old assert (likelihood Medium) → **Mitigation**: Scope Dependencies fix the order (this Plan first); if reordered, that Plan's tests must keep a non-empty `workflow_id`.
- **Risk**: Concurrent edits to `tests/agent/test_tool_audit.py` and `audit_tool_exec` by wfrecovery001, maskargs001, idemaudit001 (likelihood Medium) → **Mitigation**: add-only test additions in separate classes; function-level disjoint source edits; the later change rebases; `_make_ctx` default stays non-empty.
- **Risk**: A docstring edit drifts the generated API reference and the registry manifest (likelihood Low) → **Mitigation**: docstring first lines stay unchanged; `generate_reference_table.py --check` in the Validation plan.
- **Risk**: The resumed-task path can produce an empty `workflow_id` in the context (likelihood Low, unexercised) → **Mitigation**: now a warning rather than a crash; recorded in UNK-03 for the owner.
- **Risk**: The `scripts/` change takes effect only after deploy → **Mitigation**: Phase 4 hand-off to `skills/deploy/SKILL.md` after commit and push.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Tests first: skip-and-warn tests for the three writers, no-assert guard, order tests (tests/agent/test_tool_audit.py) | Completed | — | 2026-11-02 | Procedures 02 (skip-and-warn + no-assert + order pins); red evidence: 7 failed |
| 2 | Core logic: workflow-id helper and replacement of the three asserts (scripts/agent/tool_audit.py) | Completed | — | 2026-11-02 | Procedure 01; _workflow_id_or_skip added; 3 asserts removed |
| 3 | Documentation: replace the assertion-error sentence (docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md, docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md) | Completed | — | 2026-11-02 | Procedures 03, 04; both Key Constraints bullets replaced with identical skip-and-warn wording |
| 4 | Deployment and verification: validation sequence, regression modules, deploy hand-off (scripts/agent/tool_audit.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261102-132615_02_tests_agent_test_tool_audit.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261102-132615_01_scripts_agent_tool_audit.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261102-132615_03_docs_23_agent_agent_10_02_operations-and-observability-audit-and-otel.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261102-132615_04_docs_23_agent_agent_10_03_operations-and-observability-workflow-observability.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-141314
- **Related target files**: scripts/agent/tool_audit.py, tests/agent/test_tool_audit.py, docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md, docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (replace each assert); three asserts present in `tool_audit.py` | scripts/agent/tool_audit.py | 2 | AC-1 | Tests: three-writer parametrization; no-assert guard | Confirmed by repository evidence |
| REQ-001 | Issue Testing Expectations (workflow_id = None for each function) | tests/agent/test_tool_audit.py | 1 | AC-1, AC-3 | Tests: three-writer parametrization; no-assert guard | Explicit in issue |
| REQ-002 | Issue Constraints (behavior unchanged when `workflow_id` present); guard order in each writer | scripts/agent/tool_audit.py | 2 | AC-2 | Regression modules; order tests | Explicit in issue |
| REQ-002 | Issue Constraints; early-return tests exist for logger None and empty request id | tests/agent/test_tool_audit.py | 1 | AC-2 | Tests: order tests | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes and Testing Expectations (add a test per function) | tests/agent/test_tool_audit.py | 1 | AC-3 | Tests: three-writer parametrization; fail-before check | Explicit in issue |
| REQ-004 | `agent_10_02` Key Constraints bullet (Issue Documentation Impact says N/A) | docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md | 3 | AC-4 | Validation plan: docs checkers | Confirmed by repository evidence |
| REQ-004 | `agent_10_03` Key Constraints bullet (Issue Documentation Impact says N/A) | docs/23_agent/agent_10_03_operations-and-observability-workflow-observability.md | 3 | AC-4 | Validation plan: docs checkers | Confirmed by repository evidence |
| REQ-005 | Issue Dependencies note (`log_approval_decision` has no caller under `scripts/`; decide fix or remove) | scripts/agent/tool_audit.py | 2 | AC-5 | Validation plan: reference drift check | Needs confirmation |
| REQ-005 | Issue Dependencies note; function in the registry manifest and generated reference | tests/agent/test_tool_audit.py | 1 | AC-5 | Tests: three-writer parametrization | Needs confirmation |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261102-132615 -->