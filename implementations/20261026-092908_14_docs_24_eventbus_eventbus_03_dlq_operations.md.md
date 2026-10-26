## Goal

Document the DLQ reconciliation procedure in `docs/24_eventbus/eventbus_03_dlq_operations.md`
so operators can deterministically recover DLQ files that the background sweep cannot
self-heal: files missing or corrupted after promotion, and leftover orphan files. Drives
REQ-006; Acceptance 4.

## Scope

- Update only `docs/24_eventbus/eventbus_03_dlq_operations.md`: add a "## DLQ Reconciliation"
  section after "## DLQ Background Sweep", and extend the "Failure Behavior Summary" table.

## Assumptions

- The background sweep (`sweep_orphans` → `_shared_promote`, `scripts/eventbus/dlq.py`)
  self-heals orphan files (`dlq_at IS NULL` with an existing `{event_id}.json`) by re-writing
  the file and setting `dlq_at`; this row documents the divergence the sweep CANNOT heal.
- The write-file-then-set-`dlq_at` durability order in `_atomic_write`/`_shared_promote` is
  out of scope (H-01); this doc only documents reconciliation of the file/DB divergence that
  order can leave behind.
- UNK-04 (reconciliation tool versus procedure) is an owner decision recorded before
  implementation. This row delivers the procedure form; a `scripts/eventbus/reconcile_dlq.py`
  CLI would be a separate row if the owner selects automation.
- `dlq_at IS NULL` means "not yet promoted"; `dlq_at IS NOT NULL` means "promoted". A promoted
  event whose `{event_id}.json` is missing or unparseable is unrecoverable by the sweep.

## Design decisions

- **Reconciliation section.** Document the three divergence cases and a deterministic operator
  procedure for each: orphan (file exists, `dlq_at IS NULL` — normally self-healed by the
  sweep; list any remaining and promote-or-delete per policy), missing (row has `dlq_at IS
  NOT NULL`, `{event_id}.json` absent — rebuild the DLQ record from the JSONL archive or
  quarantine), corrupt (`{event_id}.json` present but unparseable — quarantine and flag for
  manual review). State the self-heal sweep as the baseline.
- **Scope boundary.** State explicitly that reconciliation preserves the write-file-then-set-
  `dlq_at` durability order and does NOT alter the requeue transaction (H-01) or the startup
  schema-integrity gate (H-03 / readiness definition).

## Alternatives considered

- A CLI entry point (`scripts/eventbus/reconcile_dlq.py`) that automates recovery instead of a
  documented manual procedure. Adopt only if UNK-04 selects automation; the documented
  procedure is the lower-surface option and is what this row delivers.

## Implementation

### Target file

`docs/24_eventbus/eventbus_03_dlq_operations.md`

### Procedure

Add a "## DLQ Reconciliation" section after "## DLQ Background Sweep", and extend the
"Failure Behavior Summary" table with the reconciliation rows.

### Method

1. After the "## DLQ Background Sweep" section, insert "## DLQ Reconciliation" stating:
   - Self-heal baseline: the background sweep (`sweep_orphans`) re-promotes orphan files
     (`dlq_at IS NULL` plus an existing `{event_id}.json`) by re-writing the file and setting
     `dlq_at`; a non-zero sweep count under normal operation indicates an inline-promotion bug,
     not a normal condition.
   - Orphan (file exists, `dlq_at IS NULL`): normally self-healed by the sweep; the
     reconciliation procedure lists any remaining orphans and promotes-or-deletes them per
     policy.
   - Missing (row has `dlq_at IS NOT NULL`, `{event_id}.json` absent): rebuild the DLQ record
     from the JSONL archive (`published_at`, `topic`, `payload`, `producer`) and re-set
     `dlq_at`, or quarantine the event per policy.
   - Corrupt (`{event_id}.json` present but unparseable JSON): quarantine the file (rename to
     `*.corrupt`) and flag for manual review; do not silently rewrite it.
   - Boundary: reconciliation preserves the write-file-then-set-`dlq_at` durability order and
     does not touch the requeue transaction (H-01) or the readiness/integrity definition (H-03).
2. In the "Failure Behavior Summary" table, add rows for a DLQ file found missing or corrupt
   after promotion → reconciliation required (the existing JSONL-append-failure row stays).
3. Cross-reference `eventbus_05_dlq_offsets_and_delivery_semantics.md` (promotion paths) and
   `eventbus_06_persistence_schema_and_replay.md` (replay-delivery semantics used when
   rebuilding a record).

### Details

- Keep the section consistent with the existing tone; add `eventbus_06_persistence_schema_and_replay.md`
  to the `related:` front-matter list if it is not already there.
- Do not introduce a new HTTP route or CLI in this doc; reconciliation is an operator procedure
  (or a future CLI per UNK-04).
- Token values and secrets must stay out of any example output (INV-05; REQ-007).

## Compatibility considerations

N/A: documentation-only change; no runtime or API contract impact.

## Security considerations

- Reconciliation examples must not expose token values or secrets carried in `payload`
  (INV-05; REQ-007).
- Quarantine (rename to `*.corrupt`) stops the background sweep from re-processing a corrupt
  file as if it were healthy.

## Rollback considerations

N/A: revert the doc edit.

## Validation plan

- Read-through: the new "DLQ Reconciliation" section states all three divergence cases, the
  self-heal baseline, and the scope boundary; the "Failure Behavior Summary" table is extended.
- `ruff`/`mypy`/`lint-imports` remain unaffected (doc-only).

## Completion criteria

The "DLQ Reconciliation" section in `docs/24_eventbus/eventbus_03_dlq_operations.md` documents
the orphan/self-heal, missing (rebuild/quarantine), and corrupt (quarantine/manual-review)
cases, the self-heal sweep baseline, and the scope boundary relative to H-01/H-03, and the
"Failure Behavior Summary" table reflects them.

## Out of Scope

- Adding a `reconcile_dlq.py` CLI entry point (UNK-04 automation; separate row if adopted).
- Changing the promotion durability order or the requeue transaction (H-01).
- The startup schema-integrity gate (H-03 / readiness definition).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Sign-off gate on UNK-04 (procedure vs CLI) |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: doc-only row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (DLQ reconciliation exists for missing/orphan/corrupt files; Acceptance 4)
- **Source issue**: `issues/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `docs/24_eventbus/eventbus_03_dlq_operations.md`
