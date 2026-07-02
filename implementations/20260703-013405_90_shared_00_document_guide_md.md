# Implementation: docs/90_shared_00_document-guide.md — Remove Migration References

**Plan source:** `plans/20260702-201024_plan.md` (Phase 6)
**Target file:** `docs/90_shared_00_document-guide.md`

---

## Goal

Confirm there are no references to incremental migration, `ALTER TABLE`, or backward-compatible schema additions in `docs/90_shared_00_document-guide.md`, and remove any that exist.

---

## Scope

**In:**
- Scan full content of `docs/90_shared_00_document-guide.md` for migration-related terms
- Remove or rewrite any reference to `migrate_schema`, `ALTER TABLE`, `backward-compatible` additions, or incremental migration as a supported path

**Out:**
- Changes to section structure or non-migration content
- Changes to other doc files (covered by Phases 4–5)

---

## Assumptions

1. Initial scan found no direct migration references in this file; this phase is a confirmation step.
2. If any migration-adjacent wording exists (e.g., "schema updates are applied incrementally"), it must be updated to reflect the DB recreation policy.

---

## Implementation

### Target file

`docs/90_shared_00_document-guide.md`

### Procedure

1. Read the full content of `docs/90_shared_00_document-guide.md`.
2. Search for: `migrate_schema`, `ALTER TABLE`, `backward-compatible`, `duplicate column`, `incremental`.
3. If found: remove or replace with language consistent with the no-migration policy ("schema changes require DB recreation").
4. If not found: no changes needed; document as confirmed clean.

### Method

Read tool to inspect; Edit tool for targeted replacement if any matches found.

### Details

The no-migration policy statement to use if replacement is needed:
> "Schema migration is not supported. When the schema changes, recreate DB files from the latest DDL using `rotate_all_dbs()` for archival and `create_schema()` for recreation."

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Grep check | `grep -n "migration\|ALTER TABLE\|backward.compatible\|migrate_schema" docs/90_shared_00_document-guide.md` | 0 matches (or only intentional policy statements) |
| Full docs grep | `grep -R "migration\|ALTER TABLE\|backward.compatible\|duplicate column\|migrate_schema" docs/ scripts/ -n` | Any remaining occurrence is consistent with no-migration policy |
