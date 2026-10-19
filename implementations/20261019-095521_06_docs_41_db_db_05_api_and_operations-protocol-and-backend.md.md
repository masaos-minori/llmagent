## Goal
Make the Memory description state that the session connection loads sqlite-vec and that a vector write is part of the same transaction (`REQ-002`).

## Scope
- The `MemoryStore` paragraph: the `add` sentence and the `count_vec` sentence.

## Assumptions
- The scope rule is the one in the amended ADR-008 (sqlite-vec loaded by default for `rag` and `session`).

## Design decisions
- Change only the sentence(s) that state the scope or default; keep the surrounding structure and links.

## Alternatives considered
N/A: wording change only.

## Implementation
### Target file
`docs/41_db/db_05_api_and_operations-protocol-and-backend.md`

### Procedure
1. Replace the passage below with the new wording using Edit.
2. Run the documentation checkers.

### Method
- Old text (exact): "`add(entry, embedding=None)` inserts into `memories` + `memories_fts`; optionally also into `memories_vec` as needed."
- New text: "`add(entry, embedding=None)` inserts into `memories` + `memories_fts`; when an embedding is supplied it also inserts into `memories_vec` in the same transaction, and a failure of that insert (for example, `vec0` not loaded) raises and rolls the whole write back instead of storing the entry without its vector row."
- Also add, after the existing `count_vec` sentence, one sentence: the `session` connection loads `vec0` by default (see the `load_vec` description in the DB overview).
- Keep the existing sentence that `count_vec()` raises `sqlite3.OperationalError` when `memories_vec` is unavailable.

### Details
- Write in English; no line numbers or concrete configuration values (`skills/DESIGN.md`).

## Compatibility considerations
N/A: wording change only; no other document restates the replaced sentence differently (see the Plan's Implementation Target Files rows for the sibling documents).

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit (documents and the `SQLiteHelper` default must be reverted together to stay consistent).

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain overview`

## Completion criteria
- The passage states that `rag` and `session` load sqlite-vec by default and `workflow` and `eventbus` do not.
- All documentation checkers pass.

## Out of scope
- Any file other than the target file
- Code, tests, or configuration changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the passage with the new wording | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools (docs quality, structure, content policy, consistency for the touched domain) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (state how Memory vector storage gets its connection)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: docs/41_db/db_05_api_and_operations-protocol-and-backend.md
