# Implementation: 90_shared_05_db_api_and_operations.md

## Goal

Scan `docs/90_shared_05_db_api_and_operations.md` for any remaining references to
`ALTER TABLE`, `migrate_schema`, or backward-compatible migration language, and remove or
rewrite them. Verify that §10 "DB Recreation Procedure" is accurate and consistent with the
no-migration policy. The document currently contains a §10 section about DB recreation; this
pass confirms it is complete and adds any missing details.

## Scope

**Target file:** `docs/90_shared_05_db_api_and_operations.md`

**In scope:**
- Scan entire document for migration-related language: `ALTER TABLE`, `migrate_schema`,
  `backward-compatible`, `duplicate column`, `_migrate_`.
- Review §10 "DB Recreation Procedure" for completeness: archive → delete → recreate.
- Confirm §10 "Verification Plan" (`python -c` example) does not reference migration steps.
- Update §10 "DB Recreation Procedure" if `rotate_all_dbs()` or individual `rotate_*`
  functions need clarification about `eventbus.sqlite`.

**Out of scope:**
- SQLiteHelper API documentation (§2).
- Protocol definitions (§3).
- Maintenance function signatures (§7).
- Event Bus runtime.

## Assumptions

- The current document already contains a "DB Recreation Procedure" section (§10) with
  archive/delete/recreate steps.
- The document does not reference `_migrate_*` functions or `ALTER TABLE` in any existing
  section (plan §5 states "current content is clean").
- `rotate_all_dbs()` archives rag, session, and workflow DBs; `eventbus.sqlite` is not
  included in the rotation (it is recreated separately by `create_schema()`).

## Implementation

### Target file

`docs/90_shared_05_db_api_and_operations.md`

### Procedure

1. Read the full document.
2. Run grep for migration-related terms. If any are found, rewrite the offending sentence
   to align with the no-migration policy.
3. Review §10 "DB Recreation Procedure":
   - Confirm the three steps (archive, delete, recreate) are present.
   - Confirm the note about `eventbus.sqlite` being initialized by `create_schema()` is present.
   - Add a note clarifying that `rotate_all_dbs()` does not archive `eventbus.sqlite`
     (it is lightweight and recreated from scratch if needed).
4. Review §10 "Verification Plan": confirm the `python -c` example does not reference
   migration functions.
5. Add or confirm a note: "Schema migration is not supported. Use DB recreation for schema
   changes." — either as a standalone sentence or inline with the recreation procedure.

### Method

Direct file edit using the Edit tool. Each change is targeted; no large section rewrites
are expected since the document is already largely aligned.

### Details

#### Grep for stale wording (verification step, also guides editing)

```bash
grep -n "migration\|ALTER TABLE\|backward.compatible\|duplicate column\|migrate_schema\|_migrate_" \
    docs/90_shared_05_db_api_and_operations.md
```

If no results: document is clean; proceed to §10 review only.

#### §10 "DB Recreation Procedure" — expected content

Confirm presence of:
- **Step 1 Archive:** `rotate_all_dbs()` command.
- **Step 2 Delete:** `rm` command for rag, session, workflow DB files.
- **Step 3 Recreate:** `create_schema()` command.
- **Note about eventbus.sqlite:** `create_schema()` initializes eventbus.sqlite if not present.
- **Note about individual recreation:** `create_rag_schema()`, `create_session_schema()`,
  `create_workflow_schema()` for partial recreation.

If any of these are absent, add them.

#### §10 "Verification Plan" — confirm cleanliness

The `python -c` example should only call `create_schema()` (no migration functions).
Current expected content: `from db.create_schema import create_schema; create_schema()`.
No change expected.

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| No stale migration wording | `grep -n "migration\|ALTER TABLE\|backward.compatible\|duplicate column\|migrate_schema\|_migrate_" docs/90_shared_05_db_api_and_operations.md` | Zero matches (or only intentional "no migration" policy text) |
| §10 recreation procedure present | `grep -n "rotate_all_dbs\|create_schema\|Step 1\|Step 2\|Step 3" docs/90_shared_05_db_api_and_operations.md` | All three steps visible |
| Verification plan clean | `grep -n "_migrate_\|migrate_schema" docs/90_shared_05_db_api_and_operations.md` | Zero matches |
