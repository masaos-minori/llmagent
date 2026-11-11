## Goal
Remove the redundant turn-start empty-result-repeat guard call inside `ToolLoopGuard.check_all` in `scripts/agent/tool_loop_guard.py`, making the single post-execution evaluation point explicit. This is a behavior-preserving cleanup: observable behavior when the guard is enabled or disabled stays identical.

## Priority
Low

## Scope
- **In-Scope**: Delete the `check_empty_result_repeat(message)` invocation from `ToolLoopGuard.check_all`. Update `check_all`'s docstring to drop "empty result" from the ordered guard list and add a one-line note that the empty-result guard is evaluated once per turn, after execution, in `LLMTurnRunner.run`.
- **Out-of-Scope**: `record_tool_result`, `scan_empty_result_repeat`, `check_empty_result_repeat`, `observe_availability` (the counting and post-execution-check machinery). The post-execution empty-result check in `LLMTurnRunner.run`. The disabled-by-default policy (`tool_empty_result_max_repeats = 0`). The `max_tool_turns` loop bound. Any change to `_empty_result_counts` or the early-break scan.
- **Dependencies**:
  - **Depends on**: `issues/done/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md` | phase all | the turn-start call is only redundant once tool001 wired the guard through `execute_one_tool_call`; tool001 is archived, so this dependency is already satisfied at current HEAD.

## Background
`ToolLoopGuard` guards the inner tool-call loop against dedup, cycle, retry, consecutive-error, stagnation, and empty-result repeats. In `LLMTurnRunner.run`, `check_all` is called at the top of every loop iteration, before tool execution, and runs cycle, stagnation, dedup, retry, and empty-result checks in order. After `execute_all_tool_calls` returns, `LLMTurnRunner.run` calls `check_empty_result_repeat` a second time (followed by `check_unavailable_repeat` and `check_error_limit`). `tool_runner.py:execute_one_tool_call` is the sole writer of the per-tool `_empty_result_counts`; `tool_runner.py:_run_group_calls` and `_run_plan_batches` also break early on `guard.scan_empty_result_repeat()`. Both repeat guards default to disabled (`tool_empty_result_max_repeats = 0`, `tool_unavailable_repeat_max_repeats = 0`) per `config_dataclasses.py`, documented in `docs/23_agent/agent_08_03_configuration-tools-memory.md`.

The turn-start redundancy only becomes observable after the guard was actually wired. It was not, until `issues/done/20261021-093421_tool001_empty-result-loop-guard-is-never-wired.md` (High, resolved): previously `record_tool_result` was reached through `getattr(ctx, "guard", None)`, which always returned `None`, so both the turn-start and post-execution checks were inert. That fix passes the per-turn guard explicitly to `execute_one_tool_call`, so the post-execution check now fires. The tool001 verification also noted that `check_all` runs before execution and its empty-result arm "can only ever inspect counts recorded by previous inner rounds" — the seed of this follow-up cleanup.

## Problem
The empty-result check inside `check_all` can never fire when the guard is enabled: any per-tool empty-result count that reaches the threshold is caught by the post-execution `check_empty_result_repeat` in the same turn, which fails that turn (`TurnResult(action="fail", reason="empty_result_repeat")`). Counts therefore never persist past a threshold crossing, so at the start of the next turn the turn-start occurrence reads a count strictly below the threshold and returns `None`. When the guard is disabled (default), `scan_empty_result_repeat` returns `None` immediately and neither occurrence fires. Either way the turn-start call performs no useful work.

## Reason for Change
The dead call reduces clarity. A maintainer reading `check_all`'s docstring ("Run cycle, stagnation, dedup, retry, and empty result guards in order") may assume the turn-start empty-result check is meaningful, when in fact the single real evaluation point is the post-execution check in `LLMTurnRunner.run`. Removing it makes the one-evaluation-per-turn topology explicit and removes a misleading code path. Severity belongs in Priority; the timing here is purely maintainability, not runtime risk.

## Implementation Intent
Delete the `check_empty_result_repeat(message)` invocation from `ToolLoopGuard.check_all` and drop "empty result" from its docstring's ordered guard list. Add a one-line note that the empty-result guard is evaluated once per turn, after execution, in `LLMTurnRunner.run`. Keep the post-execution check in `LLMTurnRunner.run` untouched. Preserve the guard's disabled-by-default behavior and all other guard ordering.

## Requirements
- `REQ-001`: Delete the `if msg := self.check_empty_result_repeat(message): return msg` line from `ToolLoopGuard.check_all` so it no longer calls `check_empty_result_repeat`.
- `REQ-002`: Update `check_all`'s docstring to remove "empty result" from the listed guards and add a one-line note pointing to the single post-execution evaluation in `LLMTurnRunner.run`.
- `REQ-003`: Preserve behavior exactly — the empty-result repeat is still detected via the post-execution check in `LLMTurnRunner.run` (failing the turn with `reason="empty_result_repeat"`), and with the guard disabled (`0`) no empty-result detection occurs.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Modify | Delete the turn-start `check_empty_result_repeat` call in `check_all` and update its docstring (REQ-001, REQ-002); behavior preserved (REQ-003) | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3 | `check_all` at `tool_loop_guard.py` calls `check_empty_result_repeat` at the turn start; the sole real evaluation point is the post-execution `check_empty_result_repeat` in `LLMTurnRunner.run` (checked in Step 3) | `tests/agent/test_tool_loop_guard.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/llm_turn_runner.py` | Confirm the post-execution `check_empty_result_repeat` in `LLMTurnRunner.run` is left untouched and that `check_all` is the turn-start call site | `scripts/agent/tool_loop_guard.py` |
| `tests/agent/test_tool_loop_guard.py` | Confirm an empty-result sequence crossing the threshold is still detected after the change and a disabled guard performs no detection | `scripts/agent/tool_loop_guard.py` |
| `tests/agent/test_llm_turn_runner.py` | Confirm post-execution detection and disabled-guard behavior are unchanged | `scripts/agent/tool_loop_guard.py` |

## Acceptance Criteria
- `ToolLoopGuard.check_all` no longer calls `check_empty_result_repeat` (REQ-001 / AC-1).
- The empty-result repeat is still detected via the post-execution check in `LLMTurnRunner.run` and fails the turn with `reason="empty_result_repeat"` (REQ-003 / AC-2).
- With the guard disabled (`0`), no empty-result detection occurs (unchanged) (REQ-003 / AC-3).
- `ruff`, `mypy`, and the affected test trees pass (AC-4).

## Tests
- Unit tests in `tests/agent/test_tool_loop_guard.py` and `tests/agent/test_llm_turn_runner.py`: confirm an empty-result sequence that crosses the threshold is still detected after the change, and that a disabled guard performs no detection. Run `uv run ruff check` and `uv run mypy --no-namespace-packages` on the two touched files (REQ-003 / AC-4).

## Documentation Impact
`N/A: no `docs/*.md` update required. `docs/23_agent/agent_08_03_configuration-tools-memory.md` correctly documents the default-off policy; the per-turn evaluation topology addressed here is internal and not part of that document's scope.`

## Assumptions
- The turn-start call is inert in both states: when enabled, the post-execution check fails the turn before any count can persist past a threshold crossing; when disabled, `scan_empty_result_repeat` returns `None` immediately. This was verified against current source in Step 2/3.
- No other in-turn writer of `_empty_result_counts` exists besides `tool_runner.py:execute_one_tool_call` → `record_tool_result`, so removing the turn-start call cannot change what the post-execution check observes.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| N/A | none | | | |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (small task): affects one source file, no public/runtime interface change, no database schema change. The change is a pure deletion plus a docstring edit; it does not alter the guard's counting, scanning, or post-execution-check machinery, nor the disabled-by-default policy. The one-evaluation-per-turn topology is: `check_all` (turn start) runs cycle/stagnation/dedup/retry and, redundantly, empty-result; the post-execution `check_empty_result_repeat` in `LLMTurnRunner.run` is the only place a threshold crossing is observed, because a crossing fails the turn before the count can persist. Removing the turn-start empty-result arm changes nothing observable.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path): one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`.

1. **Phase 1: Delete the redundant call**
   - [ ] Delete the `if msg := self.check_empty_result_repeat(message): return msg` line from `ToolLoopGuard.check_all` in `scripts/agent/tool_loop_guard.py` (REQ-001).
2. **Phase 2: Update the docstring**
   - [ ] Remove "empty result" from `check_all`'s ordered guard list and add a one-line note that the empty-result guard is evaluated once per turn, after execution, in `LLMTurnRunner.run` (REQ-002).
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run ruff check` and `uv run mypy --no-namespace-packages` on `scripts/agent/tool_loop_guard.py` (REQ-003 / AC-4).
   - [ ] Run `uv run pytest tests/agent/test_tool_loop_guard.py tests/agent/test_llm_turn_runner.py` to confirm empty-result detection still fires post-execution and a disabled guard performs no detection (REQ-003 / AC-2, AC-3).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_loop_guard.py` | Format + lint | `uv run ruff format scripts/` and `uv run ruff check scripts/` | clean |
| `scripts/agent/tool_loop_guard.py` | Type check | `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | no new errors |
| `tests/agent/test_tool_loop_guard.py` | Unit — empty-result sequence crossing threshold still detected; disabled guard performs no detection | `uv run pytest tests/agent/test_tool_loop_guard.py` | passes |
| `tests/agent/test_llm_turn_runner.py` | Unit — post-execution detection and disabled-guard behavior unchanged | `uv run pytest tests/agent/test_llm_turn_runner.py` | passes |

## Risks
- **Risk**: Removing the call could inadvertently change `check_all`'s ordering or drop a surrounding guard. → **Mitigation**: delete only the single empty-result line; leave cycle/stagnation/dedup/retry ordering intact; verify with the targeted test run and `git diff` review.
- **Risk**: A hidden in-turn writer of `_empty_result_counts` could make the turn-start call meaningful. → **Mitigation**: Step 2/3 confirmed `tool_runner.py:execute_one_tool_call` is the sole writer; re-run the consumer scan if the assumption is ever in doubt.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the redundant turn-start `check_empty_result_repeat` call in `check_all` | Completed | — | 20261111-221559 |  |
| 2 | Update `check_all` docstring (drop "empty result", add post-execution note) | Completed | — | 20261111-221623 |  |
| 3 | Verify: ruff, mypy, and affected test trees pass | Completed | — | 20261111-221623 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/done/20261111-215359_01_scripts_agent_tool_loop_guard.py.md | 1,2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261111-212552_tlg001_redundant-empty-result-guard.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-214106
- **Related target files**: `scripts/agent/tool_loop_guard.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261111-215359 -->