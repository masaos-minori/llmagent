## Goal

Remove the stale `embedding_dims`-as-configurable-key claim in
`docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` (REQ-004),
per `plans/20260826-151220_plan.md`.

## Scope

- In scope: the `DbConfig` description paragraph (verified at line 43 as of
  2026-08-27) — the `embedding_dims` field mention and its `__post_init__`
  validation mention only.
- Out of scope: every other field description in the same paragraph
  (`rag_db_path`, `session_db_path`, etc. — all still accurate); any other
  section of this document.

## Assumptions

- `DbConfig` (`scripts/db/config.py:22-32`, re-verified 2026-08-27) has no
  `embedding_dims` field — its actual fields are `rag_db_path`,
  `session_db_path`, `workflow_db_path`, `eventbus_db_path`, `sqlite_vec_so`,
  `sqlite_timeout`, `sqlite_busy_timeout_ms`. `embedding_dims` does not exist on
  this dataclass at all, nor is it validated in `__post_init__`.
- `config/agent.toml`/`config/ingester.toml` have no `embedding_dims` key
  (re-verified 2026-08-27).
- The embedding dimension is a fixed code constant,
  `scripts/db/store_protocols.py::QWEN3_EMBEDDING_DIMS` (= 1024), returned by
  `get_embedding_dims()`.

## Design decisions

- Remove the `embedding_dims` field mention from the `DbConfig` field list and
  its `__post_init__` validation mention entirely (it is not merely stale-valued,
  it is fabricated — no such field or validation exists).
- Add, in its place or nearby, a brief statement that the embedding dimension is
  sourced from `scripts/db/store_protocols.py::get_embedding_dims()`, a fixed
  code constant — per this Plan's Design section's chosen pattern (name the
  single source of truth rather than restating a number).

## Alternatives considered

- Changing "384" to "1024" in place was considered and rejected — the field
  itself does not exist on `DbConfig`; correcting only the number would still
  leave the false claim that this is a `DbConfig` field.

## Implementation
### Target file
`docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`

### Procedure
1. Re-confirm the current line number for the `DbConfig` description paragraph
   immediately before editing (verified at line 43 as of 2026-08-27).
2. Remove the `embedding_dims (embedding vector dimension default 384)` field
   mention and the `embedding_dims >= 1` validation mention from the paragraph.
3. Add a brief cross-reference to `get_embedding_dims()` as the actual source of
   the embedding dimension.
4. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment`
   (this file's domain per `docs/00_index.md`'s task mapping — verify the
   correct `--domain` value before running, since this file may fall under
   `deployment` or another domain grouping) and confirm no new warning/error
   beyond the recorded baseline (4 warnings for `deployment`).

### Method
Direct text edit (Edit tool) — remove two fabricated-field mentions from one
paragraph, add one replacement sentence.

### Details
Current text (verified 2026-08-27, line 43, excerpted):
```
...Frozen dataclass for DB configuration. `rag_db_path` (path to `rag.sqlite`),
`session_db_path` (path to `session.sqlite`), `workflow_db_path` (default
`/opt/llm/db/workflow.sqlite`), `eventbus_db_path` (default
`/opt/llm/db/eventbus.sqlite`), `sqlite_vec_so` (path to `vec0.so`, empty = vec
extension not needed), `sqlite_timeout` (sqlite3.connect() timeout seconds >= 1),
`sqlite_busy_timeout_ms` (PRAGMA busy_timeout ms default 30000), `embedding_dims`
(embedding vector dimension default 384). `__post_init__` validates all path
fields non-empty, `sqlite_timeout` >= 1, `embedding_dims` >= 1, parent
directories exist (DB files themselves created on first open)...
```
Remove `, \`embedding_dims\` (embedding vector dimension default 384)` from the
field list, and `, \`embedding_dims\` >= 1` from the `__post_init__` validation
list. The embedding dimension is a fixed code constant
(`scripts/db/store_protocols.py::get_embedding_dims()`), not a `DbConfig` field —
add a short sentence stating this, near the paragraph, if the surrounding prose
does not already make this clear elsewhere in the document.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-paragraph text revert via `git diff`/`git checkout -- <path>`;
  independent of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` | Manual diff | `git diff <path>` | No config-key claim remains |
| `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment` (verify correct domain first) | No new warning/error beyond baseline |

## Completion criteria

- No statement remains that `embedding_dims` is a `DbConfig` field or a
  configurable key.

## Out of scope

- Every other field description in the same paragraph.
- Any other section of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Completed | — | — | Verified at line 43 |
| 2 | Remove fabricated field/validation mentions | Completed | — | — | Both `embedding_dims` references removed from DbConfig description |
| 3 | Add source-of-truth cross-reference | Completed | — | — | Added reference to `scripts/db/store_protocols.py::get_embedding_dims()` |
| 4 | Run `check_docs_consistency.py` | Completed | — | — | Pre-existing warnings only; no new findings |

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
- **Related target files**: `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`
