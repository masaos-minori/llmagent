# Plan: Implement Agent-managed replay on the unified logical call id

## Goal
- Reuse the original logical call id for an approved reissued call through a one-time Agent-managed `ReplayDirective`, so an interrupted call reconnects to its durable `tool_call_state` row while the LLM never sees, emits, or edits the id.

## Priority
High

## Scope
- **In-Scope**:
  - `ReplayDirective` type (original id, task id, original call id, tool name, canonical argument hash), matched during preparation, consumed once.
  - Directive matching in `prepare_tool_calls` / `_prepare_one`: attach the original id to the reissued call's execution context; fail closed with a structured ambiguity error when several directives match.
  - Directive reconstruction at turn entry from the persisted `tool_call_state` rows; add the `args_hash` column to `tool_call_state` so matching survives a restart (Required Changes item 3 resolved by Design decision D1).
  - Removal of the logical call id from the LLM-facing replay control text in `build_turn_control_message`.
  - Update of every intermediate type and test of the replay path in the same change set.
- **Out-of-Scope**:
  - The logical call id itself, execution context, propagation, keyless rejection, and state-row migration (mcpdl001, closed).
  - Dispatcher and ledger semantics (mcpai001, mcpdl002), dedup state and turn id audit fields (mcpai007), dry-run context (mcpai005).
  - The MCP design-document final sweep (mcpai012); the stale composed-key claim in `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` is owned by that sweep, not by this Plan.
  - `scripts/agent/llm_turn_executor.py` and `scripts/agent/conversation_state_manager.py`: verified in Step 3 to carry no replay logic, so they are reference rows, not modification targets.
- **Dependencies**: Closed — mcpdl001 (the logical call id) and mcpai001 (the dispatcher replay states) are archived with their Plans; mcpdl004 (call-state control API, recovery ownership) is also archived. No open dependency remains, so no `Depends on` bullet.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 4), follow-on of archived idemaudit001 (audit-versus-wire key mismatch). The id unification moved to mcpdl001 (closed); this Plan keeps only the replay directive. Step 2 confirmed the Issue's two `Needs confirmation` claims against current source: the control message instructs the LLM to re-issue calls with no binding to the stored key, and `build_turn_control_message` prints `idempotency_key` to the LLM in both the replayable and unreplayable sections.

## Problem
A reissued call gets a fresh uuid7 from `_logical_call_id` at preparation, so recovery cannot reconnect it to the original durable `tool_call_state` row even though the control text claims the dispatcher deduplicates "by the recorded key". The control text also shows the id to the LLM, which the Issue's constraint forbids. Both claims reproduce against current source (confirmed by repository evidence in Step 2).

## Reason for Change
At-most-once behavior after an interruption needs the reissued call to reuse the original id under Agent control. The dispatcher states that final acceptance depends on (mcpai001) are landed.

## Implementation Intent
On recovery the Agent internally attaches the original id to an approved reissued call through a one-time `ReplayDirective` held in Agent-controlled context (`TurnState`), not in tool arguments or editable LLM text. No directive is created for a non-retryable or outcome-unknown operation. Fail closed on ambiguity. Directives are not stored in a new table: they are reconstructed from the persisted `tool_call_state` rows, which already hold the original id, task id, and tool name; the missing field is the canonical argument hash, added as the `args_hash` column.

## Requirements
- `REQ-001`: Add `ReplayDirective` (original id, task id, original call id, tool name, canonical argument hash, consumed flag); each directive is consumed at most once.
- `REQ-002`: Match a reissued call during preparation by tool name plus canonical argument hash against the directives for the current task, and attach the original id to the prepared call's execution context; the LLM never emits or edits the id.
- `REQ-003`: Fail closed with a structured ambiguity error when several directives match one reissued call; the call is rejected at preparation and never dispatched.
- `REQ-004`: Create no directive for a non-retryable or outcome-unknown operation; directives are built only from `interrupted` rows whose `retry_class` is `retryable`.
- `REQ-005`: The LLM-facing replay control text must not contain the logical call id; it names the tool and the canonical argument hash only.
- `REQ-006`: Directives survive a restart: `tool_call_state` gains the `args_hash` column, the write path populates it, and directives are reconstructed from persisted rows at turn entry; consumption is recorded durably by the row's state transition.
- `REQ-007`: Update every intermediate type and test of the replay path in the same change set (Protocol, dataclass, engine contract, adapter carry, test fakes).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed 20261125: all 21 rows `Verified`, `tools/audit_plan_target_paths.py` 0 findings, `tools/check_plan_target_overlaps.py` no conflict)

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/schema_sql.py | Modify | Add the `args_hash` column to the `tool_call_state` canonical DDL | REQ-006 | `build_workflow_schema_sql()` `tool_call_state` DDL has no `args_hash` column (checked in Step 3) | tests/db/test_create_schema.py (read; asserts only `snapshot_id` absence, not affected) | Verified |
| scripts/agent/workflow/tool_call_state_ops.py | Modify | `record_tool_call` stores `args_hash`; `ToolCallState` and `_row_to_state` gain the field; add directive reconstruction from persisted `interrupted` replayable rows | REQ-001, REQ-006 | `record_tool_call()` INSERT column list and `ToolCallState` dataclass lack `args_hash`; `classify_stale_pending()` is the turn-entry entry point (checked in Step 3) | tests/agent/workflow/test_workflow_state_store.py | Verified |
| scripts/agent/workflow/state_store.py | Modify | `StateStore.record_tool_call` passes `args_hash` through to `tool_call_state_ops` | REQ-006 | `StateStore.record_tool_call` delegates to `tool_call_state_ops.record_tool_call` (checked in Step 3) | tests/agent/workflow/test_workflow_state_store.py | Verified |
| scripts/agent/context.py | Modify | `ToolCallRecorder` Protocol `record_tool_call` signature gains `args_hash`; `TurnState` gains the per-turn `replay_directives` field (Agent-controlled directive holder) | REQ-001, REQ-002, REQ-006 | `ToolCallRecorder` Protocol and `TurnState` in `scripts/agent/context.py`; `TurnState` is the per-turn transient state the Issue's constraint requires (checked in Step 3) | tests/agent/test_tool_runner.py (recorder fake) | Verified |
| scripts/agent/tool_runner.py | Modify | The recorder call site passes the canonical argument hash already carried on the prepared call's execution context | REQ-006 | `tool_runner` calls `recorder.record_tool_call` (line 202) and does not import `_canonical_args_hash`; the hash is read from `ToolExecutionContext.args_hash`, so no new import is added (corrected in `plan-to-implementation-procedure` Step 3a) | tests/agent/test_tool_runner.py | Verified |
| scripts/agent/tool_preparation.py | Modify | Add the `ReplayDirective` dataclass; match a reissued call in `_prepare_one` by tool name plus canonical argument hash; attach the original id to the prepared call's context; consume each directive once; fail closed on ambiguity with a structured error | REQ-001, REQ-002, REQ-003 | `_prepare_one` generates the fresh uuid7 via `_logical_call_id`; `_canonical_args_hash` and the `_reject` failure path exist in the same module (checked in Step 3) | tests/agent/test_tool_preparation.py | Verified |
| scripts/agent/workflow/workflow_engine.py | Modify | Change `build_turn_control_message` to return a `TurnControl` (control text plus directives); the control text names tool and `args_hash` only, never the id; build directives only from `interrupted` rows with `retry_class` `retryable` | REQ-004, REQ-005 | `build_turn_control_message` prints `idempotency_key` in the replay and unreplayable lines and splits replayable/non-retryable by `retry_class` (checked in Step 3) | tests/agent/workflow/test_workflow_engine.py | Verified |
| scripts/agent/workflow_engine_adapter.py | Modify | Consume the `TurnControl`: pass the control text unchanged to the executor and register the directives on `ctx.turn.replay_directives` for the turn | REQ-002, REQ-005 | `_run_execute_stage` calls `build_turn_control_message` and passes `control_message` to `handle_llm_turn` (checked in Step 3) | tests/agent/workflow/test_adapter_guards.py | Verified |
| tests/agent/test_tool_preparation.py | Modify | Add directive matching, one-time consumption, and ambiguous-match fail-closed tests | REQ-001, REQ-002, REQ-003 | Module already tests `_logical_call_id` (checked in Step 3) | — | Verified |
| tests/agent/test_tool_runner.py | Modify | Recorder fake implements the changed Protocol; add the test that a replayed call records the original id and `args_hash` in the state row | REQ-002, REQ-006 | File imports `PreparedToolCall` and `_canonical_args_hash` and exercises the recorder path (checked in Step 3) | — | Verified |
| tests/agent/workflow/test_workflow_engine.py | Modify | Update the control-message assertions (no id in text); add directive-construction tests incl. no directive for non-retryable and outcome-unknown rows | REQ-004, REQ-005 | File asserts `idempotency_key=` appears in the control message and calls `build_turn_control_message` (checked in Step 3) | — | Verified |
| tests/agent/workflow/test_workflow_state_store.py | Modify | Update the `record_tool_call` call sites for the new `args_hash` argument | REQ-006, REQ-007 | 18 `store.record_tool_call` call sites in the file (checked in Step 3) | — | Verified |
| tests/agent/workflow/test_workflow_status_vocabulary.py | Modify | Update the `record_tool_call` call sites for the new `args_hash` argument | REQ-006, REQ-007 | 2 `record_tool_call` call sites in the file (checked in Step 3) | — | Verified |
| tests/agent/test_mcp_call_recovery.py | Modify | Update the recorder fake / call site for the new `args_hash` argument | REQ-006, REQ-007 | 1 `record_tool_call` call site in the file (checked in Step 3) | — | Verified |
| tests/agent/test_orchestrator.py | Modify | Update the hand-written fake engine's `build_turn_control_message` to the `TurnControl` contract | REQ-007 | Fake engine defines `build_turn_control_message` mirroring the contract (checked in Step 3) | — | Verified |
| tests/agent/workflow/test_no_workflow_bypass.py | Modify | Update the hand-written fake engine's `build_turn_control_message` to the `TurnControl` contract | REQ-007 | Fake engine defines `build_turn_control_message` (checked in Step 3) | — | Verified |
| tests/agent/workflow/test_adapter_guards.py | Modify | Update the engine mock's `build_turn_control_message` return value to the `TurnControl` contract | REQ-007 | File sets `engine.build_turn_control_message.return_value` (checked in Step 3) | — | Verified |
| tests/integration/test_replay_directive_across_restart.py | Create (new file) | Interrupted-to-reissued-to-completed integration test across a process restart: the directive is reconstructed from the persisted row and the reissued call reuses the original id | REQ-002, REQ-006 | The Issue's Testing Expectations require an integration test; `tests/integration/` exists and already crosses process boundaries over `tool_call_state` rows (checked in Step 3) | — | Verified |
| docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Modify | Document the Agent-managed replay in one place, next to the identifier definitions, per the Issue's Documentation Impact | REQ-002, REQ-005 | The identifier definitions are in this doc; the replay directive is not yet described (checked in Step 3) | — | Verified |
| docs/23_agent/agent_13_reference-api-generated.md | Modify | Regenerate the guarded `AUTO-GENERATED` block after the new `ReplayDirective` symbol under `scripts/agent/` | REQ-007 | `generate_reference_table.py --check` guards the `agent-class-function-reference` block, which lists `scripts/agent/tool_preparation.py` classes (checked in Step 3) | — | Verified |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Modify | Add `args_hash` to the `tool_call_state` column contract | REQ-006 | The doc's `tool_call_state` column contract lists the current columns without `args_hash` (checked in Step 3) | — | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", or "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/llm_turn_executor.py | Confirms the replay injection path carries the control text unchanged to `LLMTurnRunner`; no directive handling exists, so the file is not modified | REQ-005 |
| scripts/agent/conversation_state_manager.py | The Issue lists it as a target; Step 3 verified it has no replay or directive handling (turn-state only), so it is not affected | REQ-002 |
| scripts/agent/tool_audit.py | The audit `idempotency_key` field derives from the logical call id; a replayed call inherits the original id automatically, so no change is needed | REQ-002 |
| scripts/shared/transport_dto.py | `ToolExecutionContext.call_id` is the carrier the preparation phase attaches the original id to | REQ-002 |
| scripts/shared/mcp_dedup_claim.py | Dispatcher-side `interrupted`/`replay_completed` semantics (out of scope) bound which states the Agent-side directive may reconnect to | REQ-004 |
| tests/db/test_create_schema.py | Pins `tool_call_state` columns; asserts only `snapshot_id` absence, so adding `args_hash` does not break it | REQ-006 |
| tests/agent/test_repl_health.py | Generic missing-column shape-gate test; adding a column does not affect it | REQ-006 |
| tests/db/test_schema_validation_per_database.py | Plants the legacy `tool_call_state` shape to test rejection; unaffected by the new column | REQ-006 |
| docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md | Describes the control-message surfacing; its stale composed-key claim is owned by the mcpai012 final sweep, not this Plan | REQ-005 |

## Acceptance Criteria
- `AC-001` (REQ-002): An interrupted approved call, reissued by the LLM, reuses the original logical call id through Agent logic; the LLM never needs to emit or modify the id.
- `AC-002` (REQ-001, REQ-003): Ambiguous replay matching fails closed with a structured error; a directive cannot be used twice.
- `AC-003` (REQ-004): No directive exists for a non-retryable or outcome-unknown operation.
- `AC-004` (REQ-005): The replay control text contains no logical call id; it names tool name and canonical argument hash only.
- `AC-005` (REQ-006): After a process restart, the directive is reconstructed from the persisted `tool_call_state` row and the reissued call reconnects to the original id.
- `AC-006` (REQ-007): The full validation sequence in `rules/toolchain.md` passes, including diff-cover ≥ 90% on changed lines.

## Tests
- Interrupted-to-reissued-to-completed integration test across a restart (REQ-002, REQ-006, AC-005) — `tests/integration/test_replay_directive_across_restart.py`.
- Ambiguous replay rejection and one-time consumption (REQ-001, REQ-003, AC-002) — `tests/agent/test_tool_preparation.py`.
- No directive for non-retryable or outcome-unknown operations (REQ-004, AC-003) — `tests/agent/workflow/test_workflow_engine.py`.
- Control text contains no id (REQ-005, AC-004) — `tests/agent/workflow/test_workflow_engine.py`.
- Replayed call records the original id and `args_hash` in the state row (REQ-002, REQ-006, AC-001) — `tests/agent/test_tool_runner.py`.
- Run ruff, mypy, import-linter, and the full test suite (REQ-007, AC-006).

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task" (Agent spec scope), the Agent-managed replay is documented in one place next to the identifier definitions in the Agent tool-execution sub-document (`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`, target row), driven by REQ-002 and REQ-005. The `tool_call_state` column contract in the DB schema-reference sub-document (`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, target row) is driven by REQ-006. The guarded generated reference block (`docs/23_agent/agent_13_reference-api-generated.md`, target row) is regenerated for the new symbol, driven by REQ-007. The final MCP design-document sweep remains with mcpai012.

## Assumptions
- After the mcpdl001 id unification, the directive's `original id` and `original call id` are the same value (the logical call id is the row key); both fields are kept as the Issue states.
- `args_hash` is `NOT NULL` with no default and is populated by the write path in the same release unit (`rules/persisted-schema-change.md` item 4); the only writer of the table is `tool_call_state_ops.record_tool_call`.
- Directives are reconstructed at turn entry from persisted `interrupted` replayable rows; no new table or session-DB store is introduced (Design D1).
- The LLM control text may show tool name and canonical argument hash; the hash is not the id and is not editable identity.
- Single-author repository: every target file's top author holds >70% of 90-day commits, so `Bus Factor` is High throughout (git-fame not installed; computed from `git log --format='%an'`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Where replay directives are persisted so they survive restart (the Issue's `不明`) | None — resolved by repository evidence: `tool_call_state` rows already persist the id, task id, and tool; only the argument hash is missing | Resolved by Design decision D1: add the `args_hash` column and reconstruct directives from persisted rows; no separate directive store | False |
| UNK-02 | `tests/agent/test_workflow_engine_adapter.py` named by the review is not a tracked file (the Issue's `Needs confirmation`) | The file does not exist in the repository (checked in Step 1) | Adapter coverage is placed in the existing `tests/agent/workflow/test_adapter_guards.py` target row; no new adapter test file is added | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/schema_sql.py | Modify | Medium | 17 | High | not applicable (rsynced) |
| scripts/agent/workflow/tool_call_state_ops.py | Modify | Medium | 10 | High | not applicable (rsynced) |
| scripts/agent/workflow/state_store.py | Modify | Medium | 15 | High | not applicable (rsynced) |
| scripts/agent/context.py | Modify | High | 12 | High | not applicable (rsynced) |
| scripts/agent/tool_runner.py | Modify | Medium | 14 | High | not applicable (rsynced) |
| scripts/agent/tool_preparation.py | Modify | Medium | 3 | High | not applicable (rsynced) |
| scripts/agent/workflow/workflow_engine.py | Modify | Medium | 11 | High | not applicable (rsynced) |
| scripts/agent/workflow_engine_adapter.py | Modify | Medium | 12 | High | not applicable (rsynced) |
| tests/agent/test_tool_preparation.py | Modify | Low | 6 | High | not applicable (rsynced) |
| tests/agent/test_tool_runner.py | Modify | Medium | 18 | High | not applicable (rsynced) |
| tests/agent/workflow/test_workflow_engine.py | Modify | Medium | 13 | High | not applicable (rsynced) |
| tests/agent/workflow/test_workflow_state_store.py | Modify | Medium | 15 | High | not applicable (rsynced) |
| tests/agent/workflow/test_workflow_status_vocabulary.py | Modify | Low | 7 | High | not applicable (rsynced) |
| tests/agent/test_mcp_call_recovery.py | Modify | Low | 1 | High | not applicable (rsynced) |
| tests/agent/test_orchestrator.py | Modify | Medium | 25 | High | not applicable (rsynced) |
| tests/agent/workflow/test_no_workflow_bypass.py | Modify | Low | 1 | High | not applicable (rsynced) |
| tests/agent/workflow/test_adapter_guards.py | Modify | Low | 2 | High | not applicable (rsynced) |
| tests/integration/test_replay_directive_across_restart.py | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |
| docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Modify | Low | 8 | High | not applicable (rsynced) |
| docs/23_agent/agent_13_reference-api-generated.md | Modify | Low | 26 | High | not applicable (rsynced) |
| docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Modify | Low | 14 | High | not applicable (rsynced) |

## Design

### D1 — Directive persistence (data ownership)
Decision: no separate directive store. A `ReplayDirective` is reconstructed at turn entry from the persisted `tool_call_state` row, which already owns the original id, task id, tool name, and retry class; the missing field is the canonical argument hash, added as the `args_hash` column. One-time consumption is recorded durably by the row's state transition (`interrupted` → `dispatch_starting` on replay), so a restarted process sees no directive for an already-consumed row. In-process consumption is tracked by the directive's consumed flag for the current turn.
Alternatives: (a) a new `replay_directives` table in `workflow.sqlite` — rejected, it duplicates a row that already holds every field except the hash; (b) a store in `session.sqlite` via `ConversationStateManager` — rejected, tool-call lifecycle data is owned by `workflow.sqlite` per the `StateStore` responsibility boundary; (c) in-process-only directives documented as non-persistent — rejected against the Issue's Required Changes: after a restart, matching by tool name alone is ambiguous when several interrupted rows exist, violating the fail-closed constraint.
Compatibility impact: the shape gate compares databases against canonical DDL by exact fingerprint; existing databases with the old column set are refused and must be archived and recreated by the operator (current-schema-only policy, compatrm001; the migration framework is removed, so no migration step is registered).

### D2 — Engine contract (public API)
Decision: `build_turn_control_message` returns a `TurnControl` (control text plus directives) from the single `classify_stale_pending` call, because the classification transitions rows and cannot be called twice. The control text names tool name and `args_hash` only.
Alternatives: a second `build_replay_directives` method — rejected, the second call sees no source-state rows; engine-side cached state — rejected, hidden state is not a contract.
Consumer scan (`tools/scan_change_consumers.py --seed build_turn_control_message`, Step 3): adapter (target row); hand-written fake engines in `tests/agent/test_orchestrator.py` and `tests/agent/workflow/test_no_workflow_bypass.py` (target rows); `tests/agent/workflow/test_adapter_guards.py` mock return value (target row); `tests/agent/workflow/test_workflow_engine.py` assertions (target row); `tests/agent/workflow/test_adapter_store_ownership.py`, `tests/agent/workflow/test_session_diagnostics_wiring.py`, `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/integration/test_orchestrator_integration.py` — not affected: import only, do not call the method.
Consumer scan (`--seed PreparedToolCall`, Step 3): `scripts/agent/tool_approval.py`, `scripts/agent/tool_run_recorder.py`, `scripts/agent/repository_gateway.py` and their tests — not affected: `PreparedToolCall` gains no field; matching happens inside `_prepare_one` before the context is built.

### D3 — Directive holder during the turn
Decision: `TurnState.replay_directives` in `scripts/agent/context.py` is the Agent-controlled per-turn holder the Issue's constraint requires; the adapter registers the directives there at turn entry, and `_prepare_one` reads them through the `AgentContext` it already receives.
Alternatives: a parameter through `handle_llm_turn` — rejected, the executor carries LLM text only and the injection path would widen; `ConversationStateManager` — rejected per D1 data ownership. `scripts/agent/llm_turn_executor.py` and `scripts/agent/conversation_state_manager.py` are not affected (reference rows).

### Predictable fallout check (Step 3, `workflow-edge.md`)
- Module size: all target files are below the 24576 B gate (`wc -c` in Step 3); no split row.
- Pinned counts: `tests/db/test_create_schema.py` asserts only `snapshot_id` absence on `tool_call_state` columns — not affected; no test pins the column count.
- Tool inventory: no `tools/*.py` added or removed — not affected.
- Generated blocks: the guarded `agent-class-function-reference` block in `docs/23_agent/agent_13_reference-api-generated.md` drifts when `ReplayDirective` is added under `scripts/agent/` — recorded as a target row.

### Persisted schema check (`rules/persisted-schema-change.md`, Path B)
- Item 1 (version stores): not applicable — the migration framework and the workflow version row were removed (compatrm001); the shape gate is exact fingerprint matching against canonical DDL.
- Item 2 (fingerprint): applies — existing databases with the old shape fail the gate and are archived and recreated by the operator; no migration step is registered.
- Item 3 (rebuild/FK): not applicable — `tool_call_state` has no foreign keys; a plain column addition is not a rebuild.
- Item 4 (NOT NULL): applies — `args_hash` is `NOT NULL` without a default; the sole writer `record_tool_call` populates it in the same release unit.
- Item 5 (frozen migration text): not applicable — no registered steps exist.
- Item 6 (registry-pinning tests): not applicable — no registry exists.
- Item 7 (rows with an old meaning): not applicable at planning time — production data is not inspected; the recreation policy means no retained row carries an empty hash after deploy.

### Validation quality baseline (Step 5)
- `radon cc`: `tool_preparation._prepare_one` is C (16) and `build_turn_control_message` is C (16); the directive matching and `TurnControl` construction add branches to functions already at C rank — the implementation procedure must keep each new function at A/B rank by extracting the matching helper.
- `vulture --min-confidence 80`: no findings in any target file (checked in Step 5).
- `bandit -c pyproject.toml`: 48 Low, 0 Medium/High; the `-ll` gate passes (checked in Step 5).
- `diff-cover coverage.xml --compare-branch=master`: current baseline reports no lines with coverage information in the diff (clean tree at planning time); the Plan MUST raise it to ≥ 90% on changed lines per `rules/toolchain.md` Completion checklist.
- `lint-imports`: 6 contracts kept, 0 broken (checked in Step 5); the new `ReplayDirective` stays inside the `agent` layer, no boundary change.
- Operational dependency inspection: `ss -ltnp` shows no listener relevant to this change; `fuser` is not installed and the dev host has no `/opt/llm/workflow.sqlite`, so the DB lock check is recorded as not run. `pip-audit` not applicable: no dependency upgrade is planned.

## Implementation steps

1. **Phase 1: Persisted directive store (release unit A)**
   - [ ] Add the `args_hash` column to the `tool_call_state` canonical DDL (REQ-006; `scripts/db/schema_sql.py`)
   - [ ] Store `args_hash` in `record_tool_call`, extend `ToolCallState` and `_row_to_state`, add directive reconstruction from persisted `interrupted` replayable rows (REQ-001, REQ-006; `scripts/agent/workflow/tool_call_state_ops.py`)
   - [ ] Pass `args_hash` through `StateStore.record_tool_call` (REQ-006; `scripts/agent/workflow/state_store.py`)
   - [ ] Extend the `ToolCallRecorder` Protocol signature (REQ-006; `scripts/agent/context.py`)
   - [ ] Pass the prepared call's `args_hash` from its execution context at the recorder call site (REQ-006; `scripts/agent/tool_runner.py`)
   - [ ] Update the affected call sites and recorder fakes (REQ-007; `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_status_vocabulary.py`, `tests/agent/test_mcp_call_recovery.py`, `tests/agent/test_tool_runner.py`)
2. **Phase 2: ReplayDirective and preparation matching**
   - [ ] Add the `ReplayDirective` dataclass and the per-turn `replay_directives` field (REQ-001; `scripts/agent/tool_preparation.py`, `scripts/agent/context.py`)
   - [ ] Match a reissued call in `_prepare_one` by tool name plus canonical argument hash, attach the original id to the prepared call's context, consume once, fail closed on ambiguity with a structured error (REQ-002, REQ-003; `scripts/agent/tool_preparation.py`)
   - [ ] Add matching, one-time consumption, and ambiguity tests (REQ-001, REQ-002, REQ-003; `tests/agent/test_tool_preparation.py`)
3. **Phase 3: Engine contract and LLM-safe control text**
   - [ ] Change `build_turn_control_message` to return `TurnControl`; build directives only from `interrupted` rows with `retry_class` `retryable`; remove the id from the control text (REQ-004, REQ-005; `scripts/agent/workflow/workflow_engine.py`)
   - [ ] Consume `TurnControl` in `_run_execute_stage`: control text to the executor unchanged, directives registered on `ctx.turn.replay_directives` (REQ-002, REQ-005; `scripts/agent/workflow_engine_adapter.py`)
   - [ ] Update the control-message assertions and add directive-construction tests; update the fake-engine stubs and the mock return value (REQ-004, REQ-005, REQ-007; `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `tests/agent/workflow/test_no_workflow_bypass.py`, `tests/agent/workflow/test_adapter_guards.py`)
4. **Phase 4: Cross-restart integration test**
   - [ ] Interrupted-to-reissued-to-completed integration test across a process restart, asserting the reissued call reuses the original id and the consumed row is not re-listed (REQ-002, REQ-006; `tests/integration/test_replay_directive_across_restart.py`)
5. **Phase 5: Documentation and deployment**
   - [ ] Document the Agent-managed replay next to the identifier definitions; regenerate the guarded reference block; update the `tool_call_state` column contract (REQ-002, REQ-005, REQ-006, REQ-007; `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`, `docs/23_agent/agent_13_reference-api-generated.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`)
   - [ ] Hand off to `skills/deploy/SKILL.md`: the change is committed and pushed first, and deploying is the user's decision (approval gate); state the prerequisite that an existing deployed `workflow.sqlite` fails the shape gate and must be archived and recreated by the operator per the DB recreation procedure (REQ-006)

### Release units
**Unit**: persisted directive store | **Phases**: 1 | **Reason**: the `args_hash` column and its write path (Protocol, `StateStore`, `tool_call_state_ops`, the `tool_runner` call site) land in one commit; a `NOT NULL` column without a default breaks every existing `INSERT` until the writer populates it, so the members cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/schema_sql.py | Unit (shape gate) | `uv run pytest tests/db/test_create_schema.py` | Fresh scratch database carries `args_hash`; existing-shape databases are refused |
| scripts/agent/workflow/tool_call_state_ops.py | Unit | `uv run pytest tests/agent/workflow/test_workflow_state_store.py` | Recorded rows carry the hash; reconstruction returns directives only for `interrupted` replayable rows |
| scripts/agent/workflow/state_store.py | Unit | `uv run pytest tests/agent/workflow/test_workflow_state_store.py` | Pass-through populates the column |
| scripts/agent/context.py | Unit | `uv run pytest tests/agent/test_tool_runner.py` | Recorder fake satisfies the Protocol; `TurnState` carries directives per turn |
| scripts/agent/tool_runner.py | Unit | `uv run pytest tests/agent/test_tool_runner.py` | Replayed call records the original id and hash (AC-001) |
| scripts/agent/tool_preparation.py | Unit | `uv run pytest tests/agent/test_tool_preparation.py` | Match, one-time consumption, ambiguous-match structured error (AC-002) |
| scripts/agent/workflow/workflow_engine.py | Unit | `uv run pytest tests/agent/workflow/test_workflow_engine.py` | Control text has no id (AC-004); no directive for non-retryable/outcome-unknown (AC-003) |
| scripts/agent/workflow_engine_adapter.py | Unit | `uv run pytest tests/agent/workflow/test_adapter_guards.py` | `TurnControl` consumed; directives registered on `ctx.turn` |
| tests/integration/test_replay_directive_across_restart.py | Integration | `uv run pytest tests/integration/test_replay_directive_across_restart.py -m integration` | Interrupted-to-reissued-to-completed across restart (AC-005) |
| Full suite / gates | — | `uv run ruff check scripts/`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `PYTHONPATH=scripts uv run lint-imports`; `uv run pytest`; `uv run diff-cover coverage.xml --compare-branch=master`; `uv run pre-commit run --all-files` | All pass; diff-cover ≥ 90% on changed lines (AC-006) |
| Generated reference block | Gate | `uv run python tools/generate_reference_table.py --check` | No drift after `ReplayDirective` is added |
| DB separation | Gate | `uv run python tools/check_db_separation.py` | `tool_call_state` ownership unchanged |

## Risks
- **Risk**: Existing deployed `workflow.sqlite` databases fail the exact shape gate after the `args_hash` column is added → **Mitigation**: the current-schema-only policy documents archive-and-recreate by the operator; the Phase 5 deploy step names the prerequisite and the user decides deployment (approval gate).
- **Risk**: High-churn targets (`tests/agent/test_orchestrator.py` 25, `docs/23_agent/agent_13_reference-api-generated.md` 26, `tests/agent/test_tool_runner.py` 18, `scripts/db/schema_sql.py` 17 commits in 30 days) may drift against concurrent work → **Mitigation**: run `tools/check_plan_target_overlaps.py` at freeze (done in Step 8b); keep every change in one change set per REQ-007.
- **Risk**: Fail-closed on ambiguity rejects a legitimate reissue when two persisted `interrupted` rows share tool name and argument hash → **Mitigation**: intended behavior per the Issue's constraint; the structured error lists the matching rows so the operator can see the ambiguity.
- **Risk**: Directive matching depends on byte-identical canonical argument hashes between the original call and the reissued call; a reissue with edited arguments gets no directive and proceeds as a new call → **Mitigation**: the control text instructs identical arguments, and the hash is computed by the same `_canonical_args_hash` used at recording; a test asserts hash equality for a byte-identical reissue.
- **Risk**: A single-author repository gives every target file a High bus factor → **Mitigation**: the frozen test rows lock the behavior; the cross-restart integration test covers the persistence assumption independently of the unit fakes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: persisted directive store (schema column + write path + affected call sites) | In Progress | — | — | Release unit A |
| 2 | Phase 2: ReplayDirective type, preparation matching, one-time consumption, fail-closed | In Progress | — | — |  |
| 3 | Phase 3: engine `TurnControl` contract, LLM-safe control text, adapter carry, stub updates | In Progress | — | — |  |
| 4 | Phase 4: cross-restart integration test | In Progress | — | — |  |
| 5 | Phase 5: documentation, generated block, deploy hand-off | In Progress | — | — | Deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261125-112546_01_scripts_db_schema_sql.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261125-112546_02_scripts_agent_workflow_tool_call_state_ops.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261125-112546_03_scripts_agent_workflow_state_store.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261125-112546_04_scripts_agent_context.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261125-112546_05_scripts_agent_tool_runner.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261125-112546_06_scripts_agent_tool_preparation.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261125-112546_07_scripts_agent_workflow_workflow_engine.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261125-112546_08_scripts_agent_workflow_engine_adapter.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261125-112546_09_tests_agent_test_tool_preparation.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261125-112546_10_tests_agent_test_tool_runner.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261125-112546_11_tests_agent_workflow_test_workflow_engine.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261125-112546_12_tests_agent_workflow_test_workflow_state_store.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261125-112546_13_tests_agent_workflow_test_workflow_status_vocabulary.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261125-112546_14_tests_agent_test_mcp_call_recovery.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261125-112546_15_tests_agent_test_orchestrator.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261125-112546_16_tests_agent_workflow_test_no_workflow_bypass.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261125-112546_17_tests_agent_workflow_test_adapter_guards.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261125-112546_18_tests_integration_test_replay_directive_across_restart.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261125-112546_19_docs_23_agent_agent_06_01_tool-execution-and-approval-execution.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261125-112546_20_docs_23_agent_agent_13_reference-api-generated.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261125-112546_21_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md` | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-105505
- **Related target files**: `scripts/db/schema_sql.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/context.py`, `scripts/agent/tool_runner.py`, `scripts/agent/tool_preparation.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/test_tool_preparation.py`, `tests/agent/test_tool_runner.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_status_vocabulary.py`, `tests/agent/test_mcp_call_recovery.py`, `tests/agent/test_orchestrator.py`, `tests/agent/workflow/test_no_workflow_bypass.py`, `tests/agent/workflow/test_adapter_guards.py`, `tests/integration/test_replay_directive_across_restart.py`, `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`, `docs/23_agent/agent_13_reference-api-generated.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes | scripts/agent/tool_preparation.py | Phase 2 | AC-002 | Ambiguous replay rejection and one-time consumption test | Explicit in issue |
| REQ-001 | Required Changes | scripts/agent/workflow/tool_call_state_ops.py | Phase 1 | AC-005 | Directive reconstruction unit test | Confirmed by repository evidence |
| REQ-001 | Required Changes | scripts/agent/context.py | Phase 2 | AC-002 | TurnState field test | Confirmed by repository evidence |
| REQ-002 | Required Changes | scripts/agent/tool_preparation.py | Phase 2 | AC-001 | Directive matching test | Explicit in issue |
| REQ-002 | Required Changes | scripts/agent/workflow/workflow_engine.py | Phase 3 | AC-001 | Directive-construction test | Confirmed by repository evidence |
| REQ-002 | Required Changes | scripts/agent/workflow_engine_adapter.py | Phase 3 | AC-001 | Adapter carry test | Confirmed by repository evidence |
| REQ-002 | Required Changes | scripts/agent/context.py | Phase 2 | AC-001 | TurnState field test | Confirmed by repository evidence |
| REQ-002 | Required Changes | tests/agent/test_tool_preparation.py | Phase 2 | AC-001 | Directive matching test | Explicit in issue |
| REQ-002 | Required Changes | tests/agent/test_tool_runner.py | Phase 1 | AC-001 | Replayed-call state-row test | Explicit in issue |
| REQ-002 | Required Changes | tests/integration/test_replay_directive_across_restart.py | Phase 4 | AC-001 | Interrupted-to-reissued-to-completed integration test | Explicit in issue |
| REQ-002 | Documentation Impact | docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Phase 5 | N/A: documentation criterion | Documentation review | Explicit in issue |
| REQ-003 | Required Changes | scripts/agent/tool_preparation.py | Phase 2 | AC-002 | Ambiguous replay rejection test | Explicit in issue |
| REQ-003 | Required Changes | tests/agent/test_tool_preparation.py | Phase 2 | AC-002 | Ambiguous replay rejection test | Explicit in issue |
| REQ-004 | Required Changes | scripts/agent/workflow/workflow_engine.py | Phase 3 | AC-003 | No-directive-for-non-retryable test | Confirmed by repository evidence |
| REQ-004 | Required Changes | tests/agent/workflow/test_workflow_engine.py | Phase 3 | AC-003 | No-directive-for-non-retryable test | Explicit in issue |
| REQ-005 | Problem (control text shows the id) | scripts/agent/workflow/workflow_engine.py | Phase 3 | AC-004 | Control-text test | Confirmed by repository evidence |
| REQ-005 | Problem (control text shows the id) | scripts/agent/workflow_engine_adapter.py | Phase 3 | AC-004 | Adapter carry test | Confirmed by repository evidence |
| REQ-005 | Problem (control text shows the id) | tests/agent/workflow/test_workflow_engine.py | Phase 3 | AC-004 | Control-text test | Confirmed by repository evidence |
| REQ-005 | Documentation Impact | docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md | Phase 5 | N/A: documentation criterion | Documentation review | Explicit in issue |
| REQ-006 | Required Changes | scripts/db/schema_sql.py | Phase 1 | AC-005 | Shape-gate test | Confirmed by repository evidence |
| REQ-006 | Required Changes | scripts/agent/workflow/tool_call_state_ops.py | Phase 1 | AC-005 | Reconstruction unit test | Confirmed by repository evidence |
| REQ-006 | Required Changes | scripts/agent/workflow/state_store.py | Phase 1 | AC-005 | Pass-through unit test | Confirmed by repository evidence |
| REQ-006 | Required Changes | scripts/agent/context.py | Phase 1 | AC-005 | Recorder fake test | Confirmed by repository evidence |
| REQ-006 | Required Changes | scripts/agent/tool_runner.py | Phase 1 | AC-005 | Replayed-call state-row test | Confirmed by repository evidence |
| REQ-006 | Required Changes | tests/integration/test_replay_directive_across_restart.py | Phase 4 | AC-005 | Cross-restart integration test | Explicit in issue |
| REQ-006 | Documentation Impact | docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md | Phase 5 | N/A: documentation criterion | Documentation review | Explicit in issue |
| REQ-007 | Constraints | tests/agent/workflow/test_workflow_state_store.py | Phase 1 | AC-006 | Call-site update | Confirmed by repository evidence |
| REQ-007 | Constraints | tests/agent/workflow/test_workflow_status_vocabulary.py | Phase 1 | AC-006 | Call-site update | Confirmed by repository evidence |
| REQ-007 | Constraints | tests/agent/test_mcp_call_recovery.py | Phase 1 | AC-006 | Fake signature update | Confirmed by repository evidence |
| REQ-007 | Constraints | tests/agent/test_orchestrator.py | Phase 3 | AC-006 | Fake engine stub update | Confirmed by repository evidence |
| REQ-007 | Constraints | tests/agent/workflow/test_no_workflow_bypass.py | Phase 3 | AC-006 | Fake engine stub update | Confirmed by repository evidence |
| REQ-007 | Constraints | tests/agent/workflow/test_adapter_guards.py | Phase 3 | AC-006 | Mock return-value update | Confirmed by repository evidence |
| REQ-007 | Constraints | docs/23_agent/agent_13_reference-api-generated.md | Phase 5 | AC-006 | `generate_reference_table.py --check` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261125-112546 -->