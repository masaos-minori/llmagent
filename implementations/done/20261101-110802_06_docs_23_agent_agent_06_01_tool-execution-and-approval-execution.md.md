## Goal

Document the new `tool_call_state` producer behavior in
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`: every dispatched tool
call now writes a `tool_call_state` row (`pending` before dispatch, `completed`/`failed`
after), keyed identically to the transport dedup key, so the merged consumer
(`build_turn_control_message`) can surface stale calls.

## Scope

- Add one subsection under `## Design Intent` describing the state-recording step in the
  execution flow.
- Extend `## Key Constraints` with the key-parity constraint (producer key == transport key)
  and the non-fatal-recording constraint.
- Nothing else in the doc changes; no other doc files are in scope (per
  `docs/00_index.md` task-scope mapping, "Agent REPL flow / tool execution" maps to this
  file plus `agent_03_01_turn-processing-flow-overview.md`; only this file is in the plan's
  frozen target list).

## Assumptions

- The plan's docs update row (REQ-011) is the only documentation edit for this
  plan; workflow-side docs (state_store/tool_call_state_ops) already describe the consumer
  and helpers from the merged toolexec001 work.

## Design decisions

- Describe behavior (what rows appear when, key derivation source, crash semantics) rather
  than implementation internals (helper names, line numbers), matching the doc's existing
  style of responsibility-level prose.
- Single new `### Tool Call State Recording` subsection under Design Intent instead of
  touching the DAG/execution prose: recording is an orthogonal concern layered on
  `_recorded_call`, and the DAG section's frozen decisions (Risk 1) must not be blurred.

## Alternatives considered

- New standalone doc file for tool-call state: rejected — the feature is a behavior layer on
  the existing execution flow described by this exact doc, and the plan's frozen target list
  names this file.
- Editing `agent_03_01_turn-processing-flow-overview.md` too: rejected — not in the frozen
  target list; scope stays at the plan boundary.

## Implementation
### Target file

`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure

1. Add `### Tool Call State Recording` after `### Result Reflection in History` (L70-75):
   - every dispatched call records a `tool_call_state` row in state `pending` before the
     executor runs and is finalized to `completed`/`failed` after; a cancelled/aborted call
     (BaseException) leaves the row `pending`;
   - the key is `shared.http_transport.derive_idempotency_key("call_tool", name, args,
     session_uid)` — identical to the transport-layer dedup key;
   - `retry_class` comes from `shared.mcp_dedup.retry_class` (`config/mcp_dedup.toml`);
   - recording failures are logged and never break tool execution;
   - the recorder is injected by `WorkflowEngineAdapter` per turn via
     `AgentContext.workflow.tool_call_recorder`;
   - interrupted-class transition and replay consumption are owned by the workflow side
     (`classify_stale_pending`, `build_turn_control_message`), cross-referencing the
     toolexec001 plan doc.
2. Add to `## Key Constraints` (L87-92): the key-parity bullet and the
   recording-is-non-fatal bullet.
3. Add `tool_call_state`, `idempotency_key`, `retry_class` to `## Keywords` (L99).

### Method

Additive edits to three existing sections; no reordering of existing content.

### Details

- Write in English per `skills/DESIGN.md` output-language rule.
- Keep claims verifiable against the merged consumer (`workflow_engine.py` L110-128) and the
  helpers (`tool_call_state_ops.py` docstrings); do not describe the replay-consumer work
  (Phase 3) as landed.

## Compatibility considerations

- `docs/00_index.md` needs no change: the file is already registered in the index and the
  task-scope mapping is unchanged.
- No doc checker IDs to register for prose-only edits; run the docs checker per
  `routing.md` "When to run which tool" before finishing.

## Security considerations

- N/A: documentation only; the doc must not quote real salts or session ids (it names the
  function, not values).

## Rollback considerations

- Revert the file (`git checkout -- docs/...`); independent of code rows.

## Validation plan

- Docs checker(s) per `routing.md` Tools → "When to run which tool"
  (`tools/check_docs_structure.py` or the applicable docs checker).
- Manual claim audit: every behavior statement cross-checked against the merged consumer
  code and the row 01 procedure after implementation.

## Completion criteria

- New subsection and constraint bullets present, English, ≤ the doc's per-section concision
  style.
- Docs checker passes.

## Out of Scope

- Other `23_agent` docs (including `agent_03_01_turn-processing-flow-overview.md` — not in
  the plan's frozen target list).
- Workflow-side state_store/tool_call_state_ops documentation (already merged with
  toolexec001).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261101-125601 | 20261101-125601 | 3 additive edits: Tool Call State Recording subsection, 2 Key Constraints bullets, 3 Keywords; consumer cross-ref to db_03_07 |
| 2 | Add or update tests per Validation plan | Completed | 20261101-125601 | 20261101-125601 | N/A: docs-only row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261101-125601 | 20261101-125601 | check_docs_quality/structure/content_policy/consistency --domain agent all clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261101-125601 | 20261101-125601 | N/A: this row is the docs row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-011
- **Source issue**: issues/done/20261031-175803_toolstate001_tool-call-state-producer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-105136_toolstate001_tool-call-state-producer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-110802
- **Related target files**: docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md