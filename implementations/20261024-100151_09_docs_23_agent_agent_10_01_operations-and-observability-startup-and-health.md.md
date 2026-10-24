## Goal

Update one agent doc so its "Resource Cleanup on Shutdown" section fully documents the current source behavior, per REQ-008.

- In `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`: expand the "Resource Cleanup on Shutdown" section with (a) the persistence-first ordering rationale and per-step guarding, and (b) the shutdown-error reporting contract (shutdown errors collected as `http_termination` entries, clean shutdown = every server confirmed gone, errors shown on console).

No code changes. No new files.

## Scope

In-scope file:

- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

Out of scope: any production or test code, any other doc, doc front-matter.

## Assumptions

- The existing "Resource Cleanup on Shutdown" section (starts line 74; numbered exit sequence lines 78-82) and the Known Limitations WAL entry (line 147) are the canonical descriptions; the edit adds the *why* and the *reporting* contract without adding steps.
- The reporting mechanism (`http_termination` entries, console display) is already implemented in `scripts/agent/resource_shutdown_coordinator.py` and surfaced via `scripts/agent/startup.py` (`StartupOrchestrator._rollback_servers`); the doc makes this explicit.
- Doc edits do not affect the build, tests, or import layer.

## Design decisions

- **Doc-only, no code.** REQ-008 is a documentation task. The behaviors documented already exist in source; the doc is incomplete relative to them.
- **Anchor to existing passages.** Insert prose adjacent to the existing numbered list and Known Limitations entry rather than rewriting them, to avoid drift in the many cross-references pointing at this section.
- **State the reporting contract explicitly.** Clean shutdown currently implies "no errors" only implicitly; making it first-class prevents readers from assuming a quiet shutdown means no failures occurred.

## Alternatives considered

- **Rewrite the whole "Resource Cleanup on Shutdown" section.** Rejected: it is long and heavily cross-referenced; a targeted insertion reduces drift risk.
- **Add a brand-new operations doc.** Rejected: the behavior already has a home here.

## Implementation

### Target file

`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. Locate the "Resource Cleanup on Shutdown" section header at line 74 and the numbered exit-sequence list spanning lines 78-82.
2. After the numbered list (after line 82, where the existing sentence "Persist is first because it reads `ctx.services` clients that `close_resources()` releases…" begins), insert/merge prose stating:
   - Persistence runs first because it reads `ctx.services` clients that `close_resources()` releases; a persistence failure is contained and reported non-fatal, so it cannot replace the exception the process was already reporting.
   - Each step is independently guarded so a failure in one step does not skip the others.
3. Insert prose stating the shutdown-error reporting contract:
   - Every failed step is added to the collected shutdown errors. For an MCP subprocess whose exit could not be confirmed, the entry is an `http_termination` entry formatted `<server_key> (<outcome>)`.
   - A clean shutdown means every started server was confirmed gone (process group observed to exit, including after SIGKILL).
   - The collected shutdown errors are also shown on the console.
4. Cross-reference the explicit-code anchors `scripts/agent/resource_shutdown_coordinator.py` and `scripts/agent/startup.py` (`StartupOrchestrator._rollback_servers`), consistent with the doc's existing "(Explicit in code — …)" convention at lines 147-148.
5. Confirm the new prose is consistent with the existing Known Limitations WAL entry at line 147 (which already describes abandoned-checkpoint shutdown errors and console display); do not duplicate it — extend the general contract.

### Method

- Edit in place with the `edit` tool using exact-match anchors (the numbered list end and the existing "Persist is first because…" sentence).
- Keep inserted prose in the same terse style as the surrounding doc.
- Do not touch front-matter, tags, or `related:` links.

### Details

- Insertion point: immediately after line 82 (end of the numbered list) — the existing "Persist is first because…" sentence already follows; fold the ordering rationale into that sentence's neighborhood and append the reporting contract after it.
- The reporting contract should read as a distinct short paragraph following the ordering rationale.

## Compatibility considerations

- Additive prose edit to an existing doc. No other doc references the exact sentences being added.
- The doc uses title-based cross-references (heading anchors), not line numbers, so inserts are safe.

## Security considerations

- None. Documentation-only; no secrets, credentials, or operational-exploit surface introduced.

## Rollback considerations

- Revert the `edit` (or `git checkout -- <path>`) to restore the prior doc state. No code, DB, or config impact.

## Validation plan

- Read the edited doc and confirm:
  - The "Resource Cleanup on Shutdown" section now states the persistence-first ordering rationale and per-step guarding.
  - It states the shutdown-error reporting contract (collected errors, `http_termination` entries, clean-shutdown = all confirmed gone, console display).
  - The new prose is consistent with the existing Known Limitations WAL entry (line 147) and does not contradict it.
- Confirm every claim maps to existing source behavior.
- No test run needed (doc-only). If the repo has a doc-lint / markdown check in `rules/toolchain.md`, run it.

## Completion criteria

- The doc contains the specified prose; every claim maps to existing source behavior.
- No code or test files modified. No new files created.
- Cross-references intact.

## Out of Scope

- Any change to `scripts/agent/resource_shutdown_coordinator.py`, `startup.py`, or any test.
- Editing any other doc.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Skipped | — | — | Doc-only; no tests. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document IS the doc update. |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-151742_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-100151
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md
