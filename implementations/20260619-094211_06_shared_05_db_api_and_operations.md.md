# Implementation: Add Extensibility Rationale to MemoryDeleteStore Section

## Goal

Add one explanatory sentence to the `MemoryDeleteStore` / `SQLiteMemoryDeleteStore` section in `docs/06_shared_05_db_api_and_operations.md` so developers understand why the Protocol/implementation split exists.

## Scope

- `docs/06_shared_05_db_api_and_operations.md` — insert one sentence in the `### MemoryDeleteStore / SQLiteMemoryDeleteStore` subsection (§4, around line 160–173)

Out of scope:
- Code changes
- Other protocol sections

## Assumptions

1. The current section (lines 160–172) has usage example and bullet points but no extensibility rationale.
2. The plan's prescribed sentence: "`MemoryDeleteStore` is a Protocol (structural type) that exists to preserve the option of a non-SQLite backend in the future. Today, `SQLiteMemoryDeleteStore` is the sole implementation."
3. The DESIGN-01 link at line 172 ("See [06_shared_90 DESIGN-01]...") should be updated to note DESIGN-01 is now RESOLVED once step 3 is complete.
4. Insert point: after the bullet list (line 172) and before the `---` separator (line 173).

## Implementation

### Target file

`docs/06_shared_05_db_api_and_operations.md`

### Procedure

1. Locate the `### MemoryDeleteStore / SQLiteMemoryDeleteStore` subsection (around line 160).
2. After the existing bullet list ending at line 172, insert the extensibility rationale sentence.

### Method

Single sentence insertion after the bullet list. No structural changes.

### Details

**Insertion point:** after line 172 (`- See [06_shared_90 DESIGN-01](...)`), before the `---` separator.

Insert:
```markdown
- `MemoryDeleteStore` is a Protocol (structural type) that exists to preserve the option of a non-SQLite backend in the future. Today, `SQLiteMemoryDeleteStore` is the sole implementation.
```

Alternatively, if a prose paragraph is preferred over a bullet:
```markdown

> `MemoryDeleteStore` is a Protocol (structural type) that exists to preserve the option of a non-SQLite backend in the future. Today, `SQLiteMemoryDeleteStore` is the sole implementation.
```

Use whichever format matches the doc's existing style in this section.

Once DESIGN-01 is marked RESOLVED (step 3), consider updating line 172 to:
```markdown
- See [06_shared_90 DESIGN-01](06_shared_90_inconsistencies_and_known_issues.md) — resolved; extensibility rationale documented here.
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read the MemoryDeleteStore section end-to-end | "why Protocol exists" is explicit without reading source |
