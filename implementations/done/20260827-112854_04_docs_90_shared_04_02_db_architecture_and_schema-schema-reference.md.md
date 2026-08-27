## Goal

Remove the stale `embedding_dims`-config-key claim (2 occurrences) in
`docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md` (REQ-004),
per `plans/20260826-151220_plan.md`.

## Scope

- In scope: both occurrences of the sqlite-vec virtual-table description
  (verified at lines 22 and 45 as of 2026-08-27).
- Out of scope: any other content in this document.

## Assumptions

- The embedding dimension is a fixed code constant
  (`scripts/db/store_protocols.py::get_embedding_dims()`, currently 1024), not
  read from an `embedding_dims` config key — re-verified 2026-08-27, no such key
  exists in `config/agent.toml`/`config/ingester.toml`.

## Design decisions

- Both occurrences share identical wording (a repeated schema description,
  likely for two different tables/sections using the same sqlite-vec pattern) —
  apply the same correction to both, per REQ-004's sourcing rule.

## Alternatives considered

- Editing only one occurrence and leaving the other as a cross-reference to the
  first was considered — acceptable if it reduces duplication, but the simpler,
  safer approach (correcting both occurrences identically, matching this
  document's existing repeated-description style) is chosen to avoid introducing
  a new cross-reference structure not already used in this document.

## Implementation
### Target file
`docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md`

### Procedure
1. Re-confirm current line numbers for both occurrences immediately before
   editing (verified at lines 22 and 45 as of 2026-08-27).
2. Rewrite both occurrences per Method/Details.
3. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment`
   (verify correct `--domain` for this file) and confirm no new warning/error.

### Method
Direct text edits (Edit tool, `replace_all` may apply if both occurrences are
character-for-character identical) — two occurrences of the same sentence.

### Details
Current text (verified 2026-08-27, both lines 22 and 45, identical):
```
sqlite-vec virtual table for vector similarity search. Stores float32
little-endian BLOB. chunk_id INTEGER PRIMARY KEY, embedding FLOAT[DIMS] where
DIMS replaced at runtime from embedding_dims config (default 384).
```
Replace both occurrences with:
```
sqlite-vec virtual table for vector similarity search. Stores float32
little-endian BLOB. chunk_id INTEGER PRIMARY KEY, embedding FLOAT[DIMS] where
DIMS is `scripts/db/store_protocols.py::get_embedding_dims()`, a fixed
code-level constant (not a config key).
```
Confirm both occurrences are indeed character-for-character identical before
using a single `replace_all` edit — if their surrounding context differs (e.g.
one describes `rag.sqlite`'s chunks table, the other `session.sqlite`'s
memories table), adjust each occurrence's wording independently to preserve any
table-specific context.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Two-occurrence text revert via `git diff`/`git checkout -- <path>`;
  independent of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md` | Manual diff | `git diff <path>` | No config-key claim remains in either occurrence |
| `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment` (verify correct domain first) | No new warning/error beyond baseline |

## Completion criteria

- Neither occurrence states `embedding_dims` is a config key.

## Out of scope

- Any other content in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers for both occurrences | Completed | — | — | Verified at lines 22 and 45 |
| 2 | Rewrite both occurrences | Completed | — | — | Both occurrences updated; no config-key claim remains |
| 3 | Run `check_docs_consistency.py` | Completed | — | — | Pre-existing warnings only; no new findings |

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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20260821_10_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-151220_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112854
- **Related target files**: `docs/90_shared_04_02_db_architecture_and_schema-schema-reference.md`
