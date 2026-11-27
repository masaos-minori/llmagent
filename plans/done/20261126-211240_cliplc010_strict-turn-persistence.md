## Goal
- Make turn persistence all-or-nothing in practice: validate each phase group before writing, verify inserted-row counts, report compensation status explicitly, and pause a session whose compensation failed until recovery or a health check clears it.

## Priority
Medium

## Scope
- **In-Scope**: inserted-count returns from the repository write methods; pre-write phase-group validation on the turn path; compensation status (`completed`/`failed`/`not_needed`) on the persistence error and the turn result; degraded-session marking and next-turn refusal; safe public error formatting without raw SQLite details; documentation updates.
- **Out-of-Scope**: session transitions and generations (issue `20261119-145300_cliplc002_session-transition-generation`); changing the repository's skip-and-warn contract for non-turn callers; the compensation behavior established by the archived persis001 work.
- **Dependencies**: the session-transition Plan is complete and archived; its generation model is the integration point for the degraded state.
  - **Depends on**: `plans/done/20261122-232757_cliplc002_session-transition-generation.md` | all | the degraded-session state must integrate with the frozen session id/generation model that plan landed

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 10). Related archived work: `issues/done/20261115-081702_persis001_persistence-compensation-sqlite-only.md`, `plans/done/20261027-070403_turn001_atomic-turn-persistence.md`.

## Problem
Verified against current source at `90ec3d2809a53b24b15bfd7d1ae760f7bac595ca`; re-verified at `a6822e424e43651994f169c3a678ecaeb2f8c2dc` with line citations updated:

- `scripts/agent/turn_persistence.py` `_fail_from_error` (lines 213-232; the Issue's 218-225 is the log block) logs a compensation failure and raises `ConversationPersistenceError` chaining the original error. The error carries no compensation status, so the caller cannot distinguish a clean rollback from a failed compensation. Confirmed.
- `ConversationPersistenceError.__init__` formats `f"{message}: {cause}"`, putting raw SQLite error text into the public error string. Confirmed.
- `scripts/agent/session_message_repo.py` warns and skips invalid roles and a missing session id in non-strict mode (lines 85-98, 122-154) and skips invalid roles in `replace_messages` even in strict mode (line 178). `strict_mode` defaults to `False` and `scripts/agent/session.py` passes it through unchanged (lines 67-69, 281-282), so the turn path runs non-strict today. Confirmed.
- `save`, `save_many`, and `save_phase_grouped` return `None` — no inserted-row count (lines 80, 114, 381). Confirmed. `TurnPersistence` sets `_write_committed = True` after any successful call (lines 110, 125, 143, 163 — the `replace_messages` site at 163 was not cited at the original revision), so a zero-row write is treated as committed. Confirmed.
- `scripts/agent/turn_result.py` `TurnResult` has no compensation status field. Confirmed.
- No session degraded/paused state exists anywhere in `scripts/agent/`; the only "degraded" concepts are memory services and MCP capabilities, unrelated to turn persistence. Confirmed.

## Reason for Change
These gaps undermine the all-or-nothing persistence contract despite transaction support: a skipped message, a zero-row write, or a failed compensation is invisible to the caller and to the session state.

## Implementation Intent
Validate each phase group before writing on the turn path, require the inserted count to equal the expected count, report compensation status explicitly on the error and the turn result, mark the session degraded when compensation fails, and refuse the next turn until recovery or a health check clears the state. Public errors carry no raw SQLite details.

## Requirements
- `REQ-001`: Turn persistence validates each phase group before writing: any invalid role or missing session id rejects the whole group; the repository's skip-and-warn contract stays intact for non-turn callers (decision D2).
- `REQ-002`: Repository write methods return the inserted-row count; the boundary compares it with the expected count; a zero-row write is never marked committed.
- `REQ-003`: Compensation status `completed`, `failed`, or `not_needed` is exposed on `ConversationPersistenceError` and on `TurnResult`; the caller can distinguish compensation success from failure.
- `REQ-004`: A compensation failure marks the session degraded; the next turn is refused until recovery or a health check clears the state (clearing criteria: UNK-01).
- `REQ-005`: Public errors use safe summaries without raw SQLite details.
- `REQ-006`: Documentation states the compensation statuses and the degraded-session behavior.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed — see this Plan's Step 8 report in the workflow run).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/turn_persistence.py` | Pre-write phase-group validation; inserted-count comparison; compensation status on the error; safe public error format; degraded-session marking | No status on the error, raw cause in the public string, zero-row write treated committed | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005; AC-1, AC-2, AC-3, AC-4 | `scripts/agent/turn_persistence.py` lines 49-51 (`f"{message}: {cause}"`), 110/125/143/163 (`_write_committed`), 213-232 (compensation failure logged, original raised) | `tests/agent/test_turn_persistence.py` | Verified |
| `scripts/agent/session_message_repo.py` | `save`, `save_many`, `save_phase_grouped` return the inserted-row count; `replace_messages` rejects invalid roles in strict mode; non-strict skip-and-warn contract preserved | Counts missing; strict-mode gap in `replace_messages` | REQ-001, REQ-002; AC-1 | `scripts/agent/session_message_repo.py` lines 80, 114, 381 (`-> None`), 85-98 and 122-154 (skip-and-warn), 178 (skip even in strict mode) | `tests/agent/test_session_message_repo.py` | Verified |
| `scripts/agent/turn_result.py` | Add compensation status field with default `not_needed` | Turn result carries no compensation status | REQ-003; AC-2 | `scripts/agent/turn_result.py` lines 19-30 (frozen dataclass, no status field) | `tests/agent/test_llm_turn_executor.py` | Verified |
| `scripts/agent/session.py` | Hold the degraded-session state; refuse a turn entry while degraded; integrate with the generation model | No degraded state exists; the boundary needs a place to mark it | REQ-004; AC-3 | `scripts/agent/session.py` lines 44-97 (generation model), 281-282 (repo construction, `strict_mode` passthrough) | `tests/agent/test_repl_error_handling.py` | Verified |
| `scripts/agent/orchestrator.py` | Record the compensation status from the error in the persistence-error branch | The branch records `error_kind` only | REQ-003; AC-2 | `scripts/agent/orchestrator.py` lines 202-209 | `tests/agent/test_orchestrator.py` | Verified |
| `scripts/agent/repl_input_loop.py` | Refuse the next turn when the session is degraded; surface the compensation status distinctly | A degraded session must not silently continue | REQ-004; AC-3 | `scripts/agent/repl_input_loop.py` lines 392-394 (persistence-error branch) | `tests/agent/test_repl_error_handling.py` | Verified |
| `tests/agent/test_turn_persistence.py` | Fault-injection tests first: compensation success and failure, count mismatch, zero-row write, invalid role mixed with valid, missing session id | New behavior needs coverage | REQ-001, REQ-002, REQ-003, REQ-004; AC-1, AC-2, AC-3 | Issue Testing Expectations | itself | Verified |
| `tests/agent/test_session_message_repo.py` | Count-return tests; strict-mode rejection tests; pinned skip-and-warn assertions (lines 264-307) and the `replace_messages` None contract (line 655) stay valid under decision D2/D3 | Contract change needs coverage | REQ-001, REQ-002; AC-1 | `tests/agent/test_session_message_repo.py` lines 264-307, 655 | itself | Verified |
| `tests/agent/test_llm_turn_executor.py` | TurnResult processing with the compensation field | Field addition needs coverage | REQ-003; AC-2 | `tests/agent/test_llm_turn_executor.py` TurnResult assertions | itself | Verified |
| `tests/agent/test_orchestrator.py` | Persistence-error branch records compensation status | Branch behavior change | REQ-003; AC-2 | `tests/agent/test_orchestrator.py` persistence-error tests | itself | Verified |
| `tests/agent/test_repl_error_handling.py` | Degraded-session refusal test; distinct display of compensation failure | New behavior needs coverage | REQ-004; AC-3 | `tests/agent/test_repl_error_handling.py` lines 123-158 | itself | Verified |
| `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | State the compensation statuses and the degraded-session behavior | Documentation Impact | REQ-006 | `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` covers the persistence state model | N/A: documentation gate per `rules/tool-gates.md` | Verified |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | State the inserted-count contract and the strict-mode scope | Documentation Impact | REQ-006 | `docs/23_agent/agent_09_01_data-layer-session-db.md` line 38 describes `strict_mode` ownership | N/A: documentation gate per `rules/tool-gates.md` | Verified |
| `docs/23_agent/agent_13_reference-api-generated.md` | Regenerate the reference table after the changed public contracts | Generated-reference domain hit by the predictable fallout check | REQ-002, REQ-003, REQ-006 | `docs/23_agent/agent_13_reference-api-generated.md` lines 146, 236, 238 list `SessionMessageRepository`, `ConversationPersistenceError`, `TurnResult` | N/A: `generate_reference_table.py --check` | Verified |

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
- Write every `File Path` cell, every `tests/...py` path in `Related Tests`, and every path in
  `Implementation steps` in backticks: `tools/close_procedures_batch.py` and the companion check read
  only backticked paths. `uv run python tools/backtick_plan_related_tests.py plans/{filename}.md`
  normalizes a Plan, and `tools/check_workitem_structure.py` reports a plain path
  (`plain-path-citation`).

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/cli_view.py` | `write_turn_not_persisted` display port; the distinct-surface path stays, only its content may cite the status | REQ-003 |
| `scripts/agent/commands/output_port.py` | Output port the REPL display uses; `not affected: no interface change` | REQ-003 |
| `scripts/agent/config_dataclasses.py` | `MessageRoleConfig` defines the valid roles the pre-write validation uses; `not affected` | REQ-001 |
| `scripts/agent/llm_turn_runner.py` | `TurnResult` consumer; `not affected: additive field with default` | REQ-003 |
| `scripts/agent/llm_turn_executor.py` | `TurnResult` consumer; `not affected: additive field with default` | REQ-003 |
| `scripts/agent/tool_runner.py` | Non-turn repository caller (`save_many([])` guard path); `not affected` under decision D2 | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-002): Invalid or incomplete phase groups roll back fully; persisted count equals expected count; a zero-row write is never marked committed.
- AC-2 (REQ-003): The caller can distinguish compensation success and failure through the error and the turn result.
- AC-3 (REQ-004): A degraded session cannot silently continue; the next turn is refused until cleared.
- AC-4 (REQ-005): No raw SQLite error detail appears in public error strings.

## Tests
- Fault-injection tests are written first (Issue AI Implementation Instruction): invalid role mixed with valid messages; missing session id; inserted-count mismatch; compensation success and failure (`tests/agent/test_turn_persistence.py`, `tests/agent/test_session_message_repo.py`).
- Degraded-session refusal test (`tests/agent/test_repl_error_handling.py`); TurnResult field coverage (`tests/agent/test_llm_turn_executor.py`, `tests/agent/test_orchestrator.py`).
- Run ruff, mypy, import-linter, and the full test suite; diff-cover on the change.

## Documentation Impact
Yes. Compensation statuses and the degraded-session behavior. Target docs via `docs/00_index.md` "Document References by Task": Agent spec (state and persistence model, data-layer session DB). The three `docs/` rows in `Implementation Target Files` record the concrete files, including the regenerated reference table.

## Assumptions
- The repository's skip-and-warn contract stays for non-turn callers; strict enforcement applies to the turn path through pre-write validation in the boundary (decision D2), so no existing non-turn caller changes behavior.
- `TurnResult` field addition is additive with a default, so existing construction sites compile unchanged.
- The compensation behavior from the archived persis001 work (compensation delete via the repository, single transaction) stays intact; only its status reporting is added.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How the degraded state is cleared: which command or health check, and its criteria; no session-level state health check exists in `scripts/agent/` today | Re-verified at `a6822e424e43651994f169c3a678ecaeb2f8c2dc`: `/session health` exists (`scripts/agent/commands/command_defs_list.py` line 123, `scripts/agent/commands/cmd_session.py` lines 375-378) but is a session-DB maintenance job that does not touch session state; `rg` over `scripts/agent/` shows only memory, MCP capability, and config-reload "degraded", unrelated to turn persistence | User decision (2026-11-27): the Plan implements marking and refusal only and the clearing hook stays a defined seam; clearing criteria are deferred to a follow-up work item | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/turn_persistence.py` | Validation, count check, status, safe error, degraded marking | 10 `ConversationPersistenceError` candidates (2 display consumers) | 4 | N/A: `git-fame` unavailable in this environment | N/A: no deploy change |
| `scripts/agent/session_message_repo.py` | Count returns; strict-mode scope | 12 `SessionMessageRepository` candidates; 1 construction site in `scripts/agent/session.py` | 5 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/turn_result.py` | Additive status field | 24 `TurnResult` candidates (additive, default value) | 0 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/session.py` | Degraded state holder; turn-entry refusal | Session consumers across commands and REPL | 6 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/orchestrator.py` | Persistence branch records status | Turn lifecycle display path | 13 | N/A: `git-fame` unavailable | N/A: no deploy change |
| `scripts/agent/repl_input_loop.py` | Degraded-turn refusal | REPL turn loop | 3 | N/A: `git-fame` unavailable | N/A: no deploy change |

## Design
Grounded in the Path B analyses at HEAD `90ec3d2809a53b24b15bfd7d1ae760f7bac595ca`.

Validation quality baseline:
- radon: all target source files are complexity grade A (no hotspots).
- vulture: no dead code in the target files.
- bandit: no findings on the target files.
- diff-cover: no diff against `master` at HEAD, so the baseline is empty; coverage is measured on the change itself.
- import-linter: 6 contracts KEPT at HEAD; no new cross-layer imports are introduced (the status enum stays inside `agent/`).
- Historical analysis: churn per file recorded in `Affected areas`; `git-fame` (bus factor) unavailable in this environment.
- Overlap check disposition: at the original revision `check_plan_target_overlaps.py` reported `docs/23_agent/agent_13_reference-api-generated.md` targeted by this Plan and `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`. No contradiction: both rows only regenerate the generated reference table via `generate_reference_table.py --check`; regeneration is idempotent and reflects whichever contract change lands first. Re-run at `a6822e424e43651994f169c3a678ecaeb2f8c2dc`: cliplc009 has been consumed (`plans/done/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`), so no current overlap names this Plan.

Consumer scan results (`tools/scan_change_consumers.py`):
- Seed `ConversationPersistenceError` (10 candidates): target rows `scripts/agent/turn_persistence.py`, `scripts/agent/orchestrator.py`, `scripts/agent/repl_input_loop.py`; `scripts/agent/session_message_repo.py` docstring mentions are `not affected: comment only`; ADR test citations are `not affected: no assertion change beyond the target test rows`.
- Seed `TurnResult` (24 candidates): target rows `scripts/agent/turn_result.py`, `scripts/agent/orchestrator.py`; `scripts/agent/llm_turn_runner.py` and `scripts/agent/llm_turn_executor.py` are reference rows, `not affected: additive field with default`.
- Seed `SessionMessageRepository` (12 candidates): target rows `scripts/agent/session_message_repo.py`, `scripts/agent/session.py`; `scripts/agent/config_dataclasses.py` is `not affected: docstring reference only`; doc rows are targets.

Predictable fallout check:
- Module size gate (24576 B): all target files are below the gate (largest: `scripts/agent/session_message_repo.py` at 20370 B); no split row required.
- Pinned counts: `tests/agent/test_session_message_repo.py` lines 264-307 pin the skip-and-warn stats and line 655 pins the `replace_messages` nothing-persisted `None` contract; both stay valid under decisions D2 and D3, so they are `not affected` beyond new coverage.
- Tool inventory: N/A: no tool added or removed.
- Generated blocks: `docs/23_agent/agent_13_reference-api-generated.md` lists `SessionMessageRepository`, `ConversationPersistenceError`, and `TurnResult`; the contract changes require regeneration (`generate_reference_table.py --check`) — recorded as a target row.

Design decisions (Path B):
- D1 — Compensation status location: a `CompensationStatus` StrEnum defined in `scripts/agent/turn_persistence.py`, exposed as `ConversationPersistenceError.compensation` and as a defaulted `TurnResult` field. Alternative: status only on the error; rejected because the Issue requires it on the turn result too. Compatibility: frozen `TurnResult` gains a defaulted field, so construction sites are unchanged.
- D2 — Strict-mode scope: the boundary validates each phase group before dispatch (whole-group rejection on any invalid role or missing session id); the repository keeps its `strict_mode` flag with the non-strict default for non-turn callers. Alternative: flip `strict_mode` to `True` globally; rejected per the Issue AI instruction because it would change behavior for other repository callers and break the pinned skip-and-warn tests.
- D3 — Count contract: `save`, `save_many`, and `save_phase_grouped` return the inserted-row count; the boundary compares it with the expected count and raises through the normal failure path on mismatch; a zero-row write from a non-empty group is never marked committed. `replace_messages` keeps its `None` contract only for empty input.
- D4 — Degraded session: the flag lives on `AgentSession` (the generation-model owner); the boundary sets it when compensation fails; the turn entry refuses while degraded. The clearing criteria remain UNK-01 (blocking).
- D5 — Safe public error: the public string carries the message plus the exception type name, masked through `scripts/agent/secrets_masker.py`; the raw cause stays on `__cause__` and the `cause` attribute for internal logs only.

## Implementation steps
1. **Phase 1: Repository write contract**
   - [ ] Return inserted-row counts from `save`, `save_many`, `save_phase_grouped` in `scripts/agent/session_message_repo.py` (REQ-002)
   - [ ] Reject invalid roles in `replace_messages` under strict mode in `scripts/agent/session_message_repo.py` (REQ-001)
   - [ ] Fault-injection tests first in `tests/agent/test_session_message_repo.py` (REQ-001, REQ-002; AC-1)
2. **Phase 2: Boundary validation and compensation status**
   - [ ] Pre-write phase-group validation and count comparison in `scripts/agent/turn_persistence.py` (REQ-001, REQ-002; AC-1)
   - [ ] `CompensationStatus` enum and status on `ConversationPersistenceError`; safe public format in `scripts/agent/turn_persistence.py` (REQ-003, REQ-005; AC-2, AC-4)
   - [ ] Defaulted compensation field on `TurnResult` in `scripts/agent/turn_result.py` (REQ-003; AC-2)
   - [ ] Record the status in the persistence branch in `scripts/agent/orchestrator.py` (REQ-003; AC-2)
   - [ ] Tests in `tests/agent/test_turn_persistence.py`, `tests/agent/test_llm_turn_executor.py`, `tests/agent/test_orchestrator.py`
3. **Phase 3: Degraded session state**
   - [ ] Degraded-state holder and turn-entry refusal in `scripts/agent/session.py` (REQ-004; AC-3)
   - [ ] Boundary marks the session on compensation failure in `scripts/agent/turn_persistence.py` (REQ-004; AC-3)
   - [ ] Next-turn refusal and distinct display in `scripts/agent/repl_input_loop.py` (REQ-004; AC-3)
   - [ ] Tests in `tests/agent/test_repl_error_handling.py` (REQ-004; AC-3)
4. **Phase 4: Documentation, regeneration, and full validation**
   - [ ] Compensation statuses and degraded behavior in `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` (REQ-006)
   - [ ] Count contract and strict-mode scope in `docs/23_agent/agent_09_01_data-layer-session-db.md` (REQ-006)
   - [ ] Regenerate `docs/23_agent/agent_13_reference-api-generated.md` via `generate_reference_table.py --check` (REQ-006)
   - [ ] Deployment validation/scripts check: no deploy.sh change; confirm the deployed venv files are current per `skills/deploy/SKILL.md` after commit and push (user's decision to deploy)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/session_message_repo.py` | Unit: count returns, strict rejection, preserved skip contract | `uv run pytest tests/agent/test_session_message_repo.py` | Counts equal expected; pinned tests still pass |
| `scripts/agent/turn_persistence.py` | Unit + fault injection: compensation success/failure, count mismatch, zero-row write | `uv run pytest tests/agent/test_turn_persistence.py` | Status distinguishes clean rollback from failed compensation |
| `scripts/agent/turn_result.py` | Unit: defaulted field, construction sites unchanged | `uv run pytest tests/agent/test_llm_turn_executor.py` | Status recorded on the turn result |
| `scripts/agent/session.py` + `scripts/agent/repl_input_loop.py` | Unit: degraded marking and next-turn refusal | `uv run pytest tests/agent/test_repl_error_handling.py` | Degraded session cannot silently continue |
| `scripts/agent/orchestrator.py` | Unit: persistence branch records status | `uv run pytest tests/agent/test_orchestrator.py` | `error_kind` plus compensation status surfaced |
| Whole change | Full suite + static gates | `uv run pytest`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`, diff-cover | All pass; contracts KEPT; regenerated reference table current |

## Risks
- **Risk**: strict validation on the turn path could change behavior for non-turn repository callers → **Mitigation**: decision D2 keeps the non-strict contract for them; the Issue AI instruction requires stopping and reporting if any other caller's behavior changes; `scripts/agent/tool_runner.py` verified as a guard-path caller.
- **Risk**: count comparison could reject legitimate partial writes that the current contract tolerates (empty `save_many`) → **Mitigation**: decision D3 preserves the empty-input `None` contract; only non-empty groups with a count mismatch fail.
- **Risk**: the degraded-session clearing criteria are undecided (UNK-01, blocking) → **Mitigation**: implement marking and refusal with a defined clearing seam; do not invent a clearing command without the user's decision.
- **Risk**: `TurnResult` field addition could break frozen-dataclass equality tests that pin construction → **Mitigation**: consumer scan shows construction sites use defaults; `tests/agent/test_llm_turn_executor.py` coverage added.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Repository write contract | In Progress | — | — |  |
| 2 | Phase 2: Boundary validation and compensation status | In Progress | — | — |  |
| 3 | Phase 3: Degraded session state | In Progress | — | — |  |
| 4 | Phase 4: Documentation, regeneration, and full validation | In Progress | — | — | Deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261127-103439_01_scripts_agent_turn_persistence.py.md` | 2, 3 | Procedure | Completed | — | — |
| `implementations/20261127-103439_02_scripts_agent_session_message_repo.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261127-103439_03_scripts_agent_turn_result.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261127-103439_04_scripts_agent_session.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261127-103439_05_scripts_agent_orchestrator.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261127-103439_06_scripts_agent_repl_input_loop.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261127-103439_11_tests_agent_test_repl_error_handling.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261127-103439_12_docs_23_agent_agent_04_01_state-and-persistence-state-model.md.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261127-103439_13_docs_23_agent_agent_09_01_data-layer-session-db.md.md` | 4 | Procedure | Completed | — | — |
| `implementations/20261127-103439_14_docs_23_agent_agent_13_reference-api-generated.md.md` | 4 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-145308_cliplc010_strict-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261126-211240
- **Evidence revision**: a6822e424e43651994f169c3a678ecaeb2f8c2dc
- **Related target files**: `scripts/agent/turn_persistence.py`, `scripts/agent/session_message_repo.py`, `scripts/agent/turn_result.py`, `scripts/agent/session.py`, `scripts/agent/orchestrator.py`, `scripts/agent/repl_input_loop.py`, `tests/agent/test_turn_persistence.py`, `tests/agent/test_session_message_repo.py`, `tests/agent/test_llm_turn_executor.py`, `tests/agent/test_orchestrator.py`, `tests/agent/test_repl_error_handling.py`, `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`, `docs/23_agent/agent_09_01_data-layer-session-db.md`, `docs/23_agent/agent_13_reference-api-generated.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; `scripts/agent/session_message_repo.py` lines 85-98, 122-154, 178 | `scripts/agent/session_message_repo.py` | Phase 1 | AC-1 | `tests/agent/test_session_message_repo.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes; boundary pre-write validation | `scripts/agent/turn_persistence.py` | Phase 2 | AC-1 | `tests/agent/test_turn_persistence.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes; `scripts/agent/session_message_repo.py` lines 80, 114, 381 | `scripts/agent/session_message_repo.py` | Phase 1 | AC-1 | `tests/agent/test_session_message_repo.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; `scripts/agent/turn_persistence.py` lines 110, 125, 143, 163 | `scripts/agent/turn_persistence.py` | Phase 2 | AC-1 | `tests/agent/test_turn_persistence.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; `scripts/agent/turn_persistence.py` lines 213-232 | `scripts/agent/turn_persistence.py` | Phase 2 | AC-2 | `tests/agent/test_turn_persistence.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; `scripts/agent/turn_result.py` lines 19-30 | `scripts/agent/turn_result.py` | Phase 2 | AC-2 | `tests/agent/test_llm_turn_executor.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; `scripts/agent/orchestrator.py` lines 202-209 | `scripts/agent/orchestrator.py` | Phase 2 | AC-2 | `tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; no degraded state exists in `scripts/agent/` | `scripts/agent/session.py` | Phase 3 | AC-3 | `tests/agent/test_repl_error_handling.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; `scripts/agent/repl_input_loop.py` lines 392-394 | `scripts/agent/repl_input_loop.py` | Phase 3 | AC-3 | `tests/agent/test_repl_error_handling.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; `scripts/agent/turn_persistence.py` line 50 | `scripts/agent/turn_persistence.py` | Phase 2 | AC-4 | `tests/agent/test_turn_persistence.py` | Confirmed by repository evidence |
| REQ-006 | Documentation Impact | `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Phase 4 | N/A: documentation gate per `rules/tool-gates.md` | N/A: documentation gate | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; `docs/23_agent/agent_09_01_data-layer-session-db.md` line 38 | `docs/23_agent/agent_09_01_data-layer-session-db.md` | Phase 4 | N/A: documentation gate per `rules/tool-gates.md` | N/A: documentation gate | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; generated reference rows | `docs/23_agent/agent_13_reference-api-generated.md` | Phase 4 | N/A: documentation gate per `rules/tool-gates.md` | `generate_reference_table.py --check` | Confirmed by repository evidence |
