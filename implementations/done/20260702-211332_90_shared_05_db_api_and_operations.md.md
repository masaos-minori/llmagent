# Implementation: docs/90_shared_05_db_api_and_operations.md

## Goal

Update the `chunk_insert` API documentation to reflect the extended signature that now includes `chunk_type` and `source_file` parameters.

## Scope

- Target: `docs/90_shared_05_db_api_and_operations.md`
- Update the `chunk_insert` method signature shown around line 152
- Update the description around line 160 to note the two new fields
- No other sections changed

## Assumptions

1. The doc file contains a code block or signature listing for `chunk_insert` near line 152.
2. The description text near line 160 describes the method's behavior and the columns written.
3. This is a documentation-only change; no code is generated.

## Implementation

### Target file

`docs/90_shared_05_db_api_and_operations.md`

### Procedure

1. Locate the `chunk_insert` signature block (around line 152). Update it to include `chunk_type` and `source_file`.
2. Locate the description text (around line 160). Add a note that both `chunk_type` and `source_file` are forwarded to the `chunks` table.

### Method

**Signature block** — replace the old signature:

```python
def chunk_insert(
    self,
    doc_id: int,
    chunk_index: int,
    content: str,
    normalized: str | None,
) -> int
```

With the updated signature:

```python
def chunk_insert(
    self,
    doc_id: int,
    chunk_index: int,
    content: str,
    normalized: str | None,
    chunk_type: str = "",
    source_file: str = "",
) -> int
```

**Description text** — append to the existing description (near line 160):

> `chunk_type` and `source_file` default to `""` and are written directly to the corresponding columns in the `chunks` table. Existing callers that pass only the first four arguments are unaffected.

### Details

- Preserve all surrounding text, headings, and table formatting.
- Do not add or remove sections outside of the `chunk_insert` entry.

## Validation plan

| Check | Command | Target |
|---|---|---|
| File readable | `cat docs/90_shared_05_db_api_and_operations.md | grep chunk_insert` | Shows updated signature with `chunk_type` and `source_file` |
| No broken links | Manual review | No `[[broken]]` internal links introduced |
