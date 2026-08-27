## Goal

Remove the stale `embedding_dims`-config-key claim in
`docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md` (REQ-004),
per `plans/20260826-151220_plan.md`.

## Scope

- In scope: the `get_embedding_dims`/`get_embedding_bytes`/
  `validate_embedding_blob` description paragraph (verified at line 7 as of
  2026-08-27) only.
- Out of scope: any other content in this document.

## Assumptions

- `get_embedding_dims()` (`scripts/db/store_protocols.py`, re-verified
  2026-08-27) reads a fixed code constant (`QWEN3_EMBEDDING_DIMS = 1024`), not
  `agent.toml::embedding_dims` — this doc's parenthetical "(reads
  `agent.toml::embedding_dims`, default 384)" is the specific false claim to
  correct; the function names themselves (`get_embedding_dims`,
  `get_embedding_bytes`, `validate_embedding_blob`) and their described
  signatures/behavior are otherwise accurate and unaffected.

## Design decisions

- Correct only the parenthetical describing `get_embedding_dims()`'s data
  source — leave `get_embedding_bytes()`'s description (`dims * 4 for float32`)
  and `validate_embedding_blob()`'s description unchanged, since neither claims
  a config-key source.

## Alternatives considered

- N/A: single narrow clause correction within an otherwise-accurate sentence.

## Implementation
### Target file
`docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 7 as of 2026-08-27).
2. Rewrite the `get_embedding_dims()` parenthetical per Method/Details.
3. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment`
   (verify correct `--domain`) and confirm no new warning/error.

### Method
Direct text edit (Edit tool) — one parenthetical clause within one sentence.

### Details
Current text (verified 2026-08-27, line 7, excerpted):
```
...Embedding helpers: `from db.store import get_embedding_dims,
get_embedding_bytes, validate_embedding_blob`; `dims = get_embedding_dims()`
(reads `agent.toml::embedding_dims`, default 384); `nbytes =
get_embedding_bytes()` (dims * 4 for float32); `validate_embedding_blob(blob)`
(raises `TypeError` if not bytes, `ValueError` if wrong size).
```
Replace the parenthetical `(reads \`agent.toml::embedding_dims\`, default 384)`
with `(returns a fixed code-level constant,
\`scripts/db/store_protocols.py::QWEN3_EMBEDDING_DIMS\`, not config-driven)`.
Leave the rest of the sentence (the import statement, `get_embedding_bytes()`'s
and `validate_embedding_blob()`'s descriptions) unchanged.

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-clause text revert via `git diff`/`git checkout -- <path>`;
  independent of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md` | Manual diff | `git diff <path>` | No config-key claim remains |
| `docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain deployment` (verify correct domain first) | No new warning/error beyond baseline |

## Completion criteria

- `get_embedding_dims()`'s description no longer claims it reads
  `agent.toml::embedding_dims`.

## Out of scope

- Any other content in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Completed | — | — | Verified at line 7 |
| 2 | Rewrite the `get_embedding_dims()` parenthetical | Completed | — | — | False claim "(reads `agent.toml::embedding_dims`, default 384)" replaced with reference to fixed constant |
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
- **Related target files**: `docs/90_shared_05_02_db_api_and_operations-protocol-and-backend.md`
