## Goal

Remove the stale `embedding_dims`-config-key claim (3 occurrences) in
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
(REQ-004), per `plans/20260826-151220_plan.md`.

## Scope

- In scope: the three occurrences (verified at lines 34, 67, 73 as of
  2026-08-27).
- Out of scope: any other content in this document (e.g. WAL mode, busy_timeout,
  schema initializer descriptions on the same lines — all still accurate).

## Assumptions

- The embedding dimension is a fixed code constant
  (`scripts/db/store_protocols.py::get_embedding_dims()`, currently 1024), not
  `agent.toml::embedding_dims` (that key does not exist — re-verified 2026-08-27).

## Design decisions

- Each of the three occurrences is embedded in a longer sentence describing
  other, still-accurate facts (WAL mode, busy_timeout, schema location) — edit
  only the `embedding_dims`/"384" clause within each sentence, leaving the rest
  of each sentence unchanged.

## Alternatives considered

- N/A: three independent, narrowly-scoped clause edits within otherwise-accurate
  sentences; no broader restructuring is warranted.

## Implementation
### Target file
`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Re-confirm current line numbers for all three occurrences immediately before
   editing (verified at lines 34, 67, 73 as of 2026-08-27).
2. Rewrite each occurrence's `embedding_dims`/"384" clause per Method/Details.
3. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment`
   (verify correct `--domain`) and confirm no new warning/error.

### Method
Direct text edits (Edit tool) — three narrow clause replacements within three
different sentences.

### Details
Current text (verified 2026-08-27):
- Line 34: `- \`embedding_dims\` is dynamically replaced from config at runtime
  (default 384).`
- Line 67 (excerpt within a longer sentence): `...default embedding dimension
  384 (\`agent.toml::embedding_dims\`)...`
- Line 73 (excerpt within a longer sentence): `...embedding dimension set via
  \`agent.toml::embedding_dims\` (default 384)...`

Replace line 34 with:
```
- Embedding dimension is a fixed code-level constant returned by
  `scripts/db/store_protocols.py::get_embedding_dims()`, not a config key.
```
Replace line 67's clause `default embedding dimension 384
(\`agent.toml::embedding_dims\`)` with `embedding dimension fixed by
\`scripts/db/store_protocols.py::get_embedding_dims()\` (not config-driven)`,
keeping the rest of that sentence (SQLite version, sqlite-vec path, WAL mode,
busy_timeout, float format, single-node note) unchanged.

Replace line 73's clause `embedding dimension set via
\`agent.toml::embedding_dims\` (default 384)` with `embedding dimension fixed
by \`scripts/db/store_protocols.py::get_embedding_dims()\``, keeping the rest of
that sentence (schema locations, SQLiteHelper workflow.sqlite note, schema
initializer note, trigger references) unchanged.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Three-clause text revert via `git diff`/`git checkout -- <path>`; independent
  of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` | Manual diff | `git diff <path>` | No config-key claim remains in any of the 3 occurrences |
| `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment` (verify correct domain first) | No new warning/error beyond baseline |

## Completion criteria

- None of the three occurrences states `embedding_dims` is a config key.

## Out of scope

- Any other content in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line numbers for all 3 occurrences | Pending | — | — | |
| 2 | Rewrite all 3 occurrences | Pending | — | — | |
| 3 | Run `check_docs_consistency.py` | Pending | — | — | |

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
- **Related target files**: `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
