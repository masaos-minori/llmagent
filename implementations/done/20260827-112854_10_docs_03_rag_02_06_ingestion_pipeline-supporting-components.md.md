## Goal

Remove the stale `embedding_dims`-config-key claim in
`docs/03_rag_02_06_ingestion_pipeline-supporting-components.md` (REQ-004), per
`plans/20260826-151220_plan.md`.

## Scope

- In scope: the `embedding_dims` table row (verified at line 52 as of
  2026-08-27) only.
- Out of scope: any other row of the same table; any other content in this
  document.

## Assumptions

- The embedding dimension is a fixed code-level constant
  (`scripts/db/store_protocols.py::get_embedding_dims()`, currently 1024), not
  configurable — re-verified 2026-08-27.

## Design decisions

- Replace the "384" value with a reference to the code constant, per REQ-004's
  sourcing rule. Preserve the row's other useful information ("Expected
  dimensions of the embedding vector; verified against API response") if still
  accurate — confirm whether the described verification-against-API-response
  behavior still exists in current source before keeping that clause; if it
  does not, note the discrepancy instead of silently keeping stale claim text.

## Alternatives considered

- N/A: single table-cell correction.

## Implementation
### Target file
`docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`

### Procedure
1. Re-confirm the current line number immediately before editing (verified at
   line 52 as of 2026-08-27).
2. Verify whether "verified against API response" still describes current
   ingester behavior (grep the ingester source for an embedding-dimension
   verification-against-response check) before keeping or removing that clause.
3. Rewrite the row per Method/Details.
4. Run `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` and
   confirm no new warning/error.

### Method
Direct text edit (Edit tool) — one table row.

### Details
Current row (verified 2026-08-27, line 52):
```
| `embedding_dims` | 384 | Expected dimensions of the embedding vector; verified against API response |
```
Replace with (adjust the third column based on step 2's verification):
```
| Embedding dimension | Fixed code-level constant (`scripts/db/store_protocols.py::get_embedding_dims()`) | Expected dimensions of the embedding vector; verified against API response |
```
If step 2 finds the "verified against API response" behavior no longer exists
or differs, replace that clause accordingly rather than leaving a second stale
claim in the same row.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface
  is affected.

## Security considerations

- N/A: no security-relevant content.

## Rollback considerations

- Single-row text revert via `git diff`/`git checkout -- <path>`; independent
  of the other 14 target files in this Plan's pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md` | Manual diff | `git diff <path>` | No config-key claim remains |
| `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md` | Doc consistency check | `.venv/bin/python3 tools/check_docs_consistency.py --domain rag` | No new warning/error beyond baseline |

## Completion criteria

- The row no longer states `embedding_dims` is a configurable key with a
  specific default value.

## Out of scope

- Any other row of the same table.
- Any other content in this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm line number | Completed | — | — | Verified at line 52 |
| 2 | Verify "verified against API response" still accurate | Completed | — | — | No such verification exists in current source; removed that clause per procedure |
| 3 | Rewrite the row | Completed | — | — | Config-key claim removed; API verification clause also removed |
| 4 | Run `check_docs_consistency.py --domain rag` | Completed | — | — | Pre-existing warnings only; no new findings |

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
- **Related target files**: `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`
