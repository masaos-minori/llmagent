# Implementation: Add DB Recreation Procedure to `docs/90_shared_05_db_api_and_operations.md`

## Goal

Add a new "DB Recreation (Schema Update Procedure)" section to `docs/90_shared_05_db_api_and_operations.md`
so that operators have a documented, official workflow for applying schema changes by
recreating DB files from the latest DDL.

## Scope

- `docs/90_shared_05_db_api_and_operations.md` — add a new section after existing maintenance sections
- Document `rotate_all_dbs()` archive step, manual file deletion, `create_schema()` recreation
- State explicitly that migration is unsupported and recreated DBs are empty
- Reference `common.toml` config keys for DB paths (not hardcoded paths)

Out of scope:
- `docs/90_shared_04_db_architecture_and_schema.md` (handled separately)
- Any Python source file changes
- `eventbus.sqlite` archival (not covered by `rotate_all_dbs()`)

## Assumptions

1. `rotate_all_dbs()` in `scripts/db/maintenance.py` archives `rag.sqlite`, `session.sqlite`,
   and `workflow.sqlite` via the SQLite online backup API. It does NOT archive `eventbus.sqlite`.
2. `create_schema()` in `scripts/db/create_schema.py` initializes all four DB files
   (`rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`).
3. DB paths are defined in `common.toml` keys: `rag_db_path`, `session_db_path`, `workflow_db_path`.
   Default values are `/opt/llm/db/rag.sqlite`, `/opt/llm/db/session.sqlite`, `/opt/llm/db/workflow.sqlite`.
4. The archive directory defaults to `sqlite_archive_dir` in `common.toml`
   (default: `/opt/llm/db/archive`).
5. Existing section numbering in the file uses `## N.` format (e.g., `## 9. Error Handling`).
6. The new section should be inserted between the Error Handling section and the existing
   Verification Plan section.
7. The existing "Section 10: Verification Plan" should be renumbered to "Section 11" if the
   new section is inserted as Section 10.

## Implementation

### Target file

`docs/90_shared_05_db_api_and_operations.md`

### Procedure

1. Read the full file to confirm current section numbering and identify the insertion point.
2. Locate the end of `## 9. Error Handling` section (before the `---` separator preceding
   `## 10. Verification Plan`).
3. Insert the new section as `## 10. DB Recreation (Schema Update Procedure)`.
4. Renumber the existing `## 10. Verification Plan` to `## 11. Verification Plan`.
5. Renumber the existing `## 11. AI Reference Guide` to `## 12. AI Reference Guide`.

### Method

Use the Edit tool with `old_string` / `new_string` for targeted in-place edits.
Do not rewrite the entire file.

### Details

Insert the following section between `## 9. Error Handling` and the existing `## 10. Verification Plan`:

```markdown
---

## 10. DB Recreation (Schema Update Procedure)

Schema changes require full DB recreation — incremental migration is not supported.

> **Warning:** Complete this procedure in order. Do not delete DB files before archiving.

**Step 1: Archive existing DB files**

Archive all three production DBs using the SQLite online backup API:

```bash
uv run python -c "from db.maintenance import rotate_all_dbs; rotate_all_dbs()"
```

Archived copies are stored in `sqlite_archive_dir` (configured in `common.toml`;
default: `/opt/llm/db/archive`). `rotate_all_dbs()` covers `rag.sqlite`,
`session.sqlite`, and `workflow.sqlite`. `eventbus.sqlite` is NOT archived by this
function and must be handled separately if required.

**Step 2: Delete existing DB files**

```bash
rm /opt/llm/db/rag.sqlite /opt/llm/db/session.sqlite /opt/llm/db/workflow.sqlite
```

DB paths are resolved from `common.toml` keys:
- `rag_db_path` (default: `/opt/llm/db/rag.sqlite`)
- `session_db_path` (default: `/opt/llm/db/session.sqlite`)
- `workflow_db_path` (default: `/opt/llm/db/workflow.sqlite`)

**Step 3: Recreate DB schemas**

```bash
uv run python -c "from db.create_schema import create_schema; create_schema()"
```

`create_schema()` initializes all four DB files using the latest DDL:
`rag.sqlite`, `session.sqlite`, `workflow.sqlite`, and `eventbus.sqlite`.

**Important notes:**
- Recreated DBs are empty — existing records are NOT migrated automatically.
- All DDL uses `IF NOT EXISTS` — `create_schema()` is safe to run multiple times.
- To recreate a single DB, use individual functions: `create_rag_schema()`,
  `create_session_schema()`, or `create_workflow_schema()`.
```

After inserting the new section, update the subsequent section numbers:
- `## 10. Verification Plan` → `## 11. Verification Plan`
- `## 11. AI Reference Guide` → `## 12. AI Reference Guide`
- Update any internal anchor links referencing old section numbers if present.

## Validation Plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| New section presence | Manual review | Read `docs/90_shared_05_db_api_and_operations.md` | Section `## 10. DB Recreation` is present with all three steps |
| `rotate_all_dbs()` accuracy | Code cross-check | Read `scripts/db/maintenance.py` | Confirms rag + session + workflow are archived; eventbus is not |
| `create_schema()` accuracy | Code cross-check | Read `scripts/db/create_schema.py` | Confirms all four DBs are created |
| DB path references | Config cross-check | Read `config/common.toml` | Paths match documented defaults |
| Section numbering | Manual review | Read the full file | No duplicate or skipped section numbers |
| Warning block | Manual review | Read the file | Warning to archive before delete is present |
