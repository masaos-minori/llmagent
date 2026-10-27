## Goal

Update `agent_03_01_turn-processing-flow-overview.md` so the pause-state description
states the success-based resume semantics introduced by REQ-1, replacing the now-false
"persists until the process restart" claims.

## Scope

- Two statements in `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`: the
  bullet at L93 and the Known Limitations entry at L131.
- Deferred docs-phase row: execute only after the seq 01 code change lands, so the doc
  describes shipped behavior.

## Assumptions

- The seq 01 procedure (`scripts/agent/bg_task_monitor.py`) implements the resume clear;
  this document must not land before it (docs-vs-code interim window flagged in the Plan
  Risks).
- No other doc makes a pause-persistence claim: repo-wide docs grep finds the claim only
  at L93/L131 here; `agent_02_runtime-architecture.md` L46/L50 mention blocking/opt-in
  only and need no change (reference, not a target).

## Design decisions

- State both the in-memory nature and the new clear condition in one sentence per site;
  keep the per-task-type wording already at L91 untouched.
- Keep the Known Limitations entry (the pause still exists and is still opt-in) — only
  its persistence clause changes.

## Alternatives considered

N/A: documentation-only wording update; the resume semantics themselves are decided by
the Plan (REQ-1).

## Implementation
### Target file

`docs/23_agent/agent_03_01_turn-processing-flow-overview.md`

### Procedure

Replace the two stale persistence statements with resume semantics; change nothing else.

### Method

1. L93: replace

   > The paused state is held only in process memory and persists until the process restarts.

   with

   > The paused state is held only in process memory and persists until a clean completion of the same task type clears it (a threshold breach pauses; the next success of that type resumes it).

2. L131 (Known Limitations): replace

   > Background task failure pause is opt-in, and the paused state persists until process restart (see Background Task Failure Threshold Notification and Pausing).

   with

   > Background task failure pause is opt-in, and the paused state persists until a clean completion of the same task type clears it (see Background Task Failure Threshold Notification and Pausing).

### Details

- No section headings, front matter, or Keywords list changes; bullet-level edits only.

## Compatibility considerations

N/A: prose-only doc change; cross-doc links (`agent_02_runtime-architecture.md`
references to this document) stay valid.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Check | Command | Expected |
|-------|---------|----------|
| no stale claim | `grep -n "until the process restart" docs/23_agent/agent_03_01_turn-processing-flow-overview.md` and `grep -n "until process restart" docs/23_agent/agent_03_01_turn-processing-flow-overview.md` | zero matches |
| docs gate | `uv run python tools/check_docs_quality.py && uv run python tools/check_docs_structure.py docs/23_agent/agent_03_01_turn-processing-flow-overview.md && uv run python tools/check_docs_content_policy.py && uv run python tools/check_docs_consistency.py --domain agent` | clean |

## Completion criteria

- REQ-3: no "persists until the process restart" claim for pause state remains in this
  document, and both edited statements match the behavior implemented by seq 01.

## Out of Scope

- Changes to `docs/23_agent/agent_02_runtime-architecture.md` (verified: no persistence
  claim) or any other document.
- `docs/00_index.md`: no mapping change (Plan Documentation Impact).
- Code and tests (seq 01/02 documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the two persistence statements per Procedure/Method | Pending | — | — | Run after the seq 01 code change lands |
| 2 | Run the documentation checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-3` (docs describe the resume semantics)
- **Source issue**: `issues/20261026-225036_bgmonitor001_reset-background-failure-pause.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-085246_bgmonitor001_reset-background-failure-pause.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-235926
- **Related target files**: `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`
