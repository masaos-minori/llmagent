## Goal
Record in `docs/24_eventbus/eventbus_07_configuration-and-operations.md` the end condition of the legacy offset import, the retention rule for the old offset files, the owner, and a read-only check an operator runs to see whether any consumer still needs the files (REQ-001, REQ-002).

## Scope
- In: one new section `Legacy Offset Files` between `Consumer ID Stability` and `Delivery Operations`.
- Out: the Configuration Fields table, any code or config, the other two documents (rows 02 and 03), deleting any file.

## Assumptions
- Verified 2026-10-21: `config/eventbus.toml` sets `offsets_dir = "/opt/llm/offsets"`; that directory is empty on the supported host.
- The supported deployment and baseline are those of the owner decision of 2026-10-21 (Plan Background; database document section 8e).
- The service never modifies or deletes the offset files; the retention rule adds an operator rule only.
- The document is 11331 B, well under the 24576 B limit.

## Design decisions
- The check uses two read-only commands (`ls -A` and a `mode=ro` query) so an operator can run it with the service up.
- The section states the end condition in terms of the supported baseline instead of a date.

## Alternatives considered
N/A: the Plan fixes this document as the operator-facing home of the end condition and retention rule.

## Implementation
### Target file
`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure
1. Insert the section below after the `Consumer ID Stability` section (after the line ending "...offset persistence details.") and its trailing `---`, before `## Delivery Operations`.
2. Run the documentation checkers.

### Method
Section text (English; adjust only to satisfy the checkers):

````markdown
## Legacy Offset Files

`offsets_dir` (`config/eventbus.toml`) holds the file-based offsets that predate the `consumer_offsets` table. The service reads them only in the startup import (`migrate_legacy_offsets()`); it never writes, modifies, or deletes them, and no runtime path resumes from them. `consumer_offsets` in `eventbus.sqlite` is the only resume source.

- **Owner:** the EventBus service owns the import; the deployment operator decides whether the files are archived or deleted.
- **Retention:** the files are not needed once every consumer they name has a `consumer_offsets` row. After that an operator may archive or delete them; the service does not.
- **End condition:** the import may be removed when no supported deployment keeps files in `offsets_dir`. The supported baseline is in [DB migration and scaling](../41_db/db_03_architecture_and_schema-migration-and-scaling.md) (section 8e).

To check that no consumer still needs the files, run these read-only commands. The first lists the files (an empty result means nothing is left to import); the second lists the stored offsets. A `.map` companion file holds the original consumer ID of its offset file, and that ID must appear in the second result before its files are removed.

```bash
ls -A <offsets_dir>
sqlite3 "file:<eventbus_db_path>?mode=ro" "SELECT consumer_id, offset FROM consumer_offsets;"
```

The open decisions about the import (collision handling, a completion marker, commit behavior) are in [Legacy Offset Import: Open Decisions](eventbus_05_dlq_offsets_and_delivery_semantics.md#legacy-offset-import-open-decisions).
````

### Details
- Heading anchor `#legacy-offset-files` is linked from rows 02 and 03; keep the heading text exact.
- Do not write the word "Needs confirmation" (inventory checker).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: the commands are read-only and print file names and offsets only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py` (links must resolve), `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_docs_consistency.py --domain overview`, `check_needs_confirmation_inventory.py`.
- Run the two commands read-only against the supported host and confirm the first prints nothing and the second prints no row.

## Completion criteria
- The section states the end condition, retention rule, and owner (AC-1) and the operator check (AC-2).
- The listed checkers pass (AC-5).

## Out of Scope
- Adding a deletion tool or a completion marker; changing `offsets_dir`; editing other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `Legacy Offset Files` section (REQ-001, REQ-002) | Completed | 20261021-101811 | 20261021-101846 | Changed: docs/24_eventbus/eventbus_07_configuration-and-operations.md (new section Legacy Offset Files) |
| 2 | Run the documentation checkers and the read-only commands (REQ-005) | Completed | 20261021-101811 | 20261021-101846 | check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese, check_docs_consistency --domain overview, check_needs_confirmation_inventory all exit 0; read-only commands on the supported host: offsets_dir empty, consumer_offsets 0 rows. Docs-only: no test run. |

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
- **Requirement ID**: `REQ-001` (end condition, retention, owner), `REQ-002` (operator check), `REQ-005` (checkers pass)
- **Source issue**: `issues/20261020-122817_compat002_define-the-end-condition-and-retention-policy-for-the-eventbus-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-233641_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-101632
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`