## Goal

Make `check_rag_consistency` fail closed: propagate fatal-class probe errors
instead of swallowing them, mark an unverified dimension rather than a healthy
zero, and stop a single failing probe from cancelling the other checks. Also fix
the `_embedding_dimension_issue` display bug that renders a 0/1 flag instead of
the expected dimension count.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The additive verification-status field is defined in the sibling procedure
  `scripts/db/models.py` (seq 03); this module consumes it via the
  `RagConsistencyReport` dataclass and does not define it. Seq 03 MUST land
  before this change: the split probes set those flags.
- Execution interlock (verification finding 2026-11-05, HEAD d6acadd14): on the
  current fixture the embedding probe raises on every fixture (no `embedding`
  column). Landing the split without seq 05's fixture update would add a
  diagnostic error to every report and regress `is_consistent` on all healthy
  fixture tests. Land seq 05 step 1 (fixture) in the same cycle as this change.
- On the non-`vec0` test harness (`chunks_vec` without an `embedding` column) the
  embedding probe raises `sqlite3.Error`. The fixtures in
  `tests/db/test_rag_consistency.py` (seq 05) must expose a `vec0`-compatible
  `chunks_vec` (an `embedding` column present) so a healthy database verifies
  clean, while a genuinely missing table still fails closed. See UNK-04.

## Design decisions

- Replace the single combined `try`/`except sqlite3.Error: pass` block
  (`rag_consistency.py` L93-L100) with one guarded call per fatal-class probe.
  Each probe's `sqlite3.Error` is recorded and that dimension is left unverified,
  so one failing probe cannot cancel the other two (REQ-001, REQ-003).
- Express the unverified state through the additive report status field
  (`models.py` procedure) rather than by mutating numeric counts, so numeric
  consumers are unaffected (REQ-002).

## Alternatives considered

- Return an `(result, error)` tuple from each probe versus inline
  `try`/`except`. Chose inline per-probe guards that append to
  `diagnostic_errors`, mirroring the existing per-collection-stage pattern already
  used above in `check_rag_consistency`.
- Treat a missing embedding column as a clean pass versus unverified. Chose
  unverified (fail closed); the test harness is updated to a valid `vec0` form so
  clean databases stay verified.

## Implementation
### Target file
`scripts/db/rag_consistency.py`

### Procedure
1. Locate the combined fatal-class probe block (L93-L100) and split it into three
   independent guarded calls.
2. For each probe, catch `sqlite3.Error`, append a diagnostic message to
   `diagnostic_errors`, and leave that dimension's result unverified via the
   report status; do not let one failure reset the other counters.
3. Confirm FK, embedding, and schema checks execute and report independently when
   any one raises.
4. Fix `_embedding_dimension_issue` (L337-L346): render the configured expected
   embedding dimension count instead of the 0/1 `dimension_mismatch` flag.
5. Confirm a healthy database still reports verified and consistent.

### Method
Refactor the orchestration in `check_rag_consistency` and correct the issue
builder. No new public symbol is introduced.

### Details
- Current L93-L100 wraps `_check_fk_consistency`, `_check_embedding_dimension`,
  and `_check_schema_recognition` in one `try` ending `except sqlite3.Error:
  pass`. A raise in any one zeroes the other two counters and skips the remaining
  probes, so a missing/broken table reads as a consistent report.
- After the split each probe runs under its own guard; a `sqlite3.Error` records a
  diagnostic and marks that dimension unverified (status field from
  `models.py`) without touching the other counters.
- `_embedding_dimension_issue` (L342-L343) renders
  `expected={report.dimension_mismatch}`, where `dimension_mismatch` is the 0/1
  flag set at L95-L97. Substitute the configured expected dimension from
  `get_embedding_dims()` (`scripts/db/store_protocols.py`) so the message shows
  the real expected dimension.

## Compatibility considerations
`check_rag_consistency`'s return type is unchanged; behavior differs only when a
probe genuinely errors (a previously masked problem). A healthy database reports
identically. The consumer regression suite (`tests/agent/`, `tests/rag/`) must
stay green.

## Security considerations
N/A: read-only consistency probes; no auth, secrets, or input mutation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py` — error-path and independence
  tests (see seq 05).
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`,
  `uv run mypy scripts/`.

## Completion criteria
- No fatal-class probe shares a `try`/`except`; each records its own error.
- A single failing probe leaves the other dimensions verified.
- `_embedding_dimension_issue` shows the configured dimension count, not `0`/`1`.
- A clean database still returns a verified, consistent report.

## Out of Scope
The additive status field itself (seq 03), the probe-layer error signatures
(seq 02), consumer propagation (seq 04), and the tests (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261105-184806 | 20261105-184806 | Combined block split into three per-probe guards setting `fk_unverified`/`embedding_unverified`/`schema_unverified` + diagnostics; `_embedding_dimension_issue` now renders `get_embedding_dims()`. Interlock applied in-cycle: seq 05 step 1 fixtures (`embedding BLOB` column + `_insert_vec`) and the three `TestCollectionFailureDiagnostics` prefix updates landed here to keep the targeted suite green. |
| 2 | Add or update tests per Validation plan | Completed | 20261105-184806 | 20261105-184806 | Diagnostic-prefix tests updated in-cycle; error-path/independence tests land in seq 05. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261105-184806 | 20261105-184806 | tests/db/test_rag_consistency.py 59 passed; full suite 11628 passed/9 skipped; ruff, mypy (557 files), lint-imports 6 kept/0 broken. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261105-184806 | 20261105-184806 | N/A: docs handled by seq 07. |

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
- **Requirement ID**: `REQ-001` (probe errors and unavailable extension state propagate as verification failures), `REQ-002` (unknown never aggregates as healthy)
- **Source issue**: issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-153113
- **Related target files**: scripts/db/rag_consistency.py