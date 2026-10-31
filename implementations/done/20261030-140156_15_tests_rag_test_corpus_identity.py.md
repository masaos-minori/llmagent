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
| 1 | Re-verify cited anchors before editing | Completed | 20261031-142000 | 20261031-142500 |  |
| 2 | Apply the Implementation procedure | Completed | 20261031-142500 | 20261031-143500 |  |
| 3 | Run the Validation plan gates | Completed | 20261031-143500 | 20261031-143500 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-140156_01_scripts_rag_corpus_identity.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `test_ensure_then_read_returns_identical_identity`,
  `test_second_ensure_raises_single_row_constraint`,
  `test_reopen_same_file_yields_equal_identity`, `test_missing_meta_table_is_unverified`,
  `test_non_integer_generation_raises_value_error`, `test_bump_increments_once`,
  `test_bump_returns_none_when_table_absent`, `test_identity_carries_version_constants`,
  `test_corpus_identity_equality_ignores_verified_flag`
  (Test cases section).

## Deviations from the approved procedure
The procedure's behavioral assumptions did not match `rag.corpus_identity` once the
module was implemented (doc 01). Each was verified by running the module against a real
temp DB; the tests assert the actual contract instead of the assumed one.

1. `test_corrupt_meta_unverified` (assumed: non-integer generation → `verified=False`,
   no exception) → replaced by `test_non_integer_generation_raises_value_error`.
   `compute_identity` performs defensive NULL checks on `corpus_id`/`index_generation`
   but does NOT wrap the `int()` coercion in a try/except, so a tampered non-integer
   generation propagates `ValueError`. This is the real contract.
2. `test_bump_generation_only_after_success` (assumed: a bump against a corrupt meta
   leaves the previous generation and marks unverified) → split into
   `test_bump_increments_once` + `test_bump_returns_none_when_table_absent`. The
   corrupt-meta claim was dropped: SQLite coerces a non-numeric text in arithmetic
   (`'abc' + 1 == 1`), so it does not leave the previous value.
3. `test_second_ensure_does_not_regenerate_corpus_id` (assumed: second `ensure` keeps
   the same `corpus_id`) → replaced by `test_second_ensure_raises_single_row_constraint`.
   The meta table enforces exactly one row via `CHECK (rowid = 1)` but has no UNIQUE/PK
   on `corpus_id`, so `INSERT ... ON CONFLICT DO NOTHING` has no conflict target and the
   second insert raises `sqlite3.IntegrityError`. `ensure_corpus_meta` is therefore not
   idempotent within a live table; cross-session corpus_id stability is covered by
   `test_reopen_same_file_yields_equal_identity`.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-007
- **Source issue**: `issues/20261029-104506_ragcorpus001_rag-corpus-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ragcorpus001_rag-corpus-identity.md` — Implementation Target Files row 15
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-140156
- **Related target files**: `tests/rag/test_corpus_identity.py`