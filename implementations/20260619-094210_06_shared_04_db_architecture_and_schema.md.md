# Implementation: Update db/ Directory Listing to Show Three-File Split

## Goal

The `db/` directory structure in `docs/06_shared_04_db_architecture_and_schema.md` currently shows a single `store.py` ("Protocol definitions + SQLite implementations"). The actual codebase has three files: `store_protocols.py`, `store_impl.py`, and `store.py` (re-export stub). Update the listing to match reality.

## Scope

- `docs/06_shared_04_db_architecture_and_schema.md` — change the `db/` directory listing (line 20) to show the three-file split

Out of scope:
- Code changes
- Any other section of the doc

## Assumptions

1. Files confirmed present: `scripts/db/store.py`, `scripts/db/store_impl.py`, `scripts/db/store_protocols.py`.
2. `store.py` is a re-export stub (verify by reading it briefly before editing).
3. `store_protocols.py` contains Protocol definitions; `store_impl.py` contains SQLite implementations.
4. The listing uses a fixed-width `├──` format; alignment with existing entries must be preserved.

## Implementation

### Target file

`docs/06_shared_04_db_architecture_and_schema.md`

### Procedure

1. Verify the role of each file by reading the module docstrings.
2. Replace line 20 with three lines covering `store_protocols.py`, `store_impl.py`, and `store.py`.

### Method

In-place edit of the fenced code block (lines 16–24). Replace one `├──` line with three `├──` lines. Adjust the final `└──` entry if `store.py` becomes the last alphabetical entry or keep existing order.

### Details

**Current (line 20):**
```
├── store.py           Protocol definitions + SQLite implementations
```

**Replace with (insert after line 19, before `maintenance.py`):**
```
├── store_protocols.py Protocol definitions (MemoryDeleteStore, VectorStore, …)
├── store_impl.py      SQLite implementations of store protocols
├── store.py           Re-export stub — public API surface for db.store imports
```

Verify that line ordering matches the actual filesystem sort order. If `store_protocols.py` / `store_impl.py` should come after `helper.py` and `create_schema.py` alphabetically, adjust accordingly.

**Also update the DESIGN-01 reference in this file if present** (check with `grep -n "DESIGN-01"` — likely none).

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| File existence | `ls scripts/db/store*.py` | 3 files confirmed |
| Manual review | Read the updated listing | three-file split is clear and descriptions match file purpose |
