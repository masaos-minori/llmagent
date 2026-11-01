# Implementation Procedure: tests/agent/workflow/test_workflow_engine.py

## Goal

Regression for turn-entry pending-call detection and replay-as-new-turn control
injection (row 08): the engine finds interrupted pending tool calls via the row 07
helpers, re-executes retryable ones, surfaces unreplayable ones, and hands the
control message to the runner (REQ-008), test-first for rows 07-08.

## Scope

**In scope:**
- `tests/agent/workflow/test_workflow_engine.py`: new integration cases.

**Out of scope:**
- Control-message injection into the LLM context (row 09, tested by row 21); store
  unit behavior (row 17); state_store helper unit tests (row 07's own row doc).

## Assumptions

- Anchor finding (re-verified 2026-10-31): the earlier claim of `TestRetryClassification:118`,
  `TestExecutionRouting:153`, `test_terminal_state_wins:181`,
  `test_terminal_state_is_idempotent_on_replay:198` is stale draft residue — those names do not
  exist anywhere in `tests/`. The actual characterization set to keep byte-identical is the
  file's existing classes: `TestWorkflowEngineHappyPath:87`, `TestWorkflowEngineRetry:109`,
  `TestWorkflowEngineTimeout:161`, `TestWorkflowEngineIdempotency:184`
  (`test_skip_already_processed_stage:186`), `TestWorkflowEngineStages:206`,
  `TestRunStageWithRetryGeneralization:231` (REQ-010 stage-retry semantics unchanged).
- The engine's stage hooks live in `agent/workflow/idempotency_ops.py`
  (`begin_stage_if_new:18`, `is_event_processed:12`, verified HEAD); new pending
  detection is a separate axis (tool-call state rows, not stage events) per row 08.
- Fixtures write `tool_call_state` (new) rows directly through the row 07 helpers (not raw
  SQL) so the test also pins the helper API; tmp workflow DB via the existing
  fixture pattern in this file.
- Red state: new cases fail until rows 06-08 land; row 06 is gated on dbmig001
  rows 01-02, so this doc inherits that gate.

## Design decisions

- `TestPendingDetection` (new): seed pending rows (retryable vs non_retryable via
  `retry_class` (new)) + completed rows; assert turn-entry classification: re-execute set,
  replay-stored set, unreplayable set.
- `TestReplayAsNewTurn` (new): retryable interrupted call → engine re-enters execution with
  a control message object (the value later injected by row 09); assert the message
  names the tool and idempotency key (shape per row 08 design decisions) but do not
  assert LLM-side rendering (row 21 owns that).
- `TestUnreplayableSurfaced` (new): non_retryable interrupted → surfaced as a failure
  diagnostic, no silent re-execution (REQ-008 AC wording).
- Snapshot equality influence comes from `execution_snapshots` (new) rows (row 06 tables):
  one case with matching snapshot (replay allowed) and one with mismatch
  (choice changes, execution not blocked — plan Risks wording pinned at engine
  level).

## Alternatives considered

- Testing through the full AgentREPL — rejected: turn wiring is row 09/21's surface;
  engine-level integration with mocked transport keeps the failure attributable.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
1. New classes `TestPendingDetection` (new), `TestReplayAsNewTurn` (new),
   `TestUnreplayableSurfaced` (new), `TestSnapshotInfluence` (new) appended at end of file.
2. Fixture helper: seed `tool_call_state` (new) + `execution_snapshots` (new) rows via row 07
   helpers.

### Method
Test-first: red until rows 06-08 land (row 06 gated on dbmig001 — inherited gate).

### Details
- Existing classes `:87-319` (per the corrected Assumptions anchor list) untouched.

## Compatibility considerations

- Stage idempotency tests (`:181,:198`) must stay green: the new tool-call-state
  axis must not change `processed_events` behavior (REQ-010 orthogonality).

## Security considerations

- N/A: synthetic tool names/keys.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py` (new classes red
  before rows 06-08, green after; existing green throughout);
  `uv run mypy --no-namespace-packages tests/agent`; `uv run lint-imports`.

## Completion criteria

- Pending detection, replay-as-new-turn, unreplayable surfacing, and snapshot-
  influence semantics proven at engine level with rows 06-08 landed.

## Out of Scope

- LLM turn context injection (row 21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add four new test classes + seed helpers | Completed | 2026-10-31 (row 08 cycle) | 2026-10-31 | Deviation recorded: the landed design (row 08, owner-approved Notes) makes the engine build a control message from the rows its `classify_stale_pending` call just transitioned; it does not itself re-execute anything. The four proposed classes were therefore consolidated into one `TestBuildTurnControlMessage` (6 cases): retryable-interrupted -> replay section (= pending detection + replay-as-new-turn message naming tool + key), non_retryable -> unreplayable section surfaced (not replayed), no rows -> None, fresh pending never listed, transitioned rows consumed once, store failure -> None (no raise). The snapshot-equality axis is pinned at the dispatcher integration level instead (`tests/mcp_servers/test_mcp_dispatch.py::TestDurableDedup` snapshot-mismatch case), because the implemented engine path does not read `execution_snapshots`; re-execution itself awaits the producer follow-up issue `issues/20261031-175803_toolstate001_tool-call-state-producer.md`. Existing classes untouched and green. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-31 | 2026-10-31 | `pytest tests/agent/workflow/test_workflow_engine.py` 18 passed; `mypy --no-namespace-packages` clean (via `MYPYPATH=scripts`); `lint-imports` 6 kept in the batch gate run; whole-suite run covers this file. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Row 06 gated on dbmig001 rows 01-02 implementation | Yes | 2026-10-31 (dbmig001 plan fully Completed) |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-008` (interrupted calls replay as a new turn), `REQ-010`
  (existing stage-retry semantics preserved)
- **Source issue**: `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-102825
- **Related target files**: tests/agent/workflow/test_workflow_engine.py
