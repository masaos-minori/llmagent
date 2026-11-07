## Goal

- Update `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` schema section to remove the ledger table and migration-version-chain description and describe the post-cutover EventBus schema policy (REQ-009 / AC-009).

## Scope
**Release unit**: N/A: not part of a release unit (documentation row, Plan Phase 4)

## Assumptions

- The schema paragraph at line 32 carries the ledger/version-chain text (`schema_migrations`, `3 -> 4 -> 5 -> 6`, `eventbus_ledger_baseline`, `scripts/eventbus/migrate.py --apply`, ADR-008 amendment note citing db_03 section 8b) — it is the primary edit target (Plan row evidence: "Cites `schema_migrations`").
- ADR body wording itself is out of this row (compatrm004 owns the ADR sweep); this document only fixes the eventbus doc's own claims.

## Design decisions

- Post-change narrative: current schema is `user_version = 6` (from canonical `schema.sql`) plus the structural fingerprint; an existing database is accepted only on match and refused otherwise for archive-and-recreate; no registered migration route exists.

## Alternatives considered

- Keeping the historical version-chain as background: rejected — docs content policy keeps Current Specification only; history lives in git history and superseded ADR notes owned by compatrm004.

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. After Plan Phases 1-3 land, edit the schema section (Phase 4).

### Method
- Rewrite the line 32 paragraph: delete the registered-chain narrative, ledger baseline sentence, `migrate.py --apply` route, and the `schema_migrations` table references; state the acceptance/refusal rules from document 07's gate (version 6 + fingerprint, refusal message with archive-and-recreate guidance) and note `dlq_outbox` stays part of the current shape (versions 5/6 table changes are now simply the current schema).
- Keep the surrounding replay/delivery semantics paragraphs byte-identical.

### Details
- Verify every retained claim against post-change `scripts/eventbus/schema.sql` and `scripts/eventbus/schema.py` before writing (docs consistency rule).

## Compatibility considerations

- N/A: docs-only.

## Security considerations

- N/A: docs-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_consistency.py --domain eventbus` (routing.md Tools).

## Completion criteria

- The eventbus schema document contains no ledger/migration-route claims and matches the regenerated canonical shape (AC-007, AC-009).

## Out of Scope

- ADR-008 amendment text sweep — plan compatrm004.
- `db_03` rewrite — own document (seq 27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the schema-section paragraph to the post-cutover policy (Plan Phase 4) | Pending | — | — | Docs row: no release unit |
| 2 | Run the docs checkers named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-009 (documentation describes the current-schema-only policy)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
