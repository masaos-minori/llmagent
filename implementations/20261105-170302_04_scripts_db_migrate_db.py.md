## Goal

Make the workflow CLI (`scripts/db/migrate_db.py`) supply the operator's durable archive target for `--apply`, map the new gate-family refusal reasons to the documented exit-code classes, and pin the `--status` field semantics (`user_version` integer code, `marker` semantic string) in help text (REQ-001, REQ-004, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/db/migrate_db.py`. CLI-level tests are carried by procedure document 07.

## Assumptions

- Runner API after procedure 01: `MigrationRunner.apply(..., archive_dir: Path | None = None)`; CLI passes it only for `--apply`.
- Exit-code classes already exist (verified 20261105): `EXIT_OK = 0`, `EXIT_GATE_FAILURE = 1`, `EXIT_REFUSAL = 2` (module comment near L34-L38).
- Gate-family reasons after procedure 01: `NO_VERIFIED_BACKUP`, `CHECKPOINT_BUSY`, `NO_ARCHIVE_TARGET`, `ARCHIVE_FAILURE`. All other reasons stay in the refusal class.
- Size gate: file is 6954 B against 24576 B; ample headroom.
- `deploy.sh`/`init_db.sh` do not invoke `migrate_db.py --apply` — must be re-confirmed in step 3 (Plan Phase 8) before finishing; record the grep result in Execution Status notes.

## Design decisions

- `--archive-dir` is a parser option validated in code, not an argparse `required=True`: it is required only for `--apply`; a missing value there logs an explicit error and returns `EXIT_REFUSAL` (exit 2), matching the Plan Validation plan's expected boundary. Dry-run and status never require it and never archive.
- No default archive location is inferred in code (issue AI-instruction; Plan Design 1).

## Alternatives considered

- `argparse required=True` on `--archive-dir`: rejected — it would make the flag required for `--dry-run`/`--status` too.

## Implementation
### Target file
`scripts/db/migrate_db.py`
### Procedure

1. Add `parser.add_argument("--archive-dir", ...)` (type `Path`, `default=None`, help text stating it is required for `--apply` and is the durable pre-migration archive location).
2. In the `--apply` branch (before `runner.apply`, near L167): if `args.archive_dir is None`, call `parser.error("--apply requires --archive-dir")`.
3. Pass `archive_dir=args.archive_dir` to the `runner.apply(conn, path, verify_backup, ...)` call; the `--dry-run` call site (near L160) stays unchanged.
4. Extend the `MigrationRefusalError` handler (near L174-L178): return `EXIT_GATE_FAILURE` for the gate-family set `{NO_VERIFIED_BACKUP, CHECKPOINT_BUSY, NO_ARCHIVE_TARGET, ARCHIVE_FAILURE}`; keep `EXIT_REFUSAL` for all other reasons. Update the exit-code class comment to name the classes.
5. Extend `--status` help text and `_cmd_status` docstring (near L66-L82): `user_version=` is the integer migration code (PRAGMA), `marker=` is the semantic `workflow_schema_version` string; both names are stable machine-readable fields.

### Method

- Config-boundary change only: the operator supplies the path, the CLI validates and forwards it; all archive mechanics live in the runner (procedure 01).

### Details

- Keep the existing `EXIT_*` constants; the handler becomes a set membership test instead of the single `NO_VERIFIED_BACKUP` comparison.

## Compatibility considerations

- Breaking CLI change: existing `--apply` invocations without `--archive-dir` now fail with exit 2. Operator-facing docs are updated in procedure 09; UNK-04 (live invocation inventory) is confirmed by the deploy/init grep in step 3.
- `--dry-run` and `--status` behavior is unchanged.

## Security considerations

- Archive location is operator-supplied only; the CLI never infers or defaults it.

## Rollback considerations

- Single-commit revert; the flag is additive so the previous CLI contract is fully restored.

## Validation plan

- CLI tests in `tests/db/test_migrations_workflow.py` (procedure 07): `--apply` without `--archive-dir` → exit 2 with message; gate-family refusals → exit 1; other refusals → exit 2; `--help` shows `--archive-dir`.
- Operational check: `grep -n 'migrate_db' deploy.sh init_db.sh setup_services.sh` (or equivalent repo-wide grep) confirming no `--apply` invocation; record result.
- `rules/toolchain.md` sequence incl. `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-001 (CLI half): every `--apply` run names an archive target; AC-005: gate-family and refusal classes are distinguishable at the exit-code boundary; AC-007: help/docstring define both status fields.

## Out of Scope

- Archive mechanics and audit artifact (procedure 01), eventbus CLI (procedure 05), tests (procedure 07), docs (procedure 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement steps 1-5 (flag, validation, forwarding, exit mapping, status semantics) | Pending | — | — | |
| 2 | CLI tests carried by procedure 07 (no tests in this document) | Pending | — | — | |
| 3 | Operational dependency check (deploy.sh/init_db.sh grep, Plan Phase 8) + `rules/toolchain.md` sequence | Pending | — | — | |
| 4 | No docs change in this document (docs are carried by doc 09) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-004, REQ-006
- **Source issue**: issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-233415_dbmigsafe001_durable-verified-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-170302
- **Related target files**: `scripts/db/migrate_db.py`, `tests/db/test_migrations_workflow.py`
