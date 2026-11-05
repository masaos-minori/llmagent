## Goal
Update the recovery-and-reference drill artifact table to define the three metrics
(`backup_duration_seconds`, RPO, RTO) separately and state the rpo_window_seconds
→ `backup_duration_seconds` rename.

## Scope
**Release unit**: drill metric rename and assertions (shared with
`scripts/db/recovery_drill.py` and `tests/db/test_recovery_drill.py`).

## Assumptions
- `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is the only file in
  `docs/` that documents the drill artifact (a grep for the drill outside `db_07`
  returns nothing).
- The artifact table is at `L176-L182`; the rpo_window_seconds row is `L178`.
- `rto_seconds` is already documented at `L177` as measured wall time.
- Frequency/retention is an owner decision deferred under UNK-01 (`L184`); this edit
  does not touch that sentence.

## Adversarial verification finding — mismatch already present
The current doc (`L178`) defines rpo_window_seconds as "Gap between `drill_ts` and
the archive timestamp", but the code (`scripts/db/recovery_drill.py` `L185`, `L214`)
measures archive **elapsed time**, not the gap from `drill_ts`. The documented
definition and the implemented measurement already disagree even before this Plan.
This row fixes both the label and the definition.

## Design decisions
- **Rename the field row** rpo_window_seconds → `backup_duration_seconds` with the
  correct definition (archive elapsed time).
- **Add `rpo_seconds`** as a distinct row: recovery-point age at the assumed failure
  time (assumed-failure timestamp minus archive completion). Measurement, not a
  threshold.
- **Keep `rto_seconds`** and clarify it is restore-start-to-completion wall time.
- **State the rename** explicitly so operators reading stored artifacts understand
  the field change.

## Alternatives considered
- **Update only the definition, keep the field name.** Rejected: AC-003 requires the
  rpo_window_seconds field to be renamed; the table must reflect the new artifact.
- **Rename without adding RPO/RTO rows.** Rejected: AC-006 requires the three
  metrics defined separately, so `rpo_seconds` and `rto_seconds` need their own rows.

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. Locate the artifact field table (`L176-L182`).
2. Replace the rpo_window_seconds row (`L178`) and refine the surrounding metric
   rows so the three measurements are defined separately. Replace `L177-L178` with:
   ```markdown
   | `backup_duration_seconds` | Archive elapsed time: archive completion minus archive start. The field
     formerly (mis)labeled rpo_window_seconds. Measurement semantics, not a threshold. |
   | `rpo_seconds` | Recovery-point age at the assumed failure time: assumed-failure
     timestamp minus archive completion (staleness of the recovery point).
     Measurement semantics, not a threshold. The assumed-failure event is a
     documented operational decision (see UNK-05). |
   ```
   Keep the existing `rto_seconds` row (`L177`) and ensure it reads as
   restore-start-to-completion wall time:
   ```markdown
   | `rto_seconds` | Measured restore-and-verify wall time (restore start to completion).
     Measurement semantics, not a threshold. |
   ```
3. Add a one-line note adjacent to the table stating the rename:
   > The drill artifact field rpo_window_seconds was renamed to
   > `backup_duration_seconds`; `rpo_seconds` and `rto_seconds` are now defined as
   > distinct measurements derived from recorded event timestamps.
4. Do not modify the UNK-01 frequency/retention sentence (`L184`).

### Method
- Docs-only edit; no code or test change. Keep the table column
  (`Meaning for RPO / RTO reading`) consistent with the new definitions.

### Details
- Current line map: artifact table `L176-L182`; rpo_window_seconds row `L178`;
  `rto_seconds` row `L177`; UNK-01 retention sentence `L184`.

## Compatibility considerations
- The rename must ship together with the code (`recovery_drill.py`) and test
  (`test_recovery_drill.py`) updates so the documented contract matches the artifact.
- No backward-compatibility alias is documented; external consumers were confirmed
  absent (UNK-01).

## Security considerations
- Documentation change only; no security impact.

## Rollback considerations
- Reverting the table edits restores the prior (mislabeled) definitions. No service
  or config change is involved.

## Validation plan
- Read-through: the table defines exactly three distinct metrics and states the
  rename; no stale rpo_window_seconds reference remains in this file.
- Confirm no other `docs/` file references rpo_window_seconds (grep).

## Completion criteria
- `AC-006`: the runbook table defines `backup_duration_seconds`, RPO, and RTO
  separately and states the rename.

## Out of Scope
- Setting RPO/RTO objective values (measurements only).
- Changing the drill's verification logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the drill metric table with the three definitions and the rename | Completed | 20261105-182000 | 20261105-182000 | docs-only edit; code already implements backup_duration_seconds/rpo_seconds (recovery_drill.py L251/L257); docs checkers pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|-----|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004`, `REQ-006`
- **Source issue**: `issues/20261104-143443_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-232133_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-174750
- **Related target files**: `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`
```

## Notes on filling sections

- **Lightweight fill applies.** This is a docs-only row; keep the Procedure to the
  exact table edits.
- **Fix the pre-existing mismatch.** The current definition already disagreed with
  the code; this row corrects both the label and the meaning.
- **Line numbers are guidance.** Verify against live source before editing.
