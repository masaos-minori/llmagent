## Goal

Update the migration-contract passages of `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` to match the post-dbmigsafe001 behavior: full refusal-reason table, durable archive + audit artifact, WAL-consistent dry-run, ledger ordering key, CLI version semantics, and the current migration chains.

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`.

## Assumptions

- This document is executed after procedures 01-05 and 07-08 land; it documents their shipped behavior, not intent.
- Adversarial recheck 20261105 found the doc text stale in three places it must correct: section 8a documents the chain as `0 -> 1 -> 2 -> 3` while the registry holds four steps (`0 -> 1 -> 2 -> 3 -> 4`, `workflow_attempt_lease` included); section 8b documents one eventbus step (`eventbus_ledger_baseline`) while the registry holds two (`eventbus_dlq_outbox` included); the "Migration guarantees" verification-order paragraph still presents the postcondition as the integrity check (it becomes observational).
- `docs/00_index.md` task-scope mapping for migration/operations points at this file (Plan Documentation Impact); no other doc row exists in the Plan's frozen table.

## Design decisions

- Update in place within the existing section structure (8a, 8b, "Migration guarantees"); do not restructure the document or renumber sections.
- Document the refusal-reason set as a table keyed by `MigrationRefusalReason` value with its CLI exit class, including the documented `PRAGMA wal_checkpoint(FULL)` behavior (busy source → `checkpoint_busy` refusal) and the UNK-02 note that FULL-checkpoint conservatism is implemented behavior pending an ADR.

## Alternatives considered

- Moving migration contracts into a new dedicated doc: rejected — the Plan's frozen target table names this file, and `docs/00_index.md`'s mapping already points here.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
### Procedure

1. Section 8a: extend the chain description to `0 -> 1 -> 2 -> 3 -> 4` naming the `workflow_attempt_lease` step; state that integrity checks run pre-commit (`pre_commit_verification`) and a failed check rolls the step back.
2. Section 8b: document both registered eventbus steps (`eventbus_ledger_baseline`, `eventbus_dlq_outbox`) and the same pre-commit verification contract.
3. "Migration guarantees": rewrite the verification-order sentence (preconditions → per-step transaction → `pre_commit_verification` pre-commit → commit; postconditions observational only); add the durable-archive paragraph (SQLite backup API, operator-supplied `--archive-dir`, audit artifact fields `archive_path`/`sha256`/`source_db`/`source_version`/`created_at`/`retention_status` with `retention_status: "unset"` pending the retention policy, nothing pruned automatically); add WAL-consistent dry-run semantics (backup-API snapshot, WAL-committed rows visible, live file byte-identical); add the ledger ordering key (`rowid`/`LedgerRow.seq` append order); add the refusal-reason table with exit classes (`EXIT_OK` 0, `EXIT_GATE_FAILURE` 1, `EXIT_REFUSAL` 2) covering `no_verified_backup`, `checkpoint_busy`, `in_memory_database`, `no_archive_target`, `archive_failure`; state the unattended EventBus startup path runs archive-less until a retention policy exists (owner decision 20261105).
4. CLI semantics: document `--status` fields — `user_version=` integer migration code and `marker=` semantic `workflow_schema_version` string (workflow domain; eventbus prints `user_version=` only) — and `--apply` requiring `--archive-dir` on both CLIs.

### Method

- Prose edits against the anchors listed in Assumptions; keep existing cross-links (`db_07` section 11, `eventbus_06`) intact.

### Details

- N/A: prose-only document.

## Compatibility considerations

- Documentation-only; must not claim behavior that the code rows have not shipped — execute after code procedures complete.

## Security considerations

- Document that archive files are full database copies and their location/retention is an operator responsibility (no automatic pruning).

## Rollback considerations

- Single-commit revert of the doc.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain db` — no findings (Plan Validation plan; corrected 20261105 to the actual checker set).
- `uv run python tools/check_doc_links.py` and `uv run python tools/check_stale_docs.py` per `routing.md` Tools.

## Completion criteria

- The three stale passages named in Assumptions are corrected; AC-007 doc half: both status fields are defined in the docs; the refusal-reason table matches the shipped enum.

## Out of Scope

- Any other `docs/41_db/` file; ADR authoring for UNK-01/UNK-02/UNK-03 (owner tasks, not docs edits here).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement steps 1-4 (sections 8a, 8b, guarantees, CLI semantics) | Pending | — | — | |
| 2 | No tests in this document (docs row) | Pending | — | — | |
| 3 | Run the doc checkers listed in Validation plan | Pending | — | — | |
| 4 | Docs update is this document | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-005, REQ-006 (documentation half), REQ-007 (context)
- **Source issue**: issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-233415_dbmigsafe001_durable-verified-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-170302
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
