# Implementation Procedure: scripts/agent/workflow/workflow_engine.py

## Goal

At task-turn entry, detect pending tool-call state for the task and inject the replay
control message so the LLM re-issues interrupted calls under the same key; surface
non-retryable pending calls as an unreplayable status message instead (REQ-008 replay as
a new turn).

## Scope

**In scope:**
- `scripts/agent/workflow/workflow_engine.py`: pending detection in the turn path reached
  from `run` (`async def run(` at `:108`) and control-message construction handed to the
  turn runner.

**Out of scope:**
- Propagation into the LLM context (row 09), helpers (row 07).

## Assumptions

- Ownership rule holds: retry/idempotency decisions belong to the workflow engine
  (`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` `:150`, `:277` per the
  plan's Reference Files) — the engine decides replay; the turn runner only carries the
  message.
- `retry_class` (new) per row is read from the `tool_call_state` (new) row itself (written at record
  time per rows 06-07), so the engine does not load `config/mcp_dedup.toml` directly.
- Wiring finding (verified 2026-10-31): `WorkflowEngine.run` (`:108` confirmed) is a stage
  callback engine — it never imports or calls `LLMTurnRunner`. The shipped turn chain is
  orchestrator → `agent/workflow_engine_adapter.py` (`orchestrator.py:145-148`) → engine
  stage callbacks → `agent/llm_turn_executor.py` (`handle_llm_turn`, instantiates
  `LLMTurnRunner` at `:84`) → `LLMTurnRunner.run`. Passing the control message from the
  engine to the runner therefore crosses `workflow_engine_adapter.py` and
  `llm_turn_executor.py`, neither of which is in the frozen target table. Owner decision
  2026-10-31: `agent/llm_turn_executor.py` (and `agent/workflow_engine_adapter.py` only
  if the callback contract proves insufficient) are approved additional targets of the
  row 08 cycle for the message hand-off.

## Design decisions

- Before each turn dispatch for a task: `state_store.classify_stale_pending(task_id,
  timeout)` then `pending_tool_calls(task_id)`.
- Control message (constructed here, passed per row 09's contract): one message per task
  listing replayable calls — `tool`, `idempotency_key`, `state="interrupted"` — with the
  instruction to re-issue each call unchanged; a separate unreplayable section lists
  `retry_class="non_retryable"` interrupted rows with the dispatcher's
  `dedup_unreplayable` (new) semantics (row 04) so the LLM reports rather than re-issues
  (REQ-005 refuse path, REQ-008).
- No pending rows → no message (byte-identical turn behavior, REQ-010).

## Alternatives considered

- Replaying calls automatically without an LLM turn — rejected: REQ-008 fixes
  "replay as a new turn" so the LLM observes the outcome; also keeps ADR-014 loop
  ownership intact (see also `plans/done/20261030-001153_turnadr001_*` sequencing).
- Detecting pending state from `mcp_dedup.sqlite` — rejected per row 07's DB-separation
  rationale.

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
1. In the turn-entry path under `run` (`:108`), before invoking the turn runner, run the
   detection sequence from Design decisions.
2. Build the control message text and pass it to `LLMTurnRunner.run` via the new
   keyword documented in row 09.
3. Finalization: after the turn returns, finalize `tool_call_state` (new) rows the turn
   completed (the same-keys re-issued calls complete through the dispatcher path; the
   engine marks task-level closure consistent with existing attempt finalization).

### Method
No new imports above the workflow layer's existing contract (state_store is same-package).

### Details
- Detection must not raise into the turn path: on store errors, log and proceed with no
  control message (turn availability beats replay accuracy; the dispatcher's own dedup
  still guards execution).

## Compatibility considerations

- Tasks without tool-call state rows behave exactly as today; existing
  `test_workflow_engine.py` cases stay byte-identical (row 20 only adds cases).

## Security considerations

- Control message embeds only tool names + keys (hashes), never stored results; the LLM
  cannot forge replay for a different key/content — the dispatcher re-validates
  `args_hash` per row 04.

## Rollback considerations

- Revert the commit: rows 06-07 tables go dormant; turns resume message-free.

## Validation plan

- Row 20 (`tests/agent/workflow/test_workflow_engine.py`, test-first): pending + retryable
  → control message with same key present in the runner call; pending + non_retryable →
  unreplayable status message, no replay instruction; no pending → no kwarg passed;
  stale-pending classified interrupted once.
- `uv run pytest tests/agent/workflow/test_workflow_engine.py`; `uv run mypy
  --no-namespace-packages scripts/ tests/agent`; `lint-imports`.

## Completion criteria

- A task left with an interrupted pending call produces a next-turn control message that
  re-issues the identical call (plan Phase 6 kill-mid-call staging check: replay observed
  in the next turn); non-retryable pending rows surface as status text, never as replay.

## Out of Scope

- LLM-context injection mechanics (row 09); dispatcher refusal (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement detection + control-message construction | Completed | 20261031-173000 | 20261031-175803 | `WorkflowEngine.build_turn_control_message(task_id)`: classify stale pending (timeout from `shared.mcp_dedup.load_dedup_config().pending_timeout_minutes` — the loader, not the TOML directly), then list the interrupted rows it transitioned: retryable -> re-issue instruction, non-retryable -> unreplayable manual-action text (`dedup_unreplayable` semantics, row 04). Store/config errors log and return None (turn path never raises). Fresh pending rows (inside the timeout window) are not listed — re-issuing them risks duplicating live work, and once-consumption is preserved because already-interrupted rows are never re-listed. Call site: `workflow_engine_adapter._run_execute_stage` (the parameterless `StageCallback` contract proved insufficient, so the two owner-approved additional targets `workflow_engine_adapter.py` and `llm_turn_executor.py` carry the message to `LLMTurnRunner.run`) |
| 2 | Land row 20 tests (test-first) | Completed | 20261031-173000 | 20261031-175803 | 6 cases in `tests/agent/workflow/test_workflow_engine.py` (`TestBuildTurnControlMessage`, real temp DB): retryable replay section, non-retryable unreplayable section, no-rows None, fresh-pending not listed, consumed-once, store-failure returns None. Step 3 finalization (post-turn row finalization) is inert by design until the producer lands (see Blocker Log) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261031-173000 | 20261031-182400 | Batched with rows 07/09: gates fast all Pass, lint-imports 6 kept, ruff clean, mypy green, bandit at the 3-medium master baseline. Batch full suite (post orchestrator-test fix): 10744 passed / 8 skipped / 0 failed in 7m17s; `diff-cover --compare-branch=master --fail-under=90`: 92% (429 changed lines, 33 missing, all in `scripts/shared/mcp_dedup.py` defensive branches) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on rows 06-07 (gated on dbmig001 rows 01-02) | Yes | 2026-10-31 (dbmig001 plan fully Completed; rows 06-07 execute before row 08 in this batch) |
| 1 | No producer records pending rows yet (write-trigger gap, row 07 Blocker Log). Owner decision 2026-10-31 (option B): mechanism lands inert; detection returns None in production until the follow-up producer (`issues/20261031-175803_toolstate001_tool-call-state-producer.md`) lands. Completion criteria that depend on a live interrupted row (kill-mid-call staging check) move to that follow-up | Yes | 2026-10-31 |
| 2 | `tests/agent/test_orchestrator.py` stand-in engine `_RetryThenHaltEngine` (out-of-table characterization test) lacked `build_turn_control_message`, so the new adapter call raised inside every execute attempt (1 full-suite failure). Fixed by mirroring the new engine contract on the stand-in (returns None) | Yes | 2026-10-31 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (interrupted calls replay as a new turn)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: scripts/agent/workflow/workflow_engine.py; owner-approved additional targets: scripts/agent/workflow_engine_adapter.py, scripts/agent/llm_turn_executor.py
