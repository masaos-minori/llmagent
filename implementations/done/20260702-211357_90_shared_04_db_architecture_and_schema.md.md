# Implementation: 90_shared_04_db_architecture_and_schema.md

## Goal

Remove all references to automatic schema migration, `ALTER TABLE`, and backward-compatible
column additions from `docs/90_shared_04_db_architecture_and_schema.md`. Replace with an
explicit DB recreation policy. Align the `documents` table description and §8 with the
no-migration stance adopted in the corresponding code changes to `schema_sql.py` and
`create_schema.py`.

## Scope

**Target file:** `docs/90_shared_04_db_architecture_and_schema.md`

**In scope:**
- §5 `documents` table: remove `(added via migrate_schema())` annotation from `chunking_strategy` row.
- §8 "Schema Generation and Migration Approach": rewrite entirely to state the DB recreation policy.
- §9a "AI Reference Guide" / §10 "Source of Truth": update the "What initializes schemas?" answer to remove migration reference.
- Add `chunk_type TEXT` and `source_file TEXT` columns to the §5 `chunks` table documentation
  (these columns now exist in `schema_sql.py` DDL after Phase 2 of the plan).

**Out of scope:**
- Changing runtime behavior of any Python module.
- Changes to `schema_sql.py` or `create_schema.py` (covered by separate implementation docs,
  already processed).
- Event Bus runtime documentation.

## Assumptions

- Phase 2 (`schema_sql.py`) and Phase 3 (`create_schema.py`) have already been implemented,
  so `chunk_type` and `source_file` are now part of the canonical DDL.
- The production DB has all `_migrate_*` column additions applied (confirmed in plan §3).
- No other section in this file contains migration-specific language beyond §5 and §8.

## Implementation

### Target file

`docs/90_shared_04_db_architecture_and_schema.md`

### Procedure

1. Open the file and read its full content to identify all occurrences of migration-related text.
2. Edit §5 `documents` table row for `chunking_strategy`: remove the parenthetical
   `(added via migrate_schema())`.
3. Edit §5 `chunks` table: add `chunk_type TEXT` and `source_file TEXT` rows after
   `normalized_content` in the column table.
4. Rewrite §8 "Schema Generation and Migration Approach" entirely.
5. Update §9a "What initializes schemas?" answer to remove migration reference.
6. Run grep to verify no stale migration wording remains.

### Method

Direct file edit using the Edit tool. Each change targets a specific section.
No code is generated; only documentation prose is modified.

### Details

#### §5 `documents` table — `chunking_strategy` row

Current text:
```
| `chunking_strategy` | TEXT | NOT NULL DEFAULT `'text'` (added via `migrate_schema()`) |
```

Replace with:
```
| `chunking_strategy` | TEXT | NOT NULL DEFAULT `'text'` |
```

#### §5 `chunks` table — add missing columns

After the `normalized_content` row, insert:
```
| `chunk_type`        | TEXT | (NULL allowed; identifies chunk category) |
| `source_file`       | TEXT | (NULL allowed; source file path for code chunks) |
```

#### §8 rewrite

Replace the current §8 block with:

```markdown
## 8. Schema Generation and Migration Approach

```python
# Initialize all schemas (rag + session + workflow + eventbus)
from db.create_schema import create_schema
create_schema()
```

- All DDL uses `IF NOT EXISTS` — idempotent; safe to run multiple times.
- **Schema migration is not supported.** When the schema changes, recreate DB files
  from the latest DDL in `schema_sql.py`.
- Existing DB updates are handled by DB recreation, not automatic migration.
- `schema_sql.py` is the canonical latest schema definition. All table columns,
  including `chunk_type`, `source_file`, and `undone`, are present in `schema_sql.py`
  DDL and require no migration helpers.
- `embedding_dims` is substituted dynamically in `_build_rag_schema_sql(dims)` and
  `_build_session_schema_sql(dims)`.

**Operational guidance:** To apply a schema change to a production deployment:
1. Archive existing DBs: `rotate_all_dbs()` from `db.maintenance`.
2. Delete the DB files at the configured paths.
3. Run `create_schema()` to initialize empty DBs from the latest DDL.

See [90_shared_05 §10](90_shared_05_db_api_and_operations.md#10-db-recreation-procedure)
for the full step-by-step command sequence.
```

#### §9a — update "What initializes schemas?" row

Current:
```
| What initializes schemas? | `create_schema()` + `init_schema()` — idempotent |
```

Replace with:
```
| What initializes schemas? | `create_schema()` — idempotent DDL-only initialization; no migration |
```

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| No stale migration wording | `grep -n "migration\|ALTER TABLE\|backward.compatible\|duplicate column\|migrate_schema\|added via migrate" docs/90_shared_04_db_architecture_and_schema.md` | Zero matches |
| `chunk_type` and `source_file` present in §5 | `grep -n "chunk_type\|source_file" docs/90_shared_04_db_architecture_and_schema.md` | Two matches in `chunks` table section |
| Docs render correctly | Manual review of §5, §8, §9a sections | Prose is coherent; no broken table formatting |
| Cross-reference to §10 is valid | Check that `90_shared_05_db_api_and_operations.md` §10 exists | Section heading present in that file |
