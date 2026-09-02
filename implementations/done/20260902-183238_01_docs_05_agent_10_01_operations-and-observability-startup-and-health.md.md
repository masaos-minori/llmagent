## Goal
Satisfy `REQ-001`/`REQ-003` (Plan `plans/20260901-070239_plan.md`): add an Operations
runbook section to `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`
describing the manual recovery procedure for `workflow.sqlite` and `eventbus.sqlite`.

## Scope
Add exactly one new `### ` subsection under the existing `## Operational Notes` section
of `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`. No other
section of this file is touched. Does not modify `scripts/db/rotation.py`,
`scripts/db/recovery.py`, or ADR-008 itself (Plan Out-of-Scope).

## Assumptions
- Re-verified 2026-09-02: `scripts/db/rotation.py`'s `rotate_all_dbs()` (lines 68-78)
  confirms all four databases are archived, calling `rotate_workflow_db()` and
  `rotate_eventbus_db()` — the Plan's cited "lines 72-78" is a 4-line shift from
  current source but the content and conclusion are unchanged.
- `scripts/db/recovery.py::recover_corruption()` (line 237-241) confirms
  `action="no_recovery_allowed"` is returned for `target in ("workflow", "eventbus")`,
  consistent with ADR-008 INV-18 (`docs/adr/ADR-008-sqlite-4db-separation.md` line 300).
- `_resolve_archive_dir()` (the actual function backing archive-directory resolution)
  is defined in `scripts/db/rotation.py` (lines 15-21), not `scripts/db/config.py` as
  the Plan's Reference Files row states — this is a Reference File citation
  inaccuracy only (not a Target File row), out of this document's scope to correct,
  and does not change the runbook's content since the resolution logic itself
  (`cfg.get("sqlite_archive_dir")`) is confirmed either way.
- `scripts/db/recovery.py` line 238's code comment cites "ADR-011 Requirement #6" —
  ADR-011 was merged into ADR-008 in the 2026-08-31 consolidation and no longer
  exists as a separate file. This is stale-comment drift in a Reference File, out of
  this Plan's scope (Plan Out-of-Scope: "change ADR-008's recovery policy itself");
  not corrected here.

## Design decisions
Place the runbook as a new `### Manual Recovery: workflow.sqlite / eventbus.sqlite`
subsection under the existing `## Operational Notes` section, alongside its sibling
subsections (`### Restoration of Pending Post-Execution Approvals`, `### Resource
Cleanup on Shutdown`, `### SIGINT/SIGTERM Interruption During Startup`) — these are
all existing operator-facing procedural subsections of the same kind, so the new
runbook fits the established document structure rather than requiring a new top-level
`## ` section (Plan `Design`'s Path A classification: small, doc-only task).

Structure the runbook per the Plan's own Design section (5 steps): precondition check,
validate candidate, apply restore, post-restore verification, no-backup escalation
path.

## Alternatives considered
Adding a new top-level `## Manual Database Recovery` section instead of a `###`
subsection under `## Operational Notes` — considered, but rejected: the existing
`## Operational Notes` section already groups exactly this kind of operator
procedure (shutdown cleanup, interruption handling), so a new top-level section would
duplicate that grouping rather than extend it.

## Implementation
### Target file
docs/05_agent_10_01_operations-and-observability-startup-and-health.md

### Procedure
Add a new `### Manual Recovery: workflow.sqlite / eventbus.sqlite` subsection under
`## Operational Notes`, after the existing `### SIGINT/SIGTERM Interruption During
Startup` subsection and before `## Known Limitations / Unresolved Issues`.

### Method
1. Locate the boundary between `### SIGINT/SIGTERM Interruption During Startup`
   (current lines 83-86) and `## Known Limitations / Unresolved Issues` (current line
   87).
2. Insert a new subsection:
   ```markdown
   ### Manual Recovery: workflow.sqlite / eventbus.sqlite

   Per ADR-008 INV-18, automatic restoration is prohibited for `workflow.sqlite` and
   `eventbus.sqlite` — corruption recovery for these two databases is a manual
   operator action only (`scripts/db/recovery.py::recover_corruption()` returns
   `action="no_recovery_allowed"` for these targets). This is intentionally different
   from `rag.sqlite` (rebuilt) and `session.sqlite` (automatically restored from
   backup).

   1. **Locate available backups**: `rotate_all_dbs()`
      (`scripts/db/rotation.py`) archives all four databases, including
      `workflow.sqlite` and `eventbus.sqlite`, to the configured archive directory
      (`sqlite_archive_dir` config key; resolved by
      `scripts/db/rotation.py::_resolve_archive_dir()`). List timestamped archive
      files there to find the most recent copy of the corrupted database.
   2. **Validate a candidate**: run SQLite's built-in integrity check against the
      archived copy (e.g. `sqlite3 <archive_path> "PRAGMA integrity_check;"`) before
      using it — do not restore from an archive that has not been validated.
   3. **Apply the restore manually**: stop the affected service, copy the validated
      archive file over the corrupted live database path, then restart the service.
      This step is a manual filesystem operation — no automated restore path exists
      for these two databases by design (ADR-008 INV-18).
   4. **Post-restore verification**: re-run the integrity check against the restored
      live database file to confirm the copy succeeded before resuming normal
      operation.
   5. **No valid backup available**: if no archived copy passes the integrity check,
      this is a data-loss event for the affected database. Escalate per standard
      incident-handling procedure rather than attempting an unvalidated restore;
      `workflow.sqlite`/`eventbus.sqlite` have no automatic fallback by policy.

   Archived copies accumulate without automatic deletion — `rotate_all_dbs()`'s
   archiving has no retention/cleanup logic of its own (a separate, narrower
   mechanism, `scripts/db/maintenance.py::CorruptArchiveRetentionConfig`, governs only
   the pre-restore safety copies `recover_corruption()` creates for `rag`/`session`,
   not these `rotate_all_dbs()` archives).
   ```

### Details
This subsection is additive only — it does not modify any existing subsection's text,
and does not change `## Known Limitations / Unresolved Issues` or `## Related Docs`
(both remain as-is; the cross-reference from ADR-008 to this new subsection is a
separate row, seq 02 of this same Plan).

## Compatibility considerations
Documentation-only addition; no code, schema, or runtime behavior affected.

## Security considerations
N/A: the runbook describes an existing, already-implemented manual procedure; it does
not introduce new tooling, credentials, or automated recovery paths.

## Rollback considerations
Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan
- Manual review: confirm the runbook accurately reflects `rotate_all_dbs()`'s current
  behavior and does not suggest automatic restoration for workflow/eventbus (Plan
  `Validation plan`).
- `uv run python tools/check_docs_quality.py` — confirm no new structural issues for
  this file (Plan Acceptance criteria).

## Completion criteria
`docs/05_agent_10_01_operations-and-observability-startup-and-health.md` contains a
runbook subsection covering: locating backups, validating a candidate, applying the
restore, post-restore verification, and the no-backup escalation path — matching
REQ-001 (accurate backup coverage) and REQ-003 (all four scenarios covered) — without
contradicting ADR-008 INV-18's automatic-restoration prohibition (REQ-002, verified by
the wording above stating "manual operator action only").

## Out of scope
Implementing new automatic backup/recovery code (Plan Out-of-Scope). Changing ADR-008's
recovery policy itself (Plan Out-of-Scope). Correcting the stale "ADR-011" comment
reference in `scripts/db/recovery.py` (a Reference File, not a Target File for this
Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Manual Recovery runbook subsection per Method | Pending | — | — | |
| 2 | N/A: no automated test for a documentation-only runbook addition | Pending | — | — | N/A |
| 3 | Run `uv run python tools/check_docs_quality.py` | Pending | — | — | |
| 4 | N/A: this file is itself the documentation being updated | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (manual recovery runbook for workflow/eventbus)
- **Source issue**: `issues/20260831-181721_adr008_03_workflow_eventbus_manual_recovery_runbook.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-070239_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183238
- **Related target files**: `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`
