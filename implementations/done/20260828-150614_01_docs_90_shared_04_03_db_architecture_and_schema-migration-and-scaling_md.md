## Goal

Correct `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` section 8 and 8a to accurately describe `eventbus.sqlite`'s incremental migration mechanism owned by `scripts/eventbus/db.py::_migrate()`, instead of grouping it with truly create-only databases (`rag.sqlite`, `session.sqlite`).

## Scope

- **In-Scope**: Update `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` section 8 and 8a; cross-check `docs/06_eventbus_03_persistence_schema_and_replay.md` for consistency.
- **Out-of-Scope**: Modify `scripts/eventbus/db.py`, `scripts/db/create_schema.py`, or any other implementation file. Extend or unify the `create_schema.py` bootstrap path with the `eventbus/db.py` live-migration path. General rewrite of the shared doc beyond correcting the identified `eventbus.sqlite` claim.

## Assumptions

- Both `create_schema.py` and `eventbus/db.py` are the only two code paths affecting `eventbus.sqlite` schema initialization — no third-party tool or external script modifies its schema.
- The `_migrate()` function's current behavior (additive columns, one column drop, additive indexes) is stable and will not change before implementation.

## Design decisions

- Distinguish the `db/create_schema.py` bootstrap path (still create-only/idempotent-DDL for `rag.sqlite`, `session.sqlite`, and for `eventbus.sqlite` when invoked directly) from the EventBus service's own `scripts/eventbus/db.py::open_db()`/`_migrate()` path, which performs incremental, additive migrations on every startup.
- Describe only what `_migrate()` actually does (additive columns, one column drop, additive indexes), consistent with `docs/06_eventbus_03_persistence_schema_and_replay.md`'s existing, already-accurate statement. Do not claim arbitrary schema evolution support.

## Alternatives considered

- Adding the full list of migrated columns/indexes verbatim. Chose concise description over exhaustive detail unless context demands specificity.
- Recording why two separate `eventbus.sqlite` initialization paths exist as intentional design vs. Known Issue. To be determined during implementation (UNK-02).

## Implementation

### Target file

`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

### Procedure

1. Read `scripts/eventbus/db.py::_migrate()` fully and confirm the exact migration operations (columns added, dropped, indexes created).
2. Re-confirm `scripts/eventbus/app.py` still calls `open_db()` at startup (`grep -n "open_db" scripts/eventbus/app.py`).
3. Spot-check whether `rag.sqlite`/`session.sqlite` have an equivalent hidden migration path (UNK-01).
4. Correct section 8's blanket claim that `eventbus.sqlite` "does not support backward-compatible migrations."
5. Update section 8a to note that `eventbus.sqlite` has its own incremental migration mechanism (`scripts/eventbus/db.py::_migrate()`), separate from `workflow.sqlite`'s versioned migration-list mechanism.
6. Cross-check `docs/06_eventbus_03_persistence_schema_and_replay.md` for consistency with the corrected shared-doc wording.

### Method

Direct edit of sections 8 and 8a in the shared documentation. No structural changes to headings or lists.

### Details

- Current section 8/8a claim: `eventbus.sqlite` grouped with `rag.sqlite`/`session.sqlite` as lacking migration support.
- Correction: State plainly that `eventbus.sqlite` does have an incremental migration mechanism owned by `scripts/eventbus/db.py`, distinct in form from `workflow.sqlite`'s versioned migration list (`db/schema_sql.py`) but functionally incremental rather than create-only.
- Document the two `eventbus.sqlite` code paths clearly enough that a reader does not conflate them: `create_schema.py` bootstrap (create-only DDL) vs. `eventbus/db.py` live-service startup (incremental ALTER TABLE operations).

## Compatibility considerations

- This is a documentation-only change; no runtime behavior impact.
- Verify that the correction does not introduce claims about migration scope that cannot be verified against current source.

## Security considerations

- None applicable. No security-relevant behavior changes.

## Rollback considerations

- Simple revert: restore the previous version of the documentation. No data migration or schema rollback needed.

## Validation plan

| Target File | Testing Strategy | Expected Outcome |
|---|---|---|
| `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` | Manual verification: compare updated sections against `scripts/eventbus/db.py::_migrate()` | Sections accurately describe eventbus.sqlite's incremental migration mechanism |
| `docs/06_eventbus_03_persistence_schema_and_replay.md` | Manual verification: cross-reference with corrected shared doc | No contradictions between the two documents |

## Completion criteria

- AC-001: `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` no longer states that `eventbus.sqlite` lacks an incremental migration mechanism; it accurately describes `scripts/eventbus/db.py::_migrate()`'s additive column/index behavior.
- AC-002: The doc clearly distinguishes the `create_schema.py` bootstrap path from the EventBus service's own `open_db()`/`_migrate()` startup path for `eventbus.sqlite`.
- AC-003: `docs/06_eventbus_03_persistence_schema_and_replay.md` and the corrected shared doc do not contradict each other on this point.
- AC-004: No unverified claim about migration scope is introduced — only confirmed additive-column/drop-column/index behavior is described.

## Out of scope

- Modifying any source files under `scripts/eventbus/` or `scripts/db/`.
- Extending or unifying the `create_schema.py` bootstrap path with the `eventbus/db.py` live-migration path.
- Rewriting the shared doc beyond correcting the identified `eventbus.sqlite` claim.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read `scripts/eventbus/db.py::_migrate()` and confirm migration operations | Completed | — | — | Confirmed: additive columns (delivery_failure_count, dlq_requeue_count), drop column (retry_count), additive indexes (idx_events_dlq_at, idx_events_dlq_seq) |
| 2 | Re-confirm `scripts/eventbus/app.py` calls `open_db()` at startup | Completed | — | — | Confirmed at line 59 |
| 3 | Spot-check rag.sqlite/session.sqlite for hidden migration paths | Completed | — | — | No _migrate equivalent found; they remain truly create-only |
| 4 | Correct section 8's blanket claim about eventbus.sqlite | Completed | — | — | Fixed: qualified "All DDL uses IF NOT EXISTS" to apply only to create-only DDL path; removed eventbus from rag/session grouping |
| 5 | Update section 8a with path distinction | Completed | — | — | Fixed: changed "rag/session/eventbus do not support backward-compatible migrations" → "rag/session do not support backward-compatible migrations" |
| 6 | Cross-check `docs/06_eventbus_03_persistence_schema_and_replay.md` | Completed | — | — | No contradictions found |
| 7 | Verification: re-read against source code | Completed | — | — | All sections consistent with source |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: `issues/20260828-130904_doc002_eventbus_migration_description_stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260828-143136_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260828-150614
- **Related target files**: `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
