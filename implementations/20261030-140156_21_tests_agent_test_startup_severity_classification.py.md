# Implementation Procedure: `tests/agent/test_startup_severity_classification.py` (RAGCORPUS001 Phase 1)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-005, REQ-006)

## Goal
Extend the severity-classification coverage file with the RAG findings stream.

## Scope
- `_make_startup_ctx` `:27`, `_run_check_services` `:40`,
  `TestCheckServicesSeverityClassification` `:114` with per-subsystem patterns
  (mcp_auth fatal `:128`, readiness `:169-208`, routing_drift `:281-349`).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Test cases to land
- Extend `TestCheckServicesSeverityClassification` in place (this file's convention is
  one subsystem group per block):
  - `test_rag_consistency_fatal_when_duplicate_chunk_index` (new)
  - `test_rag_consistency_warning_when_fts_gap_only` (new)
  - `test_rag_consistency_unverified_warning_on_check_failure` (new)

1. Add the three tests as a RAG group at the end of the class body, following the
   routing_drift group's stubbing style (`:281-349`).
2. Keep the file's strictness-matrix framing: RAG severity is code-fixed, so unlike
   routing_drift there is no strict/non-strict pair — assert fatal regardless (AC-4).

## Compatibility considerations
**Dependencies**: upstream: docs 05, 06, 07 (same contracts as doc 20)
**Blocks**: none

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/agent/test_startup_severity_classification.py`

## Completion criteria
- RAG joins the other subsystems in the classification matrix; existing 562-line suite
  green.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_05_scripts_db_models.py.md` | 1 (dependency) | Procedure | Pending | — | — |
| `20261030-140156_20_tests_agent_test_startup.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `test_rag_consistency_fatal_when_duplicate_chunk_index`,
  `test_rag_consistency_warning_when_fts_gap_only`,
  `test_rag_consistency_unverified_warning_on_check_failure` (Test cases section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 21
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `tests/agent/test_startup_severity_classification.py`
