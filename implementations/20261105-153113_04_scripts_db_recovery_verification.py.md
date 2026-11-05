## Goal

Make the recovery path consume the fail-closed RAG consistency contract: a RAG dimension that
is unverified (probe error or unavailable `sqlite-vec`) must be treated as a verification
failure by `_verify_rag_logic`, and named in `_rag_inconsistency_detail` rather than passed
through as if consistent.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The report now carries per-dimension unverified flags (`fk_unverified`,
  `embedding_unverified`, `schema_unverified`; `scripts/db/models.py`, seq 03). This layer
  reads them; it does not define them.
- `_verify_rag_logic` is called by `scripts/db/recovery.py` (`_run_logical_verification`) on
  the restored database during recovery. The physical-restore-completion guardrail in
  `_run_logical_verification` (returns `(True, None)` on `sqlite3.Error` so a verification
  gap never aborts a completed physical restore) still applies; this Plan changes the
  *logical* result, not that guardrail.
- `rag_is_consistent` (`scripts/db/rag_consistency.py`) is the numeric predicate; the new
  unverified flags are orthogonal and must be checked in addition to it.

## Design decisions

- Branch on unverified flags BEFORE trusting the numeric predicate: even if a numeric check
  happened to pass, an unverified dimension means the report is incomplete, so
  `_verify_rag_logic` returns `(False, detail)`.
- Name the unverified dimension(s) in `_rag_inconsistency_detail` so the audit artifact and
  recovery logs show WHICH dimension failed, not just that counts were off.

## Alternatives considered

- Checking unverified flags only when `rag_is_consistent` is `False` versus always. Chose to
  check always: a masked/unverified dimension is a failure even when the surviving numeric
  checks happen to align, so relying on the numeric predicate alone reintroduces the
  fail-open class this Plan removes.
- Reusing `diagnostic_errors` at consumption time versus reading the structured flags. Chose
  the structured flags (seq 03): they are the report-contract expression of the failure and
  keep this layer decoupled from message-string parsing.

## Implementation
### Target file
`scripts/db/recovery_verification.py`

### Procedure
1. In `_verify_rag_logic` (L87-L92), after computing `report = check_rag_consistency(db)`,
   check the unverified flags from the report contract (seq 03) in addition to
   `rag_is_consistent(report)`:
   - If any of `report.fk_unverified`, `report.embedding_unverified`,
     `report.schema_unverified` is `True`, return `(False, _rag_inconsistency_detail(report))`.
   - Otherwise fall through to the existing `if rag_is_consistent(report): return True, None`
     branch.
2. In `_rag_inconsistency_detail` (L33+), add entries for any unverified dimension so the
   detail string names it (e.g. `"embedding_unverified"`, `"fk_unverified"`,
   `"schema_unverified"`), alongside the existing count-based entries.
3. Confirm `_run_logical_verification` (L111-L128) still returns `(True, None)` only on the
   `sqlite3.Error`-opening-guardrail (physical-restore-completion); the logical unverified
   result flows back through its normal `(False, detail)` return, not through that guardrail.
4. Confirm a restored RAG database whose dimensions are all verified behaves exactly as before.

### Method
Additive branching in two functions. No signature change; no new public symbol.

### Details
- Current `_verify_rag_logic` returns `(True, None)` whenever `rag_is_consistent(report)` is
  `True` and `(False, detail)` otherwise. It never inspects verification status, so an
  unverified-but-numerically-clean report would pass. The added flag check closes that gap.
- `_rag_inconsistency_detail` builds a `"; "`-joined summary from `(include, text)` entries.
  Add `(report.embedding_unverified, "embedding_unverified")` etc. to the same pattern.
- The physical-restore-completion guarantee lives in `_run_logical_verification`, not here.
  This Plan does not touch it; the drill's physical restore still completes, and the logical
  unverified state is recorded in the audit artifact (see `scripts/db/recovery_drill.py`,
  seq 06).

## Compatibility considerations
`_verify_rag_logic` keeps its `(bool, str | None)` return type. Behavior differs only when a
dimension is genuinely unverified (a previously masked problem). A fully verified report
behaves identically. The recovery test suite (`tests/db/test_db_recovery.py`,
`tests/db/test_recovery_drill.py`) must stay green.

## Security considerations
N/A: logical verification of read-only restored databases; no auth, secrets, or input
mutation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py tests/db/test_recovery_drill.py` — assert an
  unverified dimension blocks a consistency pass (see seq 06).
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- `_verify_rag_logic` returns `False` when any unverified flag is set, regardless of the
  numeric predicate.
- `_rag_inconsistency_detail` names the unverified dimension(s).
- A fully verified restored database still returns `(True, None)`.

## Out of Scope
Defining the unverified flags (seq 03), populating them (seq 01), the drill wiring (seq 06),
and the tests (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Additive branching. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by seq 06. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (recovery drill and recovery verification consume explicit failure states)
- **Source issue**: issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-153113
- **Related target files**: scripts/db/recovery_verification.py
