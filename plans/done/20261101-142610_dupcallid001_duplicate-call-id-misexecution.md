## Goal
Detect a tool call id that appears more than once in a single assistant message (round) during the preparation phase, reject every occurrence before the approval gate, and make the scheduler refuse duplicate ids instead of collapsing them — so no call runs with another call's arguments, no approved call is silently dropped, and each declared id gets a consistent answer.

## Priority
High

## Scope
- **In-Scope**:
  - Duplicate-call-id detection in `scripts/agent/tool_preparation.py::prepare_tool_calls`, rejecting all occurrences with a distinct `duplicate_id` failure kind, before `_run_approval_gate()`.
  - Defense-in-depth: `scripts/agent/tool_scheduler.py::build_execution_groups()` raises on duplicate ids instead of silently resolving multiple raw calls to one spec.
  - Round-level and unit tests for the above.
  - Documentation of the new preparation check and its reporting behavior.
- **Out-of-Scope**:
  - Normalizing or generating ids for providers that omit them.
  - The LLM streaming and accumulation path (`scripts/shared/llm_sse_helpers`, `scripts/agent/llm_turn_runner`).
  - Approval prompt content.
  - Changing how unique ids are processed (order, concurrency, results).
  - Rewriting the provider message ids.
- **Dependencies**: `N/A: none`. `issues/done/20261026-224729_turn002_repair-orphan-tool-call-rows.md` is archived background about unpaired rows at history load and does not cover duplicate ids within a round.

## Background
The tool round keys its working data by the model-supplied tool call id and never checks that the ids in one assistant message are unique. When two calls share an id, both scheduled entries resolve to the last prepared call: the second call's arguments execute twice and the first call's arguments never execute, even though the user approved each call separately. Only one result is collected for the two declared calls.

## Problem
Reproduction (throwaway script, not committed): two prepared write calls with the same id and different arguments, a stub gateway that records the arguments it receives, and `_execute_with_dag` with the real scheduler. Observed: the stub received the second call's arguments twice, in order, and never received the first call's; the collected results held one entry for the shared id. No real tool server or database was used.

Effects:
- A write the user approved is silently not performed, while a different write is performed twice. The transport's idempotency key is derived from tool name, arguments and session, so the duplicated run (identical arguments) is deduplicated server-side for tools that use the dedup store; the first call's arguments are still never executed and the history still answers two declared calls with one result.
- The history then has two declared calls and one answer for that id, which is an inconsistent pairing for the next request.
- Model output is untrusted input at this boundary: the id is chosen by the model or by the serving layer, and uniqueness is a convention, not something this code enforces. Whether a given model or server emits duplicate ids is `Needs confirmation`.

## Reason for Change
The preparation phase is documented as fail-closed ("parse, resolve, validate before approval"), but id uniqueness is not part of it, and the consequence is a wrong side-effecting call. The failure needs no bug in the model other than a repeated id.

## Implementation Intent
Treat a duplicated call id in one round as a preparation failure, before approval and scheduling, so that no call with a duplicated id executes and every declared occurrence is answered consistently. The owner decides the exact reporting (for example one tool error row per id explaining the duplication) within the constraint that no call may run with another call's arguments and that no approved call is silently dropped.

## Requirements
- `REQ-001`: During preparation, detect any call id that appears more than once in the batch and reject every occurrence (before the approval gate) with a distinct `duplicate_id` failure kind.
- `REQ-002`: `build_execution_groups()` raises instead of silently collapsing duplicate ids (defense-in-depth).
- `REQ-003`: After such a round, each declared id has exactly one consistent answer (real result, prep-failure, denial, or synthesized "not executed" row) in history and persisted rows.
- `REQ-004`: Rounds with unique ids are processed exactly as before (order, concurrency, results unchanged).
- `REQ-005`: The existing missing-id rejection is preserved.

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
| `scripts/agent/tool_preparation.py` | Add batch-level duplicate-call-id detection in `prepare_tool_calls`: after `_prepare_one`, move every `PreparedToolCall` whose `call_id` occurs more than once into `failures` via `_reject(..., "duplicate_id", ...)`. Update `_reject` docstring to list the new kind. | The batch loop applies only per-call checks; nothing compares ids across calls (checked 20261103) | REQ-001, AC-001, AC-002 | `prepare_tool_calls` (prep:149) builds one `PreparedToolCall` per raw call and rejects only a missing id; `_execute_with_dag` (tool_runner:434-435; re-verified 20261103, earlier citation 429-430 drifted) keys `call_specs`/`pc_by_id` by `call_id`, so a later occurrence overwrites an earlier one. | `tests/agent/test_tool_preparation.py` | Verified |
| `scripts/agent/tool_scheduler.py` | In `build_execution_groups`, raise when the walked raw calls contain a duplicate `id` before building phases. | The walk indexes `call_specs` per raw call with no id-uniqueness check (checked 20261103) | REQ-002, AC-001 | `build_execution_groups` (sched:276-283) walks raw calls and looks each up by id in `call_specs`; two raw calls produce two scheduled entries mapping to the same spec. | `tests/agent/test_tool_scheduler.py`, `tests/agent/test_tool_scheduler_comprehensive.py`, `tests/agent/test_tool_scheduler_serialization.py` | Verified |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | Add the id-uniqueness check to the preparation checklist and describe the duplicate-id reporting behavior (intent only). | The checklist and invariant do not mention id uniqueness (doc:49, 59-64) | REQ-001, REQ-003 | Prep checklist (doc:59-64) enumerates existence/JSON/resolution/schema/metadata checks with no uniqueness check; scheduling invariant (doc:49) documents the `call_id` key. | `docs/00_index.md` Document References by Task | Verified |
| `tests/agent/test_tool_preparation.py` | Add unit tests: a duplicated id moves both occurrences to `failures` with kind `duplicate_id` and none reaches `prepared`; the existing missing-id tests stay untouched. | No existing test covers duplicated ids in `prepare_tool_calls` | REQ-001, REQ-005; AC-002 | The file asserts per-call rejection tuples per failure class (configuration/unknown_tool/validation/schema); no duplicate-id case (checked 20261103) | tests/agent/test_tool_preparation.py | Verified |
| `tests/agent/test_tool_scheduler.py` | Add a unit test: `build_execution_groups` raises on duplicate ids; unique-id ordering/serialization tests unchanged. | No existing scheduler test passes duplicate ids | REQ-002, REQ-004; AC-004 | The file builds raw-call dicts and id-keyed `call_specs`; `test_unknown_tool_raises_missing_tool_spec` shows the raise-path test pattern (checked 20261103) | tests/agent/test_tool_scheduler.py | Verified |
| `tests/agent/test_tool_runner.py` | Add a round-level test with a stub gateway recording executed arguments: two calls sharing an id execute neither twice nor with wrong arguments, and the rejected call never reaches the approval prompt. | The silent-collapse behavior has no round-level coverage | REQ-001, REQ-003; AC-001, AC-002 | The file already drives round flows with stub registries/gateways (`ctx.services_required.gateway` stubs) (checked 20261103) | tests/agent/test_tool_runner.py | Verified |

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
| `scripts/agent/tool_runner.py` | `_execute_with_dag` (keys `call_specs`/`pc_by_id` by `call_id`) and `execute_all_tool_calls` (prep → approval → execution ordering, `RoundState.declared_ids`). Confirms rejecting in preparation keeps every dup call off the approval gate (AC-002). | REQ-001, REQ-003 |
| `scripts/agent/tool_round_completion.py` | `complete_round`/`_merge_in_declared_order` answer each declared id; unchanged by this Plan but must be read to confirm a rejected-dup round still answers every declared id (REQ-003). | REQ-003 |
| `scripts/agent/tool_result_pairing.py` | `pair_round_results` synthesizes rows for unanswered declared ids; unchanged but must be read to confirm no double-synthesis for a rejected id. | REQ-003 |
| `scripts/agent/tool_loop_guard.py` | `check_dedup` keys on `(name, args)` hash, not id — confirms the existing guard does not cover this bug and where the gap is. | Background, REQ-001 |
| `scripts/agent/tool_approval.py` | `run_approval_checks` — confirm denied/rejected calls never reach the approval prompt and that prep failures bypass it. | REQ-001, AC-002 |

## Acceptance Criteria
- `AC-001`: With two calls sharing an id, no tool runs with another call's arguments and no call runs more than once. (`REQ-001`, `REQ-002`)
- `AC-002`: A call rejected for a duplicate id never reaches the approval gate. (`REQ-001`)
- `AC-003`: Each declared id has a consistent, explicit answer in history after a duplicate-id round. (`REQ-003`)
- `AC-004`: Rounds with unique ids behave as before. (`REQ-004`)
- `AC-005`: The new tests fail on the current code and pass after the change. (all requirements)

## Tests
- `test_tool_calls` with two calls sharing an id and differing arguments: both become `duplicate_id` prep failures; neither appears in `prepared`. (`REQ-001`, `AC-001`, `AC-002`)
- `build_execution_groups` with duplicate ids raises; with unique ids unchanged. (`REQ-002`, `AC-004`)
- Round-level test with a stub gateway that records executed arguments: two calls sharing an id execute neither with the wrong arguments nor twice; the approval prompt is not shown for a rejected call. (`REQ-001`, `REQ-003`, `AC-001`, `AC-002`)
- Regression: run the tool runner, scheduler, preparation, approval and round completion tests; run `ruff` and `mypy --no-namespace-packages` on touched files.

## Documentation Impact
Required. `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` lists the preparation checks (its checklist enumerates existence, JSON parse, resolution, schema, and metadata checks without id uniqueness; its scheduler section documents the `call_id`-keyed invariant). Add the id-uniqueness check to the preparation checklist and describe the duplicate-id reporting behavior (intent only). Driven by `REQ-001`/`REQ-003`. Named via `docs/00_index.md`'s "Document References by Task" table.

## Assumptions
- A duplicated id within a round is always ambiguous and unsafe to resolve by "last wins"; the safe default is to reject.
- `error_type` values are free-form identifiers (no enum constrains them), so `duplicate_id` needs no schema change.
- Rejecting all occurrences in preparation is sufficient to satisfy the safety constraint; the scheduler guard is defense-in-depth only.
- A4 (20261103 adversarial verification, owner-approved amendment): the frozen table originally had no test-file rows although `Tests`/Phase 3 require test additions — three rows (`tests/agent/test_tool_preparation.py`, `tests/agent/test_tool_scheduler.py`, `tests/agent/test_tool_runner.py`) were added to satisfy `rules/workflow-lifecycle.md`'s one-row-per-modified-test-file rule; the first two are covered as companions of the code rows' documents, `test_tool_runner.py` gets its own document.
- A5 (20261103): all mechanism claims re-verified at HEAD — last-wins collapse via the `call_specs`/`pc_by_id` dicts (`tool_runner.py` L434-435, line drift corrected in the row evidence), `build_execution_groups` walks raw calls and looks each id up in `call_specs` (L276-283), `prepare_tool_calls` rejects only per-call conditions (missing id/name/JSON/schema/registry), `_merge_in_declared_order` consumes one failure row per declared occurrence and `pair_round_results`' `seen` guard prevents double synthesis (REQ-003/D4 confirmed). Overlap with `plans/20261101-144325_inflightcancel001_...` on the shared docs file is judged compatible (that Plan's Assumptions already record the same judgment: different sections).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a duplicated id should reject all calls that share it or keep the first. | None required; this is an implementation decision. | Implementer choice within the constraint that none runs with wrong arguments and none is silently dropped. Recommend reject-all (simplest, answers every occurrence). | False |
| UNK-02 | Whether any supported model or serving layer actually emits duplicate ids in one message. | Empirical evidence from live traffic; not available offline. | Non-blocking. Severity is driven by the unenforced-convention risk, not by confirmed occurrences. Keep the defensive fix regardless. | False |
| UNK-03 | Reporting shape: one error row per occurrence vs. one consolidated row per duplicated id. | Provider contract for duplicate `tool_call_id` values in responses is not checked here. | Non-blocking. If the provider contract forbids duplicate ids in responses, consolidate to one row per id; otherwise one row per occurrence is acceptable. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_preparation.py` | add duplicate-id detection + `duplicate_id` failure kind | low — preparation boundary, before approval and scheduling; approved unique-id flow unchanged | 0 | N/A (`git-fame` empty) | not applicable (rsynced) |
| `scripts/agent/tool_scheduler.py` | raise on duplicate ids in `build_execution_groups` | medium — scheduling engine; guarded path only fires on genuine duplicates | 2 | N/A (`git-fame` empty) | not applicable (rsynced) |
| `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | document id-uniqueness prep check + reporting | none — documentation only | N/A | N/A | not applicable (rsynced) |

Churn (30d) source: `git log --name-only --since=30.days -- <files> | sort | uniq -c`. `tool_runner.py`=11, `tool_loop_guard.py`=5, `tool_round_completion.py`=3, `tool_scheduler.py`=2, `tool_result_pairing.py`=1, `tool_preparation.py`=0 in the last 30 days.

## Design
- **D1 — Fix location (primary):** Detection lives in `prepare_tool_calls`, the batch-level preparation phase, which runs before `_run_approval_gate()` in `execute_all_tool_calls()`. Rejecting there means no call with a duplicated id is ever approved or scheduled, directly satisfying AC-002. The mechanism: after the per-call `_prepare_one` loop, count `call_id` occurrences among the successfully prepared calls; any `call_id` with count > 1 has all its `PreparedToolCall`s moved to `failures` via `_reject(..., "duplicate_id", ...)`, and the survivors stay in `prepared` in original order.
- **D2 — Defense-in-depth (secondary):** `build_execution_groups` already assumes unique ids (it walks raw calls and indexes by `call_id`). Add an explicit guard that raises on a duplicate `id` seen while walking the batch. In production this branch is unreachable once D1 rejects duplicates in preparation, but it turns any future bypass into a loud scheduling failure instead of a silent collapse. It fires only on genuine duplicates, so unique-id behavior is unchanged (REQ-004).
- **D3 — Failure kind:** Reuse the existing `_reject` helper (which tags `error_type` with a `kind`) and pass `"duplicate_id"`. `error_type` is a free `str` (no enum constrains it), so no DTO/schema change is needed; only the `_reject` docstring's kind list is updated.
- **D4 — Answering:** No change to `complete_round`/`pair_round_results` is required. Once duplicates are prep failures, `_merge_in_declared_order` consumes one failure row per declared occurrence and `pair_round_results` skips the already-answered id, so every declared id gets exactly one consistent answer (REQ-003). See UNK-03 for the optional consolidation of multiple same-id rows.
- **Option considered and rejected:** Fix downstream in `_execute_with_dag` by de-duplicating `call_specs`/`pc_by_id`. Rejected because it would still let a dup call through approval (violating AC-002) and would require reworking result collection; preparation is the earliest correct chokepoint.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Preparation-phase duplicate-id detection** (`scripts/agent/tool_preparation.py`)
   - [ ] In `prepare_tool_calls`, after the `_prepare_one` loop, detect `call_id`s occurring more than once and move all occurrences to `failures` via `_reject(..., "duplicate_id", ...)`; update `_reject` docstring kind list. (REQ-001, REQ-005)
2. **Phase 2: Scheduler defense-in-depth** (`scripts/agent/tool_scheduler.py`)
   - [ ] In `build_execution_groups`, raise on a duplicate `id` while walking the raw batch, before phase building. (REQ-002)
3. **Phase 3: Tests** (`tests/agent/test_tool_preparation.py`, `tests/agent/test_tool_scheduler*.py`, `tests/agent/test_tool_runner.py`)
   - [ ] Unit: `prepare_tool_calls` rejects a duplicated id (both occurrences fail, none prepared). (REQ-001, AC-002)
   - [ ] Unit: `build_execution_groups` raises on duplicate ids; unique-id ordering/concurrency unchanged. (REQ-002, AC-004)
   - [ ] Round-level: stub gateway records executed arguments; two calls sharing an id execute neither with the wrong args nor twice; rejected call never reaches approval. (REQ-001, REQ-003, AC-001)
4. **Phase 4: Documentation** (`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`)
   - [ ] Add the id-uniqueness check to the preparation checklist and describe duplicate-id reporting (intent only). (REQ-001, REQ-003)
5. **Phase 5: Deployment & Verification**
   - [ ] Run `ruff` and `mypy --no-namespace-packages` on touched files; run the tool runner, scheduler, preparation, approval, and round-completion test suites; confirm the new tests fail on current code before the change and pass after. (all)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_preparation.py` | Unit (radon baseline: `_prepare_one`=C) | `uv run ruff check scripts/agent/tool_preparation.py`; `uv run mypy --no-namespace-packages scripts/agent/tool_preparation.py` | clean; new kind typed as `str` |
| `scripts/agent/tool_scheduler.py` | Unit (radon: `build_execution_groups`=B) | `uv run ruff check scripts/agent/tool_scheduler.py`; `uv run mypy --no-namespace-packages scripts/agent/tool_scheduler.py` | clean; raise path covered |
| `tests/agent/test_tool_runner.py` | Round-level integration with stub gateway | `uv run pytest tests/agent/test_tool_runner.py` | new test fails pre-change, passes post-change |
| Whole tool-execution surface | Regression | `uv run pytest tests/agent/ -k "tool"` | green |

## Risks
- **Risk**: Rejecting all occurrences may produce two history rows carrying the same `tool_call_id`. → **Mitigation**: Both rows answer the two declared occurrences (constraint satisfied); if the provider contract forbids duplicate ids in responses, consolidate to one row per id (UNK-03, non-blocking).
- **Risk**: The scheduler raise could break a direct-call test that intentionally passes duplicate ids. → **Mitigation**: Run the scheduler test suites; the guard fires only on genuine duplicates, and any such test should be corrected to reflect the invariant.
- **Risk**: High churn on `tool_runner.py` (11 commits / 30d) means the surrounding flow is actively changing. → **Mitigation**: The fix does not modify `tool_runner.py`; keep the change localized to preparation and the scheduler to limit exposure.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation-phase duplicate-id detection (`tool_preparation.py`) | In Progress | — | — |  |
| 2 | Scheduler defense-in-depth (`tool_scheduler.py`) | In Progress | — | — |  |
| 3 | Tests (`tests/agent/`) | In Progress | — | — |  |
| 4 | Documentation (`agent_06_01_...md`) | In Progress | — | — |  |
| 5 | Deployment & Verification | Pending | — | — |  |

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
- **Source issue**: issues/20261101-073525_dupcallid001_duplicate-call-id-misexecution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-142610
- **Related target files**: scripts/agent/tool_preparation.py, scripts/agent/tool_scheduler.py, docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md, tests/agent/test_tool_preparation.py, tests/agent/test_tool_scheduler.py, tests/agent/test_tool_runner.py — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen` (amended 20261103 per A4)

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Required Changes; `prepare_tool_calls` builds one `PreparedToolCall` per raw call and rejects only a missing id (prep:149, 81-88); `_execute_with_dag` keys `call_specs`/`pc_by_id` by `call_id` (tool_runner:434-435, re-verified 20261103) | `scripts/agent/tool_preparation.py` | 1 | AC-001, AC-002 | `test_tool_preparation.py` dup-rejection unit | Confirmed by repository evidence |
| REQ-001 | Problem / Required Changes | `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` | 4 | AC-001, AC-003 | N/A: documentation change | Confirmed by repository evidence |
| REQ-002 | Problem; `build_execution_groups` walks raw calls and looks each up by id (sched:276-283) | `scripts/agent/tool_scheduler.py` | 2 | AC-001 | `test_tool_scheduler*.py` raise-on-duplicate | Confirmed by repository evidence |
| REQ-003 | Problem (inconsistent pairing); `complete_round`/`pair_round_results` answer each declared id (unchanged) — enabled by REQ-001's rejection | `scripts/agent/tool_preparation.py` | 1 | AC-003 | `test_tool_runner.py` round-level | Derived from confirmed evidence |
| REQ-004 | Constraints ("Do not change how unique ids are processed") | `scripts/agent/tool_preparation.py` | 1 | AC-004 | Regression: full tool-execution suite | Confirmed by repository evidence |
| REQ-004 | Constraints ("Do not change how unique ids are processed") | `scripts/agent/tool_scheduler.py` | 2 | AC-004 | Regression: scheduler suites | Confirmed by repository evidence |
| REQ-005 | Constraints ("Keep the existing missing-id rejection"); `_prepare_one` rejects a missing id (prep:81-84) | `scripts/agent/tool_preparation.py` | 1 | AC-001 | `test_tool_preparation.py` missing-id regression | Confirmed by repository evidence |
| REQ-001 | 20261103 table amendment (A4): unit coverage row | `tests/agent/test_tool_preparation.py` | 3 | AC-002 | dup-rejection unit tests | Confirmed by repository evidence |
| REQ-002 | 20261103 table amendment (A4): unit coverage row | `tests/agent/test_tool_scheduler.py` | 3 | AC-004 | raise-on-duplicate unit test | Confirmed by repository evidence |
| REQ-003 | 20261103 table amendment (A4): round-level coverage row | `tests/agent/test_tool_runner.py` | 3 | AC-001, AC-002 | stub-gateway round-level test | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261103-080412 -->