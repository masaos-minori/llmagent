# Implementation Procedure: `tests/db/test_rag_consistency.py` (RAGCORPUS001 Phase 1)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-005, REQ-006)

## Goal
Severity unit tests for every degraded class and every fatal class, including the new
checks.

## Scope
- Fake-DB fixtures: `_FakeSQLiteHelper` `:17`, `_make_rag_db` `:81`, `_insert_doc` `:89`,
  `_insert_chunk` `:99`; report helpers `_report` `:608`, `_only_issue` `:627`.
- Existing severity-adjacent classes already present (they lock today's text-prefix
  behavior and must stay green — text stays inside messages per doc 03):
  `TestRagConsistencySeverity` `:248`, `TestNewConsistencyChecks` `:458`,
  `TestNewCheckIssueDetails` `:819`, `TestIssueOrder` `:909`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Test cases to land
- `TestStructuredSeverity` (new class): per class — FTS gap, FTS orphan, vector count
  mismatch, orphan vector rows, chunks without vector rows, URL-level inconsistency,
  documents without chunks assert `severity=DEGRADED` and a non-empty `repair_action`;
  duplicate `chunk_index` asserts `severity=FATAL`.
- `TestNewFatalChecks` (new class): FK inconsistency, embedding-dimension mismatch,
  unknown schema, unverifiable corpus meta each produce exactly one FATAL finding with a
  named repair action; clean DBs produce none.
- `test_fatal_cannot_be_configured_away` (new): classification is code-fixed — assert the
  mapping table/branch, no config read (AC-4).
- Extend `TestCollectionFailureDiagnostics` `:943` region only if collection failures
  interact with findings ordering (record at implementation).

1. Append new classes after `TestIssueOrder`; reuse `_report` `:608` (it already accepts
   overrides) — extend it with the new counter fields.

## Compatibility considerations
**Dependencies**: upstream: docs 03, 04, 05
**Blocks**: none

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py`

## Completion criteria
- Every REQ-005 class has a structured severity test; the 1004-line existing suite is
  green without behavioral edits.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Completed | 20261031-074238 | 20261031-074238 | Phase 1: synthetic-report baselines set corpus_meta_verified=True so new schema_recognition/corpus_meta fatal checks stay silent on consistent reports. Folded into doc03 commit 69f36fc49; 59 tests green. |
| 2 | Apply the Implementation procedure | Completed | 20261031-074238 | 20261031-074238 | Phase 1: synthetic-report baselines set corpus_meta_verified=True so new schema_recognition/corpus_meta fatal checks stay silent on consistent reports. Folded into doc03 commit 69f36fc49; 59 tests green. |
| 3 | Run the Validation plan gates | Completed | 20261031-074238 | 20261031-074238 | Phase 1: synthetic-report baselines set corpus_meta_verified=True so new schema_recognition/corpus_meta fatal checks stay silent on consistent reports. Folded into doc03 commit 69f36fc49; 59 tests green. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_03_scripts_db_rag_consistency.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `TestStructuredSeverity`, `TestNewFatalChecks`,
  `test_fatal_cannot_be_configured_away` (Test cases section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 19
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `tests/db/test_rag_consistency.py`