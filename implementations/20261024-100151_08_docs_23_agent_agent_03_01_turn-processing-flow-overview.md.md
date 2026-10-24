## Goal

Update one agent doc so its prose matches the current source, per REQ-008.

- In `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`: add a short prose paragraph under Design Intent immediately preceding the existing "Background Task Failure Threshold Notification and Pausing" bullets, and add a matching Known Limitations entry.

No code changes. No new files.

## Scope

In-scope file:

- `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`

Out of scope: any production or test code, any other doc (including `agent_10_01`, which is a separate row in this plan), any doc front-matter beyond the body edits below.

## Assumptions

- The existing "Background Task Failure Threshold Notification and Pausing" bullet list (lines 85-94) is the canonical description of the runtime behavior; the new prose restates it as Design Intent.
- The existing Known Limitations entry (lines 129-131) is the canonical home for the pause-persistence fact; the new bullet co-locates with it.
- Doc edits do not affect the build, tests, or import layer.

## Design decisions

- **Doc-only, no code.** REQ-008 is a documentation task. The behaviors documented already exist in source; the doc is incomplete relative to them.
- **Anchor to existing passages, not rewrite.** Insert prose adjacent to the existing canonical section rather than rewriting it, to avoid drift in the many cross-references that point at that section.
- **State the reporting mechanism explicitly.** The new prose makes the opt-in/persist-until-restart fact first-class so readers do not assume the pause is global or permanent.

## Alternatives considered

- **Rewrite the whole "Background Task Failure Threshold Notification and Pausing" section.** Rejected: it is a tight bulleted list heavily cross-referenced; a targeted insertion reduces drift risk.
- **Add a brand-new doc for background-task failure.** Rejected: the behavior already has a home here.

## Implementation

### Target file

`docs/23_agent/agent_03_01_turn-processing-flow-overview.md`

### Procedure

1. Locate the "Background Task Failure Threshold Notification and Pausing" section header at line 85 (an existing bulleted list under Design Intent, lines 85-94).
2. Insert a short prose paragraph immediately before the existing bullet list (before line 85) describing: the session-title-generation task scheduled on the first turn tracks consecutive failures; on reaching the threshold `BgTaskMonitor.notify_bg_failure_threshold()` fires once and guarantees user notification with a `logger.critical()` fallback that never propagates; `pause_on_critical_failure` opt-in pauses the specific task type (per-type, not global); `handle_turn()` returns early when any `_bg_pause_state` entry is `True`; the paused state lives only in process memory until restart.
3. Under Key Constraints, add a Known Limitations bullet (near the existing entry at lines 129-131) stating: background-task failure pause is opt-in and the paused state persists until process restart, referencing the "Background Task Failure Threshold Notification and Pausing" section.

### Method

- Edit in place with the `edit` tool using exact-match anchors (the section header `### Background Task Failure Threshold Notification and Pausing` and the surrounding lines above).
- Keep inserted prose in the same terse, bulleted/short-paragraph style as the surrounding doc.
- Do not touch front-matter, tags, or `related:` links.

### Details

- Insertion point: directly before line 85 (`### Background Task Failure Threshold Notification and Pausing`).
- Known Limitations: append after the existing bullet at line 131 (co-located with it).
- The flow diagram (`:42`, `:78`), `## Key Constraints` (`:96-124`), the "Implementation note" paragraph and stage-composition sentence at `:81-83`, and any bracket text owned by turn004 are not edited.

## Compatibility considerations

- Additive prose edit to an existing doc. No other doc references the exact sentences being added, so no downstream doc update is required.
- The doc uses title-based cross-references (heading anchors), not line numbers, so inserts are safe.

## Security considerations

- None. Documentation-only; no secrets, credentials, or operational-exploit surface introduced.

## Rollback considerations

- Revert the `edit` (or `git checkout -- <path>`) to restore the prior doc state. No code, DB, or config impact.

## Validation plan

- Read the edited doc and confirm:
  - The new Design Intent prose immediately precedes the existing "Background Task Failure Threshold Notification and Pausing" bullets (lines ~85-94).
  - A matching Known Limitations entry exists (~line 129-131).
- Confirm the prose matches current source behavior (no new factual claims beyond what source already does).
- No test run needed (doc-only). If the repo has a doc-lint / markdown check in `rules/toolchain.md`, run it.

## Completion criteria

- The doc contains the specified prose; every claim maps to existing source behavior.
- No code or test files modified. No new files created.
- Cross-references intact; no broken heading anchors.

## Out of Scope

- Any change to `scripts/agent/orchestrator.py`, `bg_task_monitor.py`, `resource_shutdown_coordinator.py`, `context.py`, or any test.
- Editing any other doc (including `agent_10_01`, which is row 09).
- turn004's class-docstring cleanup (UNK-03) — out of scope for this pass.

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
- **Related target files**: docs/23_agent/agent_03_01_turn-processing-flow-overview.md
