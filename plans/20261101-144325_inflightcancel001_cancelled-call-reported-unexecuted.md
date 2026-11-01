## Goal
Distinguish, in a tool round that stopped early by cancellation, a call that was never dispatched from a call whose request had already been sent to the MCP server, and record the former as "not executed" and the latter as "dispatched, outcome unknown; verify before repeating" instead of a single fixed "not executed" text.

## Priority
High

## Scope
- **In-Scope**:
  - Per-call dispatch tracking in `scripts/agent/tool_runner.py` (`_recorded_call`, `execute_all_tool_calls`).
  - Rounding completion that answers an in-flight call with an outcome-unknown text and a never-dispatched call with the existing not-executed text (`scripts/agent/tool_round_completion.py::complete_round`, `scripts/agent/tool_result_pairing.py::pair_round_results`).
  - Either a new `ToolCallStopReason` member (recommended) or a per-id text selection without a new enum member.
  - Round-completion and pairing tests with a blocking stub gateway and task cancellation.
  - Documentation of the two-case synthesized-row semantics.
- **Out-of-Scope**:
  - Changing the shutdown sequence or the graceful timeout (`scripts/agent/repl_input_loop.py` is read-only reference).
  - Retrying or reconciling an in-flight call after restart.
  - Repair of unpaired rows at session load (`scripts/agent/services/session_restore.py`).
  - Altering the real result path, the denial text, or the persistence boundary.
- **Dependencies**: `N/A: none`. No open issue or plan targets round completion or pairing. `issues/done/20261026-224729_turn002_repair-orphan-tool-call-rows.md` is archived background only; `plans/done/20261101-105136_toolstate001_tool-call-state-producer.md` covers kill-mid-call via pending/finalize rows by a different mechanism (related, not a duplicate).

## Background
When a tool round is cancelled (for example by a shutdown request during a turn), every declared call without a collected result is answered with the fixed text "Tool call not executed: the tool round did not complete." A call whose request had already been sent to the MCP server, but whose reply had not arrived, is in that group. The server may still complete it, so the stored history states that a possibly executed write did not happen. The next turn, or a later `/session load`, can then repeat it.

## Problem
Reproduction (throwaway script, not committed): a stub gateway that records the call and then waits, `_execute_with_dag` run as a task, the task cancelled after the gateway received the call, and `pair_round_results` with the resulting `collected` and `ROUND_NOT_COMPLETED`. Observed: the gateway had received the call (the request is "sent"), `collected` was empty, and the synthesized row text was "Tool call not executed: the tool round did not complete." No real server or database was used.

Effects:
- For a write, delete, or API-write tool, the model and the user are told the operation did not run when it may have. The transport's idempotency key is derived from tool name, arguments and session (`derive_idempotency_key`), so an identical replay in the same session is deduplicated server-side; the recorded statement is still wrong, and a replay with different arguments (or in another session) is not covered and can duplicate a write.
- For a read tool, the statement is also inaccurate, though a repeat is harmless.
- The row is persisted, so the wrong statement survives a restart.

## Reason for Change
Interrupting the agent while a tool call is running is routine (Ctrl-C, termination). The recorded history is the only account of what happened, and for writes a false "not executed" is worse than "unknown".

## Implementation Intent
Track the dispatch state of each call in the round: not started, dispatched without a result, finished. When completing a round that stopped early, synthesize the "not executed" text only for calls that were never dispatched, and a distinct "dispatched, outcome unknown; verify before repeating" text for calls that were in flight. Whether an in-flight write should instead be allowed to finish within the graceful shutdown window is a related design choice for the owner; the minimum change is the accurate text.

## Requirements
- `REQ-001`: Record, per call id, that the call was dispatched (before the transport is awaited) and clear or keep that marker when a result is collected.
- `REQ-002`: In round completion, answer an in-flight call with an outcome-unknown text and a never-dispatched call with the existing not-executed text, keeping one row per declared id.
- `REQ-003`: Keep the guard-stop text for calls skipped by a loop guard unchanged.
- `REQ-004`: Preserve the guarantee that every declared id is answered exactly once; the new text contains no tool arguments or output; no schema change.

## Implementation Target Files
**Freeze status**: Frozen (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_runner.py` | Add a per-round `dispatched_ids: set[str]` to `RoundState`; inside `_recorded_call`, add `pc.call_id` to it immediately before awaiting the transport (thread the set through `_execute_with_dag` → `_run_plan_batches` → `_run_group_calls` using the existing `collected` threading); clear it once the result is collected. | REQ-001, AC-001 | `_recorded_call` writes into `collected` only after `execute_one_tool_call` returns (tool_runner:89-105), so an awaiting call is absent from `collected`; `execute_all_tool_calls` catches `BaseException` and completes the round with `ROUND_NOT_COMPLETED` (tool_runner:516-522). | `tests/agent/test_tool_runner.py` | Verified |
| `scripts/agent/tool_round_completion.py` | Partition unanswered declared ids into never-dispatched vs in-flight via `RoundState.dispatched_ids` and emit the correct text per id; keep one row per declared id. | REQ-002, AC-001, AC-002 | `complete_round` (round_completion:71-80) calls `pair_round_results` once with all declared ids and one `_STOP_TEXT[reason]`; `RoundState` (round_completion:21-28) has no dispatch field today. | `tests/agent/test_tool_round_completion.py` | Verified |
| `scripts/agent/tool_result_pairing.py` | Supply the outcome-unknown text and select it per in-flight id; keep guard-stop and not-executed texts. If a new `ToolCallStopReason` member is added, map it in `_STOP_TEXT` so the dict stays total. | REQ-002, AC-003 | `pair_round_results` (result_pairing:29-51) uses one `_STOP_TEXT[stop_reason]` for every synthesized row; `seen` set prevents double-synthesis. | `tests/agent/test_tool_result_pairing.py` | Verified |
| `scripts/agent/tool_enums.py` | Add `ROUND_INFLIGHT` to `ToolCallStopReason` (recommended option) — every existing site must keep handling it. | REQ-002, D2 | `ToolCallStopReason` (enums:50-54) currently has exactly two members (`GUARD_STOP`, `ROUND_NOT_COMPLETED`), constructed only in `tool_runner.py` (518, 522) and matched only in `tool_result_pairing.py::_STOP_TEXT`. | `tests/agent/test_tool_result_pairing.py` | Verified |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Document the two-case synthesized-row semantics (never dispatched vs dispatched with unknown outcome) and the reason. | REQ-002, AC-001 | The doc states the "not executed" semantics of synthesized rows (doc:74); it does not distinguish the two cases. | `docs/00_index.md` Document References by Task | Verified |
| `tests/agent/test_tool_runner.py` | Cancellation test: block in a stub gateway, cancel the round task mid-flight, assert the in-flight call yields the outcome-unknown row, a never-dispatched call yields the not-executed row, completed calls keep their real result. | REQ-001, REQ-002, AC-001, AC-002, AC-004 | Issue Testing Expectations. | `tests/agent/test_tool_runner.py` | Verified |
| `tests/agent/test_tool_round_completion.py` | Unit: partition of unanswered ids by dispatch state yields the correct text per id; every declared id answered once. | REQ-002, AC-003 | `complete_round` answers each declared id (round_completion:66-81). | `tests/agent/test_tool_round_completion.py` | Verified |
| `tests/agent/test_tool_result_pairing.py` | Unit: in-flight ids get the outcome-unknown text, never-dispatched get not-executed, guard-stop unchanged; `_STOP_TEXT` stays total if a new member exists. | REQ-002, REQ-003, AC-003 | `pair_round_results` selects text per stop reason (result_pairing:19-51). | `tests/agent/test_tool_result_pairing.py` | Verified |

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
| `scripts/agent/repl_input_loop.py` | `_repl_loop` cancels `dispatch_task` and awaits a graceful timeout on shutdown (line 255, 280-283) — establishes that cancellation happens in normal operation and where the dispatch boundary is. | REQ-001 |
| `scripts/shared/http_transport.py` | `HttpTransport.call` treats write-tool transport failures as "server-side execution outcome is ambiguous... fail-closed, ADR-004" (line 267-281) — the precedent the round-completion path should mirror. | REQ-002, Design |
| `scripts/agent/services/session_restore.py` | Uses different wording for interrupted calls (line 28); read to avoid duplicating or contradicting its "[interrupted] tool call did not complete before session termination" text. | REQ-002 |
| `scripts/agent/tool_enums.py` | `ToolCallStopReason` definition and its two current members. | REQ-002, D2 |
| `scripts/agent/tool_executor_helpers.py` / `shared/http_transport.py::derive_idempotency_key` | Confirms the idempotency-key derivation the issue cites (dedup coverage caveat). | Background, Problem |

## Acceptance Criteria
- `AC-001`: After a cancellation with a call in flight, the persisted tool row for that call says the outcome is unknown and that the call may have run. (`REQ-001`, `REQ-002`)
- `AC-002`: A call that was never dispatched is still recorded as not executed. (`REQ-002`)
- `AC-003`: Every declared id still has exactly one tool row. (`REQ-002`, `REQ-004`)
- `AC-004`: Guard-stop calls keep the guard-stop text; completed calls keep their real result. (`REQ-003`)
- `AC-005`: The new tests fail on the current code and pass after the change. (all requirements)

## Tests
- Round-level cancellation test with a blocking stub gateway: cancel the round task while a call is in flight → outcome-unknown row; cancel before dispatch → not-executed row; completed calls keep their real result. Assert on history and persisted rows through `complete_round`. (`REQ-001`, `REQ-002`, `AC-001`, `AC-002`, `AC-004`, `AC-005`)
- Unit: `pair_round_results` returns the outcome-unknown text for in-flight ids and the not-executed text for never-dispatched ids, one row per declared id, guard-stop unchanged. (`REQ-002`, `REQ-003`, `AC-003`)
- Regression: run the tool runner, round completion, pairing and turn persistence tests; run `ruff` and `mypy --no-namespace-packages` on touched files.

## Documentation Impact
Required. `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` states the "not executed" semantics of synthesized rows (its round-completion section). Describe the two cases (never dispatched, dispatched with unknown outcome) and the reason (in-flight server execution is ambiguous; ADR-004 precedent). Driven by `REQ-002`. Named via `docs/00_index.md`'s "Document References by Task" table.

## Assumptions
- A call that was approved and entered execution (`_recorded_call`) but has no collected result at `ROUND_NOT_COMPLETED` time was dispatched (its request was sent); a call that was approved but never entered execution was never dispatched.
- The single `ROUND_NOT_COMPLETED` stop reason can legitimately produce two different per-call texts; the distinction is per call, not per round.
- Adding a `ToolCallStopReason` member is safe because the enum is constructed in only two sites and matched only in `_STOP_TEXT`; every member must stay mapped to a text.
- Cross-plan overlaps found by `check_plan_target_overlaps.py` are all **compatible** (no design contradiction; coordinate merge order when implementing):
  - `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` is also edited by `plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md`; the two edits target different sections (preparation checklist vs. synthesized-row semantics).
  - `scripts/agent/tool_runner.py` is also targeted by `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md`, which sets a `TurnState` operation-classification flag (REQ-006, `context.py`) — orthogonal to this Plan's `RoundState.dispatched_ids` tracking.
  - `tests/agent/test_tool_runner.py` is also targeted by `wfretry001`, which adds a distinct flag test; the two plans add separate test functions.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How to express the two texts: a new `ToolCallStopReason.ROUND_INFLIGHT` member (route in-flight calls through a second `pair_round_results` invocation) vs. a per-id text selection without a new enum member. | None required; implementation decision. | Recommend the new enum member (first-class, self-describing reasons); require `_STOP_TEXT` to stay total. Alternative: pass a `dispatched_ids` set plus a second text to `pair_round_results` and select per id, leaving the enum unchanged. | False |
| UNK-02 | Whether in-flight WRITE calls should get different text than in-flight READ calls (writes are the risky case). | None required; owner policy. | Minimum: one outcome-unknown text for all in-flight calls. Refine to write-specific wording only if the owner wants it. | False |
| UNK-03 | Whether in-flight write calls should be awaited to completion during the graceful shutdown window instead of cancelled. | Requires changing `repl_input_loop.py` shutdown logic, which is out of scope. | Non-blocking; related design choice flagged by the Issue. Keep cancellation (out of scope) and report only the accurate text for this Plan. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_runner.py` | add `dispatched_ids` tracking to `RoundState` + mark in `_recorded_call` | low — contained to the round data-flow already threaded via `collected`; no external caller | 11 | N/A (`git-fame` empty) | not applicable (rsynced) |
| `scripts/agent/tool_round_completion.py` | partition unanswered ids by dispatch state; emit per-id text | low — `complete_round` called once (tool_runner:494) | 3 | N/A (`git-fame` empty) | not applicable (rsynced) |
| `scripts/agent/tool_result_pairing.py` | per-id text selection / new `_STOP_TEXT` entry | low — `pair_round_results` called once (round_completion:77) | 1 | N/A (`git-fame` empty) | not applicable (rsynced) |
| `scripts/agent/tool_enums.py` | add `ROUND_INFLIGHT` member (recommended) | low — 2 construction sites, one match site | 1 | N/A (`git-fame` empty) | not applicable (rsynced) |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | document two-case synthesized-row semantics | none — documentation only | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_runner.py` | add cancellation test | none — test only | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_round_completion.py` | add partition unit | none — test only | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_result_pairing.py` | add per-id text unit | none — test only | N/A | N/A | not applicable (rsynced) |

Churn (30d) source: `git log --name-only --since=30.days -- <files> | sort | uniq -c`. `tool_runner.py`=11, `repl_input_loop.py`=5, `tool_round_completion.py`=3, `tool_result_pairing.py`=1, `tool_enums.py`=1 in the last 30 days. Operational dependency inspection: N/A — no server ports involved and no DB schema change (the `tool_call_state` table in `shared/mcp_dedup.py` is untouched by this Plan).

## Design
- **D1 — Dispatch tracking location**: Track dispatch inside `_recorded_call`, the single writer of `collected`, using a new `RoundState.dispatched_ids: set[str]`. Mark `pc.call_id` as dispatched immediately before awaiting the transport, and remove it once the result is stored. Thread the set through `_execute_with_dag` → `_run_plan_batches` → `_run_group_calls` → `_recorded_call` alongside the existing `collected` parameter, so the change stays within the module's current data flow and touches no signatures outside this chain. A call absent from `collected` at `ROUND_NOT_COMPLETED` and present in `dispatched_ids` is in flight; absent from both was never dispatched.
- **D2 — Expressing the two texts (open decision, see UNK-01)**: Two options. (A) Add `ToolCallStopReason.ROUND_INFLIGHT` and, in `complete_round`, split the unanswered declared ids into in-flight and never-dispatched, calling `pair_round_results` once per partition with the matching reason — keeps each row's reason self-describing; requires `_STOP_TEXT` to map the new member (dict stays total) and the regression suite to still pass. (B) Keep `ROUND_NOT_COMPLETED` and pass `dispatched_ids` plus a second text into `pair_round_results`, selecting per id — more localized, no enum-contract change. Recommend (A) for semantic clarity; (B) if the owner prefers to avoid expanding the enum.
- **D3 — One round, two texts**: The round stops with a single reason, but the two texts apply to different calls within that same `ROUND_NOT_COMPLETED` round. Both options therefore partition the unanswered ids (disjoint partitions preserve the exactly-once guarantee that `pair_round_results`'s `seen` set already enforces).
- **Option considered and rejected**: Derive "in flight" from `collected` absence alone. Rejected because an approved-but-never-started call (e.g. cancelled during approval) is also absent from `collected` and must stay "not executed", so a dispatch marker is required.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Dispatch tracking** (`scripts/agent/tool_runner.py`)
   - [ ] Add `dispatched_ids: set[str]` to `RoundState`; thread it through `_execute_with_dag` → `_run_plan_batches` → `_run_group_calls`; mark `pc.call_id` before awaiting the transport and clear it once the result is collected. (REQ-001)
2. **Phase 2: Per-id synthesis text** (`scripts/agent/tool_round_completion.py`, `scripts/agent/tool_result_pairing.py`, and per D2 `scripts/agent/tool_enums.py`)
   - [ ] Partition unanswered declared ids by `dispatched_ids`; emit in-flight → outcome-unknown text, never-dispatched → not-executed text; keep guard-stop unchanged; one row per declared id. (REQ-002, REQ-003)
3. **Phase 3: Tests** (`tests/agent/test_tool_runner.py`, `tests/agent/test_tool_round_completion.py`, `tests/agent/test_tool_result_pairing.py`)
   - [ ] Round-level cancellation test with a blocking stub gateway (in-flight → unknown, never-dispatched → not executed, completed → real result). (REQ-001, REQ-002, AC-001..AC-004, AC-005)
   - [ ] Unit: `pair_round_results` per-id text selection and exactly-once. (REQ-002, REQ-003, AC-003)
4. **Phase 4: Documentation** (`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`)
   - [ ] Document the two-case synthesized-row semantics and rationale (intent only). (REQ-002)
5. **Phase 5: Deployment & Verification**
   - [ ] Run `ruff` and `mypy --no-namespace-packages` on touched files; run the tool runner, round completion, pairing, and turn persistence suites; confirm the new tests fail on current code before the change and pass after. (all)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_runner.py` | Integration (cancellation via stub gateway) | `uv run pytest tests/agent/test_tool_runner.py` | new cancellation test fails pre-change, passes post-change |
| `scripts/agent/tool_round_completion.py` | Unit (id partition) | `uv run pytest tests/agent/test_tool_round_completion.py` | green |
| `scripts/agent/tool_result_pairing.py` | Unit (per-id text) | `uv run pytest tests/agent/test_tool_result_pairing.py` | green; `_STOP_TEXT` total |
| Whole tool-execution surface | Regression | `uv run pytest tests/agent/ -k "tool or round or pairing or persistence"` | green |

## Risks
- **Risk**: Adding a `ToolCallStopReason` member leaves `_STOP_TEXT` incomplete, breaking any test that exhausts the enum. → **Mitigation**: Map the new member in `_STOP_TEXT` (dict stays total) and run `test_tool_result_pairing.py`. Prefer Option B (no new member) if the owner wants to avoid the enum contract.
- **Risk**: Threading `dispatched_ids` through four functions risks diverging from the `collected` threading (a call marked dispatched but never executed would wrongly read as in flight). → **Mitigation**: Clear the marker when the result is collected (success or captured exception); the regression suite covers completed calls keeping their real result.
- **Risk**: High churn on `tool_runner.py` (11 commits / 30d) means the surrounding flow is actively changing. → **Mitigation**: Keep the change localized to `RoundState`/`_recorded_call` and the existing `collected` thread; do not touch execution or approval logic.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Dispatch tracking (`tool_runner.py`) | Pending | — | — | |
| 2 | Per-id synthesis text (`tool_round_completion.py`, `tool_result_pairing.py`, `tool_enums.py`) | Pending | — | — | |
| 3 | Tests (`tests/agent/`) | Pending | — | — | |
| 4 | Documentation (`agent_06_01_...md`) | Pending | — | — | |
| 5 | Deployment & Verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261101-073608_inflightcancel001_cancelled-call-reported-unexecuted.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-144325
- **Related target files**: scripts/agent/tool_runner.py, scripts/agent/tool_round_completion.py, scripts/agent/tool_result_pairing.py, scripts/agent/tool_enums.py, docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent / Required Changes; `_recorded_call` writes to `collected` only after `execute_one_tool_call` returns (tool_runner:89-105) | `scripts/agent/tool_runner.py` | 1 | AC-001 | `test_tool_runner.py` cancellation | Confirmed by repository evidence |
| REQ-002 | Implementation Intent / Required Changes; `complete_round` calls `pair_round_results` once with one text (round_completion:71-80) | `scripts/agent/tool_round_completion.py` | 2 | AC-001, AC-002 | `test_tool_round_completion.py` partition | Confirmed by repository evidence |
| REQ-002 | Implementation Intent / Required Changes; `pair_round_results` uses one `_STOP_TEXT[reason]` (result_pairing:19-51) | `scripts/agent/tool_result_pairing.py` | 2 | AC-003 | `test_tool_result_pairing.py` per-id text | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; `HttpTransport.call` ambiguity precedent (http_transport.py:267-281) | `scripts/agent/tool_enums.py` | 2 | AC-001 | `test_tool_result_pairing.py` (`_STOP_TEXT` total) | Confirmed by repository evidence |
| REQ-003 | Constraints ("Keep the guard-stop text") | `scripts/agent/tool_result_pairing.py` | 2 | AC-004 | `test_tool_result_pairing.py` guard-stop unchanged | Explicit in issue |
| REQ-004 | Constraints ("exactly once", "no args/output", "no schema") | `scripts/agent/tool_round_completion.py` | 2 | AC-003 | `test_tool_round_completion.py` one row per id | Explicit in issue |
| REQ-004 | Constraints ("exactly once", "no args/output", "no schema") | `scripts/agent/tool_result_pairing.py` | 2 | AC-003 | `test_tool_result_pairing.py` exactly-once | Explicit in issue |
