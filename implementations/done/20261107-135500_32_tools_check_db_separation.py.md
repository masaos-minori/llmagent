## Goal

- Align the `tools/check_db_separation.py` TABLE_OWNERSHIP inventory with the post-cutover databases: after sibling documents 01-09 delete the migration modules and marker-table DDL, no module creates `schema_migrations` or `workflow_schema_version`, so the checker's own inventory-drift gate reports 3 violations and fails CI (amended plan row: REQ-001/REQ-002/REQ-006 fallout).

## Scope
**Release unit**: current-schema-only-cutover

- Inventory frozensets in this file only; the checker's logic stays untouched (its docstring contract: "Update together with the ADR").

## Assumptions

- The violation direction confirmed on 2026-11-07: `[table-ownership] <db>.sqlite no longer creates inventory table ...` for workflow `schema_migrations`/`workflow_schema_version` and eventbus `schema_migrations` — i.e. the inventory is stale, not the DDL (verified: 3 violations after siblings 01-09 landed).
- `rules/env.md` and the ADR (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, rewritten by sibling 13) describe the marker-free 4-DB layout this inventory must mirror.

## Design decisions

- Remove the three marker entries from the owning frozensets rather than keep them as allowances: `check_inventory()` compares the inventory against CREATE statements scraped from the DDL sources, so stale entries are drift by the checker's own definition, and a permissive-but-stale set would hide future marker reintroduction.

## Alternatives considered

- Keeping the entries so legacy databases still "pass" the checker: rejected — the checker never opens live databases; it audits source DDL, and its docstring requires the inventory to track the ADR. The startup gates, not this inventory, handle legacy DB files (AC-004).

## Implementation
### Target file
`tools/check_db_separation.py`

### Procedure
1. Apply the inventory edit; confirm the checker exits clean.
2. Run the checker and its companion tests green.

### Method
- Delete `"workflow_schema_version",` and `"schema_migrations",` from the `"workflow"` frozenset (lines 78-79).
- Delete `"schema_migrations",` from the `"eventbus"` frozenset (line 87).
- Leave `check_inventory()`, `_CREATE_RE` scraping, `VEC_TABLES`, and the REFERENCES scan unchanged.

### Companion test files
- `tests/tools/test_check_db_separation.py`
  - Procedure: no marker references exist in this file (verified 2026-11-07 by grep); run unchanged as the regression gate. If any fixture pins the workflow/eventbus table sets, align it with the marker-free inventory.
  - Validation: `uv run python tools/check_db_separation.py` exits 0 with "No violations found" and `uv run pytest tests/tools/test_check_db_separation.py` green.

## Compatibility considerations

- The checker is CI-only (no runtime imports); no signature or output-format change beyond fewer inventory names.

## Security considerations

- N/A: static source audit only.

## Rollback considerations

- Revert the commit restores the three inventory entries (single-commit change within the release unit).

## Validation plan

- `uv run python tools/check_db_separation.py` — 0 violations (post siblings 01-09).
- `uv run pytest tests/tools/test_check_db_separation.py` — green.
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- The checker exits 0 against the post-cutover DDL sources, and its inventory names exactly the tables the current schema creates (AC-001, AC-002, AC-007).

## Out of Scope

- Startup-gate behavior on live legacy databases — siblings 06, 07, 10, 12.
- ADR body rewrite — sibling 13 (done).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the three marker entries from TABLE_OWNERSHIP (Plan Phase 3) | Completed | — | 20261107-130500 | Release unit "current-schema-only-cutover" Three marker entries removed from TABLE_OWNERSHIP (workflow: workflow_schema_version+schema_migrations; eventbus: schema_migrations). Checker: 'No violations found'. tests/tools/test_check_db_separation.py 10 passed. Plan amended (fallout rows) and procedure doc generated 20261107-135500. marker ownership entries removed; checker now clean |
| 2 | Run `check_db_separation.py` and `tests/tools/test_check_db_separation.py` green | Completed | — | 20261107-130500 | Three marker entries removed from TABLE_OWNERSHIP (workflow: workflow_schema_version+schema_migrations; eventbus: schema_migrations). Checker: 'No violations found'. tests/tools/test_check_db_separation.py 10 passed. Plan amended (fallout rows) and procedure doc generated 20261107-135500. checker reports no violations; 10 tools tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Completed | — | 20261107-134719 | end-of-unit validation sequence green |

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
- **Requirement ID**: REQ-001 (migration modules deleted), REQ-002 (marker tables deleted), REQ-006 (environment/DB-separation rule consistency)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md (amended 2026-11-07, fallout row)
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-135500
- **Related target files**: `tools/check_db_separation.py`, `tests/tools/test_check_db_separation.py`