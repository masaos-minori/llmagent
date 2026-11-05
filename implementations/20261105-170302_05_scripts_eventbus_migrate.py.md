## Goal

Mirror the workflow CLI changes in the EventBus CLI (`scripts/eventbus/migrate.py`): require an explicit durable archive target for `--apply`, map the gate-family refusal reasons to the exit-code classes, and document the `--status` field semantics (REQ-001, REQ-004, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/eventbus/migrate.py`. Related tests live in procedure document 08 (`tests/eventbus/test_eventbus_migrations.py`).

## Assumptions

- Runner API after procedure 01: `MigrationRunner.apply(..., archive_dir: Path | None = None)`.
- Exit constants `EXIT_OK`/`EXIT_GATE_FAILURE`/`EXIT_REFUSAL` exist at L35-L38; today only `NO_VERIFIED_BACKUP` maps to `EXIT_GATE_FAILURE` (Plan evidence, verified 20261105).
- The EventBus CLI `--status` prints only `user_version=` (verified 20261105: no `marker=` line in this module — the EventBus domain has no semantic string version store; the workflow domain's `marker=` field is documented in procedure 04).
- Size gate: file is 5043 B against 24576 B; ample headroom.
- `deploy.sh`/`init_db.sh` do not invoke `migrate.py --apply` — re-confirmed in step 3 (Plan Phase 8); record the grep result.

## Design decisions

- `--archive-dir` validated in code, not argparse `required=True` (same decision as procedure 04): a missing value for `--apply` logs an explicit error and returns `EXIT_REFUSAL` (exit 2), matching the Plan Validation plan. Dry-run never archives.
- Same gate-family set as the workflow CLI: `{NO_VERIFIED_BACKUP, CHECKPOINT_BUSY, NO_ARCHIVE_TARGET, ARCHIVE_FAILURE}` → `EXIT_GATE_FAILURE`; all other reasons → `EXIT_REFUSAL`.

## Alternatives considered

- Defaulting the archive directory from the EventBus data dir: rejected — no location is inferred in code (issue AI-instruction; Plan Design 1).

## Implementation
### Target file
`scripts/eventbus/migrate.py`
### Procedure

1. Add `parser.add_argument("--archive-dir", ...)` (`type=Path`, `default=None`) near the other parser options (after the mode group, L80-L90 area).
2. In the `--apply` branch: if `args.archive_dir is None`, log the requirement and return `EXIT_REFUSAL`; otherwise pass `archive_dir=args.archive_dir` to `runner.apply(conn, path, verify_backup, ...)` (near L130). The `--dry-run` call (near L123) is unchanged.
3. Extend the `MigrationRefusalError` handler (near L137-L144) with the gate-family set membership → `EXIT_GATE_FAILURE`; keep `EXIT_REFUSAL` otherwise; update the exit-code class comment.
4. Extend `--status` help/docstring (L61-L70 area): `user_version=` is the integer migration code (PRAGMA); state that the EventBus domain has no semantic string marker, unlike the workflow domain.

### Method

- Config-boundary change only; archive mechanics live in the runner (procedure 01).

### Details

- The startup path (`scripts/eventbus/schema.py`) is untouched (runner-optional decision, Plan Blocker Log step 3).

## Compatibility considerations

- Breaking CLI change: `--apply` without `--archive-dir` now exits 2. Operator docs updated in procedure 09.
- `--dry-run`/`--status` behavior unchanged.

## Security considerations

- Archive location is operator-supplied only.

## Rollback considerations

- Single-commit revert; the flag is additive.

## Validation plan

- CLI coverage in `tests/eventbus/test_eventbus_migrations.py` (procedure 08): `--apply` without `--archive-dir` → `EXIT_REFUSAL`; gate-family reasons → `EXIT_GATE_FAILURE`.
- Operational check: repo-wide grep confirming `deploy.sh`/`init_db.sh` never call `migrate.py --apply`; record result.
- `rules/toolchain.md` sequence incl. `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-001 (CLI half), AC-005, AC-007 (eventbus field semantics documented).

## Out of Scope

- Runner mechanics (procedure 01), registry callback move (procedure 03), tests (procedure 08), docs (procedure 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement steps 1-4 (flag, validation, forwarding, exit mapping, status semantics) | Pending | — | — | |
| 2 | CLI tests carried by procedure 08 (no tests in this document) | Pending | — | — | |
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
- **Related target files**: `scripts/eventbus/migrate.py`, `tests/eventbus/test_eventbus_migrations.py`
