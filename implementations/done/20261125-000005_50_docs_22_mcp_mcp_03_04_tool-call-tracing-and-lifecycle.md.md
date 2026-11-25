## Goal

Correct the MCP lifecycle document's termination claim: the total shutdown time is bounded by the remaining shutdown deadline, not by a fixed 30-second window, and an unconfirmed server stays reported (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: the "Implementation Note (Shutdown Termination)" in this document.
- Out of scope: the terminator (row 12), the lifecycle coordinator (row 11), and the manager facade (row 13).

## Assumptions

- `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md:97` states that during `shutdown_all()` every HTTP subprocess server receives SIGTERM at the start and the servers are awaited together, so total shutdown time is bounded by one termination timeout of 30 seconds rather than the sum over servers.
- The "awaited together" property is unchanged by this Plan: what changes is the size of the window and where it comes from.
- The 30-second figure is the module constant `_SHUTDOWN_TIMEOUT_SEC` in `scripts/agent/http_lifecycle_shutdown_coordinator.py`, which the Plan replaces with the budget-derived window plus `shutdown_termination_confirm_seconds` (new) as the confirm fallback.

## Step 3b verification against the current source (20261125-122600)

- Anchor holds: the Implementation Note (Shutdown Termination) paragraph is `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md:97`.
- Scope extended by one paragraph: the Implementation Note (Double SIGINT Guard) at `:91-93` stated that the handler is always `_absorb_sigint_during_shutdown()`. The code now installs `_request_interrupt_on_sigint(budget)` when a budget is supplied and the absorb guard only when it is not (`scripts/agent/http_lifecycle_shutdown_coordinator.py:184-193`), so leaving that note untouched would keep a false claim in the same document. It was rewritten alongside the target paragraph.
- The window is `min(_SHUTDOWN_TIMEOUT_SEC, budget.remaining())` with `_SHUTDOWN_TIMEOUT_SEC = 30.0` as the no-budget fallback (`scripts/agent/http_lifecycle_shutdown_coordinator.py:38-41`, `:88-96`); per the Design decision the document names the budget and the fallback without quoting the constant. The confirm window is owned by `ProcessTerminator` and reaches its configured value through the factory injection recorded in row 48.

## Design decisions

- State the bound as "the time left in the shutdown sequence" and name the configuration key that sets the total, rather than quoting a number: a document that repeats a constant is the thing that goes stale when the constant changes.
- Keep the "not the sum over servers" property explicit, because it is the reason the shared window exists and the Plan preserves it.
- Add that SIGTERM and SIGKILL are always sent and that only the waiting is shortened, so the document cannot be read as "termination is skipped when time runs out".
- Compatibility impact: documentation only.

## Alternatives considered

- Keep the 30-second figure and add "unless a budget is supplied" — rejected: the default is no longer 30 seconds, so the figure would be the wrong baseline rather than the common case.

## Implementation
### Target file
`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`

### Procedure
1. Rewrite `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md:97`: the servers are still sent SIGTERM together and awaited together, and the shared window is the remaining time of the armed shutdown budget, whose total is `shutdown_deadline_seconds` (new).
2. State that each server's confirm window is clamped to the time left, that SIGKILL is still sent when the term window expires, and that a server whose exit cannot be confirmed is reported as unconfirmed in the returned list.
3. Keep the surrounding tracing and lifecycle wording unchanged.

### Method

- One paragraph replacement inside the existing Implementation Note.

### Details

- The unconfirmed outcome is the same value the shutdown report counts (row 5), so the document and the report name it identically.

## Compatibility considerations

- Runs after rows 11, 12, 13, 14 and 15: the clamped behavior it describes is installed by those rows.
- `docs/00_index.md` maps `HttpServerLifecycleManager` / `http_lifecycle.py` claims to this file and to `docs/23_agent/agent_02_runtime-architecture.md` (row 46); both must state the same bound.

## Security considerations

- N/A: no path, command line, or credential is quoted.

## Rollback considerations

- Revert this row's commit with the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Docs | `uv run python tools/check_docs_quality.py` | No finding |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Docs | `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | No finding |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Docs | `uv run python tools/check_docs_content_policy.py` | No warning for the rewritten claim |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Consistency | `uv run python tools/check_docs_consistency.py --domain mcp` | Documented termination behavior matches `scripts/` |

## Completion criteria

- No sentence in this document states a fixed termination timeout, and the unconfirmed-server outcome is stated as reported.

## Out of Scope

- The termination implementation, the budget, and the shutdown report rendering.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the termination-window wording | Completed | 20261125-130118 | 20261125-130118 | Phase 7 Termination-window and SIGINT-guard paragraphs rewritten; Step 3b note added |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-130118 | 20261125-130118 | quality/structure/policy clean |

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
- **Requirement ID**: REQ-010 (termination bounded by the shutdown deadline)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`