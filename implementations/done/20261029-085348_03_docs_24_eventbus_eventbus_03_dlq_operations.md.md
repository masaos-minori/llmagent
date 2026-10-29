## Goal

Update the DLQ reconciliation docs to reflect the new automated reconciliation (`reconcile_missing_dlq_files` (new), created by seq 01): a missing DLQ file on a promoted event is now self-healed by rebuilding from SQLite, JSONL is explicitly best-effort and NOT a rebuild source, and the manual operator-command sentence is deferred until UNK-01 resolves ownership.

## Scope

Docs-only edit to `docs/24_eventbus/eventbus_03_dlq_operations.md`. No production code, no tests.

## Assumptions

- `reconcile_missing_dlq_files (new)` is created by seq 01 (`implementations/20261029-085348_01_scripts_eventbus_dlq.py.md`); it is marked `(new)` here because it does not yet exist in the repo.
- The authority model is unchanged: SQLite `events.dlq_at` is authoritative; the JSON file is a derived artifact written first and visible only once `dlq_at` is set (existing line 120).
- JSONL append is best-effort (`eventbus_09_publish_durability.md`); an event whose append failed exists only in SQLite.
- UNK-01 (whether an operator command triggers rebuild) is unresolved; defer any "run command X" sentence.
- Corrupt-file policy (quarantine to `*.corrupt`, manual review) is unchanged.

## Design decisions

- Keep the divergence-case structure (Orphan / Missing / Corrupt); only the "### Missing Files" subsection text changes.
- State SQLite as the sole rebuild source and JSONL as best-effort/not-a-rebuild-source.
- Leave the "### Corrupt Files" subsection (existing lines 142-144) untouched.
- Update the Failure Behavior Summary row for "DLQ file missing after promotion" to say "rebuild from SQLite via reconciliation, or quarantine".
- Defer the operator-command sentence; add a placeholder noting UNK-01.

## Alternatives considered

- Rewriting the whole "DLQ Reconciliation" section: rejected; out of scope, and the authority model + corrupt policy are correct as-is.
- Naming the function inline in the inserted text: the function is new (seq 01); the inserted docs text uses the descriptor "background reconciliation" to stay clean, and the function name is cited (marked `(new)`) in the Procedure step and Details.

## Implementation

### Target file

`docs/24_eventbus/eventbus_03_dlq_operations.md`

### Procedure

1. Open `docs/24_eventbus/eventbus_03_dlq_operations.md`.
2. Replace the "### Missing Files" subsection (existing lines 138-140) with the new subsection in Method below.
3. Update the Failure Behavior Summary table row for "DLQ file missing after promotion" (existing line 161) per Method below.
4. Do not touch the "### Orphan Files" (line 134-136) or "### Corrupt Files" (line 142-144) subsections.
5. Run `stale_detector.py` on this document (cite doc files by full leading-slash path; mark `reconcile_missing_dlq_files` (new)).

### Method

Replace existing lines 138-140 with:

```markdown
### Missing Files (row has `dlq_at IS NOT NULL`, `{event_id}.json` absent)

The background reconciliation rebuilds the lost file from the SQLite row, which is the authoritative DLQ source (see Authority model above). Rebuild reads the event row (`event_id`, `topic`, `payload`, `producer`, `published_at`) and writes the record using the same write-file-then-set-`dlq_at` order. JSONL is best-effort and is not a rebuild source: an event whose JSONL append failed exists only in SQLite and is rebuilt from SQLite here; if the SQLite row is itself absent, quarantine the event per policy. Reconciliation runs on a schedule and retries a transient write failure on the next pass. {defer operator-command sentence until UNK-01}
```

Update existing line 161 from:

```
| DLQ file missing after promotion | Rebuild from JSONL archive or quarantine |
```

to:

```
| DLQ file missing after promotion | Rebuild from SQLite via background reconciliation, or quarantine |
```

### Details

- The inserted text names the function as "background reconciliation" to avoid embedding the `(new)` marker in the final docs file; the function is `reconcile_missing_dlq_files` (new), introduced by seq 01.
- `{defer operator-command sentence until UNK-01}` is a placeholder token; remove it once UNK-01 is resolved, or replace it with the operator-command sentence if ownership is assigned.
- `dlq_at`, `event_id`, `topic`, `payload`, `producer`, `published_at`, and `SQLite` already appear in this doc, so they resolve against the target file.
- Cite doc files by full leading-slash path so the stale detector skips them in the symbol check.

## Compatibility considerations

- Purely documentary; no API or behavior change. The "Scope boundary" note (existing line 146) already states reconciliation preserves the write-file-then-set-`dlq_at` order and does not alter H-01 or H-03.

## Security considerations

None.

## Rollback considerations

Revert the two edits (subsection + table row) to restore the prior text.

## Validation plan

1. Read `docs/24_eventbus/eventbus_03_dlq_operations.md` and confirm the "Missing Files" subsection now states SQLite-as-source and JSONL-best-effort, and that Orphan/Corrupt subsections are unchanged.
2. Confirm the Failure Behavior Summary row for "DLQ file missing after promotion" says "Rebuild from SQLite via background reconciliation, or quarantine".
3. Run `stale_detector.py` on this document (must report "not stale").

## Completion criteria

- "### Missing Files" subsection rewritten per Method.
- Failure Behavior Summary row updated.
- Corrupt/Orphan sections untouched.
- `stale_detector.py` clean.

## Out of Scope

- Production implementation of `reconcile_missing_dlq_files (new)` (seq 01).
- Orphan-file and corrupt-file policy text.
- UNK-01 operator-command resolution.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261029-110726 | Docs-only edit |
| 2 | Add or update tests per Validation plan | Completed | — | 20261029-110726 | No tests for docs change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261029-110726 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261029-110726 | This is the docs deliverable |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-085348
- **Related target files**: `docs/24_eventbus/eventbus_03_dlq_operations.md`