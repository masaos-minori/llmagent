## Goal

Correct the shutdown-order statement in the runtime architecture document so it describes the settle-first sequence and the budget-derived turn window instead of the checkpoint-first order (REQ-001: one owner and sequence; REQ-012: every step reported).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: the Shutdown subsection of Key Constraints in this document.
- Out of scope: the coordinator (row 5), the input loop (row 8), and the operations runbook wording (row 45).

## Assumptions

- `docs/23_agent/agent_02_runtime-architecture.md:159` states that a signal sets the `shutdown_requested` flag and the shared shutdown event, and that the wait for a cancelled turn is bounded by `_GRACEFUL_TIMEOUT_S`.
- `docs/23_agent/agent_02_runtime-architecture.md:161` explains that the bound keeps a slow turn from hanging the loop rather than exiting the process directly.
- `docs/23_agent/agent_02_runtime-architecture.md:163` states "Resource closing occurs after WAL checkpointing, and both calls are independent and protected", which is the order this Plan reverses.
- The independence claim in the same sentence stays true: the Plan keeps every step guarded.

## Design decisions

- Rewrite the order sentence rather than annotate it: the architecture document is the canonical place the shutdown order is stated, and a stale order there is what a later reader would implement again.
- State the window as the remaining time of the armed budget, with `_GRACEFUL_TIMEOUT_S` described as the value drawn from it (row 8), so the document does not imply two clocks.
- Keep the "independent and protected" property and add that each step records an outcome, because the Plan changes the order, not the isolation.
- Compatibility impact: documentation only.

## Alternatives considered

- Add a note that the order changed while keeping the original sentence — rejected: the document would then assert two opposite orders in adjacent sentences.

## Implementation
### Target file
`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure
1. Update `docs/23_agent/agent_02_runtime-architecture.md:159` so the bounded wait for a cancelled turn is the remaining time of the armed shutdown budget, and `_GRACEFUL_TIMEOUT_S` is described as the window drawn from it.
2. Replace the order sentence at `docs/23_agent/agent_02_runtime-architecture.md:163`: writers are settled and the write gate is closed first, then the session snapshot is persisted, then the WAL checkpoint and backup run, then resources are closed.
3. Keep the independence statement and add that each step records one outcome in the shutdown report.

### Method

- Sentence-level replacement inside the existing Shutdown subsection; no new heading.

### Details

- The wording names the steps in the order the report prints them, which is the same order row 45 documents.

## Compatibility considerations

- Runs after rows 5, 7, 8 and 9: the order it states is the order those rows install.
- `docs/00_index.md` maps `HttpServerLifecycleManager` / `http_lifecycle.py` claims to this file as well as to row 50's document, so the two must state the same termination bound.

## Security considerations

- N/A: no path, command, or configuration value is quoted.

## Rollback considerations

- Revert this row's commit with the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/23_agent/agent_02_runtime-architecture.md` | Docs | `uv run python tools/check_docs_quality.py` | No finding |
| `docs/23_agent/agent_02_runtime-architecture.md` | Docs | `uv run python tools/check_docs_structure.py docs/23_agent/agent_02_runtime-architecture.md` | No finding |
| `docs/23_agent/agent_02_runtime-architecture.md` | Docs | `uv run python tools/check_docs_content_policy.py` | No warning for the rewritten claims |
| `docs/23_agent/agent_02_runtime-architecture.md` | Consistency | `uv run python tools/check_docs_consistency.py --domain agent` | Documented shutdown claims match `scripts/` |

## Completion criteria

- The document states the settle-first order once, and no sentence states that resource closing follows the checkpoint.

## Out of Scope

- The step implementations, the configuration keys, and the runbook wording.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the shutdown-order and window wording | Pending | — | — | Phase 7 |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (one owner and sequence), REQ-012 (every step reported)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`
