# Implementation Procedure — scripts/shared/schema_fingerprint.py

## Goal

Compare an FTS5 virtual table by its normalized stored DDL text instead of by name, so a plain
table named `chunks_fts` or a drifted tokenizer or column list is refused (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001 (definition comparison, not names). Acceptance criterion: AC-2.

## Assumptions
- Full form: this is a shared-module contract change that can alter the accept/refuse outcome for
  every store that uses the fingerprint.
- The module must not load an extension, so the FTS5 comparison is text equality on the stored
  `sqlite_master` statement, not a `PRAGMA` read.
- Only FTS5 moves to text comparison; `vec0` stays name-only (Plan default, UNK-01).
- The rag store is the only other store with an FTS5 virtual table, so its fixtures can change
  outcome; the deploy pre-flight is run against a scratch database before any production store is
  touched.

## Design decisions
- A virtual statement is recognized by its module (`USING fts5(`); FTS5 entries carry the normalized
  statement text as their shape, while extension-backed virtual tables keep the name-only marker.
- Normalization reuses `_normalize_ddl` (line 63), so formatting differences do not change the
  comparison result.

## Alternatives considered
- Compare every virtual table through `PRAGMA`: rejected, because it requires loading the extension
  module in a leaf module (Plan Design decision).

## Implementation
### Target file
`scripts/shared/schema_fingerprint.py`

### Procedure
- Extend `_strip_virtual_statements` (line 92) to return, for FTS5 statements, the normalized
  statement text alongside the base name; extension-backed statements keep only the name.
- In `expected_fingerprint` (line 265), build the FTS5 entry from that normalized text instead of
  the empty marker from `_name_only`.
- In `_raise_first_difference` (line 279), limit the name-only skip at lines 308-310 to
  extension-backed entries, so an FTS5 entry compares its text against the live statement.
- Use `definition` as the refusal part label for an FTS5 entry, so the message reads
  `mdq.sqlite.chunks_fts: definition differ from the canonical schema` rather than reporting a
  statement text as a column difference.
- Keep `_is_name_only` (line 182), `_name_only_names` (line 191), and `_drop_shadow_tables`
  (line 196) as they are; the shadow-table omission is unchanged.

### Method
- The live side already records the stored statement text for a virtual table, so the comparison is
  normalized-text equality between the canonical statement and the stored statement.
- The module docstring (lines 12-20) is updated to state the split: FTS5 by normalized text,
  extension-backed virtual tables by name.

### Details
- A plain table named `chunks_fts` produces a real entry with columns, so it no longer matches an
  FTS5 entry that carries statement text (AC-1).
- Trigger bodies are unaffected: the existing `_triggers` comparison already compares normalized SQL
  for non-virtual tables.

### Companion test files
- `tests/shared/test_schema_fingerprint.py`
  - Procedure: split `test_rag_virtual_bases_are_name_only` (line 171) so `chunks_fts` is asserted
    through the text comparison and `chunks_vec` stays name-only; add the plain-table case and the
    tokenizer, column, and option drift cases.
  - Validation: `uv run pytest tests/shared/test_schema_fingerprint.py` — a plain table named
    `chunks_fts` is refused and `vec0` stays name-only.

## Compatibility considerations
- Consumers are `scripts/mcp_servers/mdq/db_schema.py`, the `scripts/db/` schema entry points,
  `scripts/eventbus/schema.py`, and `deploy/init_db.sh`; only the rag store has an FTS5 virtual table,
  so its previously accepted shape can now be refused (Plan Risk).
- `tests/rag/test_fts_sync.py` builds its own FTS5 schema and does not call the fingerprint, so it is
  unaffected.

## Security considerations
- N/A: comparison logic only; refusal messages continue to quote schema structure and never row
  content.

## Rollback considerations
- Reverting restores the name-only treatment; a database that was refused under the new comparison is
  accepted again, so no data change is involved. A store that was recreated in the meantime is not
  restored by the revert.

## Validation plan
- `uv run pytest tests/shared/test_schema_fingerprint.py`
- Scratch rag pre-flight: apply the canonical rag DDL to a scratch database and run the gate; never
  against a database under `/opt/llm/`.
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- A plain table named `chunks_fts` and a drifted FTS5 definition are refused with the
  archive-and-recreate message; `vec0` and the shadow-table omission behave as before (AC-2).

## Out of Scope
- The mdq readiness probe and the health vocabulary (row 4); the canonical DDL text itself (row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/shared/test_schema_fingerprint.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Scratch rag pre-flight included |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (row 17) |

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
- **Requirement ID**: REQ-001 (readiness and the fingerprint compare the stored FTS5 definition)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `scripts/shared/schema_fingerprint.py`, `tests/shared/test_schema_fingerprint.py`
