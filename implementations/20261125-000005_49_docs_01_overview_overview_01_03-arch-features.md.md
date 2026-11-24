## Goal

Update the overview's session-termination description so the persistence and WAL steps it lists are the bounded, recorded sequence the Plan installs, and the WAL backup it describes has the database-scoped name and verified publication (REQ-009: safe backup name and publication; REQ-012: every step reported).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: the "Diagnostic Storage upon Session Termination" block in this document.
- Out of scope: the persister (row 9), the checkpoint manager (row 6), and the operations runbook (row 45).

## Assumptions

- `docs/01_overview/overview_01_03-arch-features.md:65` states that on every REPL exit path diagnostics and memory are persisted and the resources are then closed.
- The numbered list at `docs/01_overview/overview_01_03-arch-features.md:67-69` is Save Session Diagnostics, Persist Session Memory, and WAL Checkpoint, and the checkpoint item is where the defensive WAL backup via `WalCheckpointManager.backup_sync` is described, including the "up to 3 attempts" TRUNCATE fallback and the shutdown-error recording.
- The overview is a feature summary, not a runbook: it states what the sequence guarantees, and the step-by-step operational detail lives in `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` (row 45).
- The "no data loss occurs" and WAL-growth statements in the same item stay true under the new sequence.

## Design decisions

- Keep the existing three items and their guarantees, and add the two steps the sequence now performs around them (settling writers, publishing the backup) rather than replacing the block with a step table: the overview's level of detail is one paragraph plus a short list.
- State the deadline once, in the sentence that introduces the sequence, instead of repeating a number in every item: the number lives in the configuration reference (row 48).
- Describe the backup by its properties (database-scoped name, temporary path, publication only after verification) rather than by a format string, so the overview does not become a second specification of the name.
- Compatibility impact: documentation only.

## Alternatives considered

- Move the whole termination description out of the overview and link to the runbook — rejected: the overview is where a reader first learns that session state is persisted on every exit path, and removing it would leave the feature undocumented at the feature level.

## Implementation
### Target file
`docs/01_overview/overview_01_03-arch-features.md`

### Procedure
1. Update `docs/01_overview/overview_01_03-arch-features.md:65` so the exit-path sentence states that the sequence runs under one deadline and records one outcome per step, and that persistence reads a single session snapshot.
2. Extend the list at `docs/01_overview/overview_01_03-arch-features.md:67-69` with the steps that now precede and follow it: in-flight writers are interrupted and settled first, and the WAL backup is published only after its copy is verified.
3. Update the checkpoint item: the retry attempts are bounded by the time the deadline leaves, and an attempt that runs out of time is recorded as `timed_out` rather than only recorded as a shutdown error.
4. Update the backup sentence in the same item: the file name is scoped to the database and the time and contains no session identifier, the copy is written to a temporary path, and an interrupted backup leaves no file at the final name.
5. Keep the "no data loss occurs" and WAL-growth sentences unchanged.

### Method

- Sentence-level edits inside the existing block; no new heading.

### Details

- The overview names the guarantee, and the runbook (row 45) names the step labels, so the two documents describe the same sequence at different depths.

## Compatibility considerations

- Runs after rows 5, 6 and 9: the sequence and the publication behavior it states are installed by those rows.
- `docs/00_index.md` maps overview-level feature claims to this file; the shutdown claims here must not contradict rows 45 and 46.

## Security considerations

- The backup wording states that the name carries no session identifier, which is the REQ-009 and REQ-013 property an operator needs to rely on.

## Rollback considerations

- Revert this row's commit with the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/01_overview/overview_01_03-arch-features.md` | Docs | `uv run python tools/check_docs_quality.py` | No finding |
| `docs/01_overview/overview_01_03-arch-features.md` | Docs | `uv run python tools/check_docs_structure.py docs/01_overview/overview_01_03-arch-features.md` | No finding |
| `docs/01_overview/overview_01_03-arch-features.md` | Docs | `uv run python tools/check_docs_content_policy.py` | No warning for the rewritten claims |
| `docs/01_overview/overview_01_03-arch-features.md` | Consistency | `uv run python tools/check_docs_consistency.py --domain overview` | Documented shutdown claims match `scripts/` |

## Completion criteria

- The overview states the bounded, recorded sequence and a backup description that matches the name and publication the checkpoint manager produces.

## Out of Scope

- The checkpoint and persister implementations, the configuration keys, and the operational runbook detail.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the termination-sequence and backup wording | Pending | — | — | Phase 7 |
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
- **Requirement ID**: REQ-009 (safe backup name and publication), REQ-012 (every step reported)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/01_overview/overview_01_03-arch-features.md`
