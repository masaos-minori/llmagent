## Goal
Update `tests/db/test_db_store_impl.py` to pass `chunk_type`/`source_file` explicitly
on every `chunk_insert()` call, matching the removed defaults in
`store_protocols.py`/`store_impl.py`.

## Scope
- In scope: `tests/db/test_db_store_impl.py` only.
- Out of scope: `store_protocols.py`/`store_impl.py` production code (own documents).

## Assumptions
- Confirmed 4 `chunk_insert()` call sites lacking explicit `chunk_type`/`source_file`
  by reading the file directly:
  - line 126: `store.chunk_insert(doc_id, 0, "first chunk content", None)`
  - line 128: `store.chunk_insert(doc_id, 1, "second chunk content", "normalized")`
  - line 134 (`test_chunk_insert_stores_chunk_type_and_source_file`): already passes
    `chunk_type="code", source_file="foo.py"` explicitly — **no change needed here**
    (the plan's Affected-areas table listed this line among the ones needing an edit;
    verified it already supplies both args).
  - line 147 (`test_chunk_insert_defaults_to_empty_strings`): `store.chunk_insert(doc_id,
    0, "content")` — this test's own name and purpose (verifying the *default*
    resolves to `""`) is invalidated once the default is removed; it must be rewritten
    or removed, not just have arguments added.
- **Correction from adversarial review, 2026-08-21:** the plan's Affected-areas
  entry listed "lines 126, 128, 134, 147" as needing the same treatment; line 134
  already conforms and needs no change, and line 147's test needs to change its
  *assertion intent* (no default exists anymore), not just gain two extra arguments.
  This nuance was not present in the plan text — recorded here for the implementer.

## Design decisions
- For line 126/128: add explicit `chunk_type="", source_file=""` (or a more meaningful
  non-empty value if the test's intent benefits from it) to keep those two tests
  (`test_chunk_insert_increments_count`) focused on count behavior, not on
  chunk_type/source_file semantics.
- For line 147 (`test_chunk_insert_defaults_to_empty_strings`): rename and rewrite as a
  test that `chunk_insert()` now requires both arguments — either assert a `TypeError`
  is raised when called without them (mirroring the removed-default contract), or
  delete the test if the requirement document's Tests section does not call for a
  "still defaults" regression test (it should not, since defaults are being removed by
  design).

## Alternatives considered
- Leaving `test_chunk_insert_defaults_to_empty_strings` unchanged and just adding the
  two now-required arguments to its `chunk_insert()` call — rejected: this would
  silently repurpose a test that documents "no default" as if nothing changed, losing
  the coverage that a call *without* these args now fails; per the plan's intent
  (removing permissive defaults must be verified, not just accommodated), a positive
  test that omission now raises is more valuable.

## Implementation
### Target file
`tests/db/test_db_store_impl.py`

### Procedure
1. Line 126: `store.chunk_insert(doc_id, 0, "first chunk content", None, chunk_type="",
   source_file="")`.
2. Line 128: `store.chunk_insert(doc_id, 1, "second chunk content", "normalized",
   chunk_type="", source_file="")`.
3. Line 134 area (`test_chunk_insert_stores_chunk_type_and_source_file`): no change.
4. Line 147 (`test_chunk_insert_defaults_to_empty_strings`): replace with a test named
   e.g. `test_chunk_insert_requires_chunk_type_and_source_file` asserting
   `store.chunk_insert(doc_id, 0, "content")` raises `TypeError` (missing required
   positional/keyword arguments).

### Method
- Keep using the existing `_make_doc_db()` helper and `SQLiteDocumentStore` fixture
  pattern already present in this file; no new test infrastructure needed.

### Details
- Run `rg -n "chunk_insert(" tests/db/test_db_store_impl.py` at implementation time to
  re-confirm no additional call site was missed beyond the 4 already identified.

## Compatibility considerations
N/A — test-only file.

## Security considerations
N/A.

## Rollback considerations
- Revert together with `store_protocols.py`/`store_impl.py` as one unit.

## Validation plan
- `uv run pytest tests/db/test_db_store_impl.py -v` — all calls pass both args
  explicitly; omission-raises test passes; signatures match between protocol and
  implementation.

## Out of scope
- Any other test file in `tests/db/`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260820-094150_plan.md
- Source implementation procedure: N/A
- Generated at: 20260821-123341
- Related target files: test_db_store_impl.py
