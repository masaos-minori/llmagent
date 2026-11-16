## Goal

Update `docs/41_db/db_07` section 12 (Recovery Drills): the `_restored` working copy is now deleted after each drill, artifact names are collision-safe, and quarantine directories are now bounded by a retention sweep (REQ-007, AC-8).

## Scope
**Release unit**: retention-sweeps-and-drill-lifecycle

- In scope: edits confined to section 12 of `db_07`.
- Out of scope: sections 9-11 restore/quarantine mechanics (Plans 002/003 already documented there); the drill code itself (row 6).

## Assumptions
- Anchors re-verified 2026-11-16. Section 12 heading at `db_07:156`; the artifact-location/fields text at `:177` (`{drill_dir}/{domain}_{timestamp}.json`, `drill_dir` default `<archive-dir>/drills`); the retention-deferred marker at `:191` (`Frequency and artifact retention are owner decisions tracked under UNK-01 ... {defer the drill cadence and the artifact retention window until UNK-01}`).
- `resolve_unique_path` (row 02) and `purge_archive_artifacts` (row 01) are created by earlier-`seq` siblings; this document references them, it does not introduce them. UNK-01 (production cadence/scheduling) remains an operator decision (WI-008-1); only the artifact/quarantine retention *window* is now bounded in code.
- Pre-existing drift noted during adversarial verification (in section 12, so in this row's edit region): `db_07:159` says "all four domains" and `:170-173` lists a `--domain eventbus` drill command, while the landed drill harness has `DOMAINS = ("rag", "session", "workflow")` (`recovery_drill.py:54`) and defers eventbus to `eventbus.db_tools verify`. Correct these to the landed three-domain shape when editing section 12.

## Design decisions
- Replace only the "retention window" half of the `:191` deferred marker: drill JSON artifacts and quarantine directories now have configured age/count limits (row 1); the cadence/scheduling deferral to UNK-01 stays.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. In section 12 (`:156`): state that the isolated `{name}_restored{suffix}` working copy is deleted immediately after `_persist_artifact` and is never left in the drill directory; a crashed orphan is removed by the `maintenance.py` 1-day stale sweep.
2. At the artifact-location text (`:177`): note the JSON and isolated names are made collision-safe by `resolve_unique_path` (a same-second repeat writes `{domain}_{ts}.json` and `{domain}_{ts}_2.json` rather than overwriting).
3. Replace the retention-window clause of the `:191` marker: drill JSON artifacts are bounded by sqlite_drill_artifact_max_files / sqlite_drill_artifact_max_age_days and quarantine directories (`<db-stem>_sidecar_quarantine_<ts>`, section 9) by sqlite_quarantine_max_files / sqlite_quarantine_max_age_days via purge_archive_artifacts(); keep the cadence/scheduling deferral to UNK-01.
4. Correct the stale domain wording in section 12: "all four domains" -> the three Agent-side domains (rag/session/workflow) and remove the `--domain eventbus` example (eventbus is verified by `eventbus.db_tools verify`), matching the landed `recovery_drill.py` `DOMAINS`.

### Method
- Touch only section 12 text on top of the landed 009 drill wording; re-read the landed text before editing.

### Details
- Reference-table refresh for the new keys is validated by `tools/generate_reference_table.py --check`.

## Compatibility considerations
- Additive/replacement prose within one section; sections 9-11 (Plan 003 quarantine mechanics) are not re-edited here.

## Security considerations
- N/A: documentation.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db`; `uv run python tools/generate_reference_table.py --check`.

## Completion criteria
- Section 12 states the `_restored` deletion, collision-safe artifact names, and the bounded quarantine/drill-JSON retention, with the cadence still deferred to UNK-01; the doc checkers pass.

## Out of Scope
- Production cadence/cron wiring (WI-008-1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update section 12 lifecycle, naming, and retention text | Pending | — | — | |
| 2 | Run the documentation checkers (`check_docs_consistency.py --domain db`, `generate_reference_table.py --check`) | Pending | — | — | |

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
- **Requirement ID**: REQ-007 (document drill artifact lifecycle and quarantine retention)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
