## Goal

Replace the diagnostics-path shutdown wording: the `finally` block items become recorded steps of one bounded sequence, and the claim that `shutdown_all()` absorbs a second Ctrl-C is replaced by the interrupt routing the Plan installs (REQ-010: termination bounded by the shutdown deadline; REQ-012: every step reported).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: the shutdown bullet list and the SIGINT-absorption statement in this document.
- Out of scope: the persister (row 9), the lifecycle coordinator (row 11), and the signal handler (row 10).

## Assumptions

- `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md:65` describes the REPL input competing with `_shutdown_event`, and `:66-69` lists the `finally` block items: session diagnostics persistence, `memory.on_session_stop()`, and resource cleanup through `lifecycle.shutdown_all()` and closing HTTP clients.
- `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md:70` states that `shutdown_all()` temporarily absorbs additional `SIGINT` during execution and restores normal handling afterwards. That absorption is what row 11 removes.
- The diagnostics and memory writes are the persistence step the Plan keeps, and they read one snapshot captured before the later steps run (row 9).

## Design decisions

- Replace the absorption statement outright rather than qualifying it: the Plan's requirement is that a second signal interrupts the running step, so a document that says the signal is swallowed contradicts the requirement it is meant to describe.
- Keep the bullet structure and add the outcome each item records, so the document still reads as a path description rather than a step table.
- Cross-reference the runbook (row 45) for the full step list instead of duplicating it here: this document's scope is the diagnostics and memory path.
- Compatibility impact: documentation only.

## Alternatives considered

- Keep the absorption statement and note that it is now opt-in — rejected: absorption is removed, not made configurable; only the force exit is configurable.

## Implementation
### Target file
`docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`

### Procedure
1. Update the `finally` block list at `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md:66-69`: the diagnostics and memory writes run as the persistence step from one session snapshot, and each item records one outcome in the shutdown report.
2. State that the resource-cleanup item runs with the time the deadline leaves, and that a server whose exit was not confirmed appears in the reported unconfirmed list.
3. Replace the absorption statement at `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md:70`: during shutdown a second Ctrl-C requests an interrupt on the step in progress, nothing is absorbed, and the process exits through the force-exit path only when `shutdown_force_exit_on_second_sigint` (new) is true.
4. Keep the input-competition bullet at `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md:65` and add that once the acceptance phase is draining, new commands and turns are refused.

### Method

- Bullet-level rewrites inside the existing shutdown subsection; no new heading.

### Details

- The step names used here are the ones the report prints, matching rows 45 and 46.

## Compatibility considerations

- Runs after rows 5, 9, 10 and 11: the behavior it documents is installed by those rows.
- `docs/00_index.md` maps diagnostics and memory claims to this file; the shutdown claims must not contradict rows 45 and 46.

## Security considerations

- N/A: no path or exception text is quoted.

## Rollback considerations

- Revert this row's commit with the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Docs | `uv run python tools/check_docs_quality.py` | No finding |
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Docs | `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | No finding |
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Docs | `uv run python tools/check_docs_content_policy.py` | No warning for the rewritten claims |
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Consistency | `uv run python tools/check_docs_consistency.py --domain agent` | Documented shutdown behavior matches `scripts/` |

## Completion criteria

- No statement in this document says a signal is absorbed during shutdown, and every `finally` item is described as a recorded step.

## Out of Scope

- The persister and coordinator implementations, and the full step sequence (rows 45, 46).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the finally-block and SIGINT-absorption wording | Pending | — | — | Phase 7 |
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
- **Requirement ID**: REQ-010 (termination bounded by the shutdown deadline), REQ-012 (every step reported)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`
