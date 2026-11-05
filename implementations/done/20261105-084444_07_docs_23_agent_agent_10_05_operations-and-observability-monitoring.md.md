## Goal

Remove the deleted handler name from the diagnostic-kinds table so the reference
points at the live runner path.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The `partial_completion` kind row's `Source` column currently names
  `handle_partial_completion`, the function in the module being deleted.
- The live handler is `LLMTurnRunner._handle_llm_error` in
  `scripts/agent/llm_turn_runner.py`.

## Design decisions

- Point the `Source` column at the runner method that actually persists the diagnostic.

## Alternatives considered

- Leaving the stale name: rejected; it references deleted code.

## Implementation
### Target file
`docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`

### Procedure

- In the diagnostic-kinds table, change the `Source` of the `partial_completion`
  kind row (currently `handle_partial_completion`) to
  `scripts/agent/llm_turn_runner.py::_handle_llm_error`.

### Method

- Single-cell edit in the `| Kind | Source | Content |` table; leave the
  `llm_transport_error` kind row (`Source`: Session Management) unchanged.

### Details

- The runner persists the diagnostic via `ctx.diagnostics.save(...)` inside
  `_handle_llm_error`; that is the correct source for the kind.

## Compatibility considerations

- N/A: documentation-only correction.

## Security considerations

- N/A: documentation-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Run the applicable `tools/check_docs_*` checkers named in `routing.md`.

## Completion criteria

- The `partial_completion` kind row cites the runner path; no deleted-handler name remains.

## Out of Scope

- Any change to the diagnostic content or the monitoring prose.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-05T15:30 | 2026-11-05 | Step 3b verification clean (stale_detector: not stale). L70 partial_completion Source cell updated to scripts/agent/llm_turn_runner.py::_handle_llm_error; llm_transport_error row unchanged. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-05 | 2026-11-05 | quality/structure/japanese clean; consistency WARNING on agent_13_reference-api-generated.md:102 attributed to procedure 08 and cleared by its regeneration. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-084444_07_docs_23_agent_agent_10_05_operations-and-observability-monitoring.md.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 — correct the stale handler name in the monitoring reference
- **Source issue**: issues/20261031-180511_partialcount001_partial-completion-counter-dead.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115736_partialcount001_partial-completion-counter-dead.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-084444
- **Related target files**: docs/23_agent/agent_10_05_operations-and-observability-monitoring.md
