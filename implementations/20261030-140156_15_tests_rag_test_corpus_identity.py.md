# Implementation Procedure: `tests/rag/test_corpus_identity.py` (RAGCORPUS001 Phase 2)

**Plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` (REQ-001, REQ-007)

## Goal
New unit test module for corpus identity computation, meta-table round-trip, and
missing/unverifiable identity handling.

## Scope
- New file (verified absent 2026-10-30 against HEAD 124e340b4).
- Fixture precedent: use the temp-DB fixture pattern already used in
  `tests/db/test_rag_consistency.py` (1004 lines; read its DB-fixture helpers at
  implementation) and the schema creation path `scripts/db/create_schema.py`
  `create_rag_schema` `:81`.

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
### Test cases to land
- `test_identity_round_trip` (new): ensure → read returns identical `CorpusIdentity`;
  second `ensure` does not regenerate `corpus_id` (Assumptions `:147`).
- `test_identity_stable_across_reopen` (new): reopen the same DB file → equal identity.
- `test_missing_meta_unverified` (new): DB without the meta table (pre-migration shape)
  → `compute_identity` returns `verified=False`; `ensure_corpus_meta` returns `None`.
- `test_corrupt_meta_unverified` (new): meta row with a non-integer generation or missing
  column → `verified=False`, no exception.
- `test_bump_generation_only_after_success` (new): bump increments once; a bump against
  a corrupt meta leaves the previous generation and marks unverified (Assumptions `:151`).
- `test_version_constants_present` (new): identity carries
  `NORMALIZATION_VERSION`/`CHUNKING_POLICY_VERSION` values (doc 01).

1. Create the module; no marks beyond the repo default test conventions.

## Compatibility considerations
**Dependencies**: upstream: docs 01, 02
**Blocks**: none (leaves docs 16/17/18 the integration coverage)

## Security considerations
- No new security surface beyond what the Source plan records.

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- `uv run pytest tests/rag/test_corpus_identity.py`

## Completion criteria
- All six tests green against doc 01's module; deterministic (no wall-clock dependence).

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
| `20261030-140156_01_scripts_rag_corpus_identity.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `test_identity_round_trip`, `test_identity_stable_across_reopen`,
  `test_missing_meta_unverified`, `test_corrupt_meta_unverified`,
  `test_bump_generation_only_after_success`, `test_version_constants_present`
  (Test cases section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-007
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 15
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `tests/rag/test_corpus_identity.py`
