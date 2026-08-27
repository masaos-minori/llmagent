## Goal

Remove the stale `embedding_dims`-config-key claim in
`docs/03_rag_01_system_overview.md` (REQ-004), per
`plans/20260826-151220_plan.md`.

## Scope

- In scope: the "Embedding Dimension" table row (verified at line 155 as of
  2026-08-27) only.
- Out of scope: any other row of the same table; any other content in this
  document.

## Assumptions

- The embedding dimension is a fixed code-level constant
  (`scripts/db/store_protocols.py::get_embedding_dims()`, currently 1024), not a
  `config/agent.toml` key — re-verified 2026-08-27, `embedding_dims` does not
  exist in that file.

## Design decisions

- Replace the "384 (production, via `embedding_dims` key in
  `config/agent.toml`)" claim with a statement naming the fixed code constant as
  the source, per REQ-004's sourcing rule.

## Alternatives considered

- N/A: single table-cell correction.

## Implementation
### Target file
`docs/03_rag_01_system_overview.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 155 as of 2026-08-27).
2. Rewrite the "Embedding Dimension" row per Method/Details.
3. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` and
   confirm no new warning/error beyond the recorded baseline (17 warnings, none
   embedding-related).

### Method
Direct text edit (Edit tool) — one table row.

### Details
Current row (verified 2026-08-27, line 155):
```
| Embedding Dimension | 384 (production, via `embedding_dims` key in `config/agent.toml`). No dataclass default; defined in config file only. float32 little-endian BLOB | `config/agent.toml` — See `03_rag_90` DOC-03 |
```
Replace with:
```
| Embedding Dimension | Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`), not config-driven. float32 little-endian BLOB | `scripts/db/store_protocols.py` |
```
Verify whether the third column's `03_rag_90` DOC-03 cross-reference (likely
`RAG-003`/`RAG-004`-style known-issue entries) should be updated or removed —
read that cross-referenced entry in `docs/03_rag_90_inconsistencies_and_known_issues.md`
before finalizing, since it may itself need updating if it describes this same
stale claim (out of scope for this item if so — flag as `Plan Gap` if a code
change to that separate doc's entry appears necessary and is not already covered
by this Plan's Requirements).

## Compatibility considerations

- Documentation-only; no runtime behavior, schema, or public interface is
  affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-row text revert via `git diff`/`git checkout -- <path>`; independent
  of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_01_system_overview.md` | Manual diff | `git diff <path>` | No config-key claim remains |
| `docs/03_rag_01_system_overview.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` | No new warning/error beyond the 17-warning baseline |

## Completion criteria

- The "Embedding Dimension" row no longer states `embedding_dims` is a
  `config/agent.toml` key.

## Out of scope

- Any other row of the same table.
- Any other content in this document.
- `docs/03_rag_90_inconsistencies_and_known_issues.md`'s cross-referenced entry
  (separate document, not a target file of this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Pending | — | — | |
| 2 | Rewrite the "Embedding Dimension" row | Pending | — | — | |
| 3 | Check the `03_rag_90` cross-reference for related staleness (informational) | Pending | — | — | |
| 4 | Run `check_docs_consistency.py --domain rag` | Pending | — | — | |

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
- **Related target files**: `docs/03_rag_01_system_overview.md`
