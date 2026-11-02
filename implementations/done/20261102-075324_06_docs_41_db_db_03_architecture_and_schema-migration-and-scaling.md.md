# Document the per-step migration contract and CLI option

## Goal

Update the shared migration contract text so it states the actual per-step mechanism,
ledger timing, foreign-key handling, the CLI database-file option, and the
postcondition order (Plan REQ-007).

## Scope

- One paragraph edit in the "Migration guarantees" subsection of section 8
  (line 58) of `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`.
- No other doc file changes; `db_07` and ADR-008 stay as-is (Plan Reference Files).

## Assumptions

- Intent-and-failure-behavior style only: no code snippets, no line-level detail
  (docs policy of this file).

## Design decisions

- Extend the existing "Per-step transactionality" bullet in place rather than adding a
  new subsection: the guarantee list is the canonical contract statement.

## Alternatives considered

- N/A: docs-only row.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. In the "Migration guarantees" paragraph, expand **Per-step transactionality**: the
   runner owns one write transaction per step (explicit begin, statements executed
   individually, the `schema_migrations` ledger row written in the same transaction),
   so a failing step leaves no partial change and the database never half-applies a
   migration.
2. Add a **Foreign-key handling** statement: a step may opt out of foreign-key
   enforcement for its transaction; the setting is switched before the transaction
   begins, checked with `PRAGMA foreign_key_check` before commit (a violation rolls the
   step back), and the prior setting is always restored.
3. Add the **pre-commit verification and postcondition order**: step preconditions run
   before the transaction, an optional verification callback runs before commit (its
   failure rolls the step back), and a step's postcondition re-check runs after the
   commit.
4. Add a **CLI rehearsal** sentence: `migrate_db.py` accepts a database-file option so
   `--status`, `--dry-run` and `--apply` can be rehearsed on a copy; a path that does
   not exist is refused without creating a file, and it is for rehearsal, not for
   bypassing service handling.

### Method
- Single-paragraph rewrite within section 8; keep the existing bullet-bold style.

### Details
- Keep the existing sentences about the verified-backup precondition, dry-run purity,
  and refusal classes unchanged.

## Compatibility considerations

- N/A: documentation-only change; ADR-008's rollback sentence already matches the
  corrected behavior.

## Security considerations

- N/A: docs-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`,
  `uv run python tools/check_docs_content_policy.py`, `uv run python
  tools/check_docs_consistency.py --domain db`, `uv run python tools/check_docs_japanese.py`
  (all pass).

## Completion criteria

- The paragraph states who owns the step transaction, when the ledger row is written,
  how foreign keys are switched and restored, the verification/postcondition order, and
  the CLI database-file option; all docs checkers pass.

## Out of Scope

- Runner/CLI implementation (procedures 01, 03), `db_07` section 11 stale claim (Plan
  UNK-04, separate Issue if the owner wants it).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-084956 | 20261102-085027 | Migration guarantees paragraph expanded: per-step transaction ownership, ledger-in-transaction, foreign-key switch/check/restore, pre-commit/postcondition order, CLI rehearsal option |
| 3 | Run the documentation checkers named in the Validation plan | Completed | — | 20261102-085027 | check_docs_quality/structure/content_policy Pass; check_docs_consistency --domain db Pass; check_docs_japanese Pass |

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
- **Requirement ID**: `REQ-007` (documentation describes actual transaction behavior
  and the CLI option)
- **Source issue**: issues/20261101-133004_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-133244_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-075324
- **Related target files**: docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md