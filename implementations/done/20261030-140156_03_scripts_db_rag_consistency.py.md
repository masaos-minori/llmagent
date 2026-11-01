# Implementation Procedure: `scripts/db/rag_consistency.py` (RAGCORPUS001 Phase 1)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-005, REQ-006)

## Goal
Replace `[WARNING]`/`[CRITICAL]` text-prefix severity with a structured severity
classification (severity enum + repair action) attached to findings; keep the prefixes
only inside human-readable message bodies.

## Scope
- `check_rag_consistency` `:19`, `is_consistent` `:108`, `summarize_issues` `:295`.
- Issue builders and their severity text (all anchor-verified): `_fts_gap_issue` `:156`
  (WARNING text at `:162`), `_fts_orphan_issue` `:167` (CRITICAL `:175`),
  `_orphan_vec_issue` `:181` (CRITICAL `:189`), `_vector_mismatch_issue` `:194`
  (WARNING `:202`), `_documents_without_chunks_issue` `:207` (WARNING `:213`),
  `_chunks_without_vec_issue` `:218` (CRITICAL `:224`), `_duplicate_chunk_index_issue`
  `:229` (CRITICAL `:238`), `_url_mismatch_issue` `:243` (WARNING `:248`).
- `_ConsistencyCheck` `:254` — check registry the new fatal checks must join.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- Classification is fixed in code, not configuration (AC-4): degraded/repairable =
  FTS gap, FTS orphan, vector count mismatch, orphan vector rows, chunks without vector
  rows, URL-level inconsistency, documents without chunks; fatal = duplicate
  `chunk_index`, FK inconsistency, embedding-dimension mismatch, unknown schema,
  unverifiable corpus generation (REQ-005). The last three counters come from doc 04;
  "unverifiable corpus generation" maps to doc 04's corpus-meta check.
- Each issue builder returns a `ConsistencyFinding` (defined in doc 05) instead of a
  bare string; the severity enum value is chosen here, the `[WARNING]`/`[CRITICAL]`
  prefix remains inside the message text for humans and for `summarize_issues` output
  compatibility.
- `check_rag_consistency` `:19` and `summarize_issues` `:295` keep their signatures for
  existing callers; findings flow through the report fields added in doc 05.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Convert each `_*_issue` builder to construct `ConsistencyFinding` with its fixed
   severity and a named repair action (e.g. FTS gap → `rebuild_fts`, orphan vector rows
   → `rebuild_vec`, duplicate chunk_index → restore-from-backup text). Repair-action
   names must match the maintenance API verbs (`rebuild_fts` `:31`, `rebuild_vec` `:66`,
   `recover` `:56` in `rag_maintenance_service.py`).
2. Add the three new fatal-check finding builders consuming doc 04's counters, wired
   into `_ConsistencyCheck` `:254`.
3. Do not remove count fields or change counting SQL; severity is additive metadata.

## Compatibility considerations
**Dependencies**:
- Upstream: doc 05 (`RagConsistencyReport` severity fields), doc 04 (new fatal-check
**Blocks**: docs 06, 07, 19

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert this file together with its paired test rows in the same commit; the change is additive and gated by the plan's checkers.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py` (doc 19). Existing 1004-line suite
  must stay green — message text is unchanged, so text assertions remain valid.

## Completion criteria
- Every finding carries a structured severity and repair action; no caller needs to text
  parse prefixes; the five fatal classes are detectable end-to-end.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | 20261031-065123 | 20261031-065123 |  |
| 2 | Apply the Implementation procedure | Completed | 20261031-065123 | 20261031-065123 |  |
| 3 | Run the Validation plan gates | Completed | 20261031-065123 | 20261031-065123 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_04_scripts_db_rag_consistency_queries.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-140156_05_scripts_db_models.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- No new top-level constructs in this file (findings type and enum are doc 05's);
  severity assignment changes are in-place conversions.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 03
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `scripts/db/rag_consistency.py`