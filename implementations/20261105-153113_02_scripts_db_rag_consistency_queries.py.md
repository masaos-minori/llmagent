## Goal

Preserve the probe-layer error contract while the orchestrator (`scripts/db/rag_consistency.py`,
seq 01) is refactored to fail closed. The three fatal-class probes already propagate
`sqlite3.Error`; this layer must keep each probe's error distinct from a clean zero and
must surface `sqlite-vec` unavailability so the orchestrator marks the dimension
unverified rather than healthy.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The substantive fail-closed orchestration change lives in `scripts/db/rag_consistency.py`
  (seq 01); this layer's role is to preserve its propagation contract so that change has
  something reliable to consume.
- The three fatal-class probes (`_check_fk_consistency`, `_check_embedding_dimension`,
  `_check_schema_recognition`) already let `sqlite3.Error` propagate; no behavioral change
  to their signatures is required. The risk is regressions introduced by the orchestrator
  refactor, not a defect here.
- `_safe_url_count_query` intentionally returns `{}` on per-query failure (acknowledged
  design in the source issue). It is NOT a bug and must not be changed.
- On the non-`vec0` test harness (`chunks_vec` without an `embedding` column) the embedding
  probe raises `sqlite3.Error`. The fixtures in `tests/db/test_rag_consistency.py` (seq 05)
  are updated to a `vec0`-compatible `chunks_vec` so a healthy database verifies clean. See
  UNK-04.

## Design decisions

- Keep the probes pure: each returns its value or lets `sqlite3.Error` propagate. The
  orchestrator decides how to interpret a propagated error (mark the dimension
  unverified). No error handling is added here, so a future orchestrator cannot silently
  re-introduce swallowing.
- Distinguish `sqlite-vec` unavailability from a clean zero: a missing embedding column or
  unloaded vec0 extension raises `sqlite3.Error` (surfaced), whereas an empty
  `chunks_vec` returns verified-clean per `_check_embedding_dimension`. The orchestrator
  branches on this distinction.

## Alternatives considered

- Wrapping each probe call in a local `try`/`except` that returns a sentinel versus letting
  the error propagate. Chose propagation: it matches the existing `_check_fk_consistency`
  contract and forces the orchestrator to handle the error explicitly.
- Returning a `(value, ok)` tuple from each probe versus bare propagation. Chose bare
  propagation to avoid touching every caller and to keep the probe signature stable.

## Implementation
### Target file
`scripts/db/rag_consistency_queries.py`

### Procedure
1. Confirm `_check_fk_consistency` (L230-L240), `_check_embedding_dimension` (L243-L254),
   and `_check_schema_recognition` (L257-L271) still propagate `sqlite3.Error` after the
   orchestrator refactor. Do not add a `try`/`except` that swallows it.
2. Verify `_check_embedding_dimension` keeps its two distinct outcomes: an empty
   `chunks_vec` (nothing to contradict the config) returns verified-clean, while a missing
   embedding column or unloaded vec0 extension raises `sqlite3.Error` so the orchestrator
   marks the dimension unverified.
3. Leave `_safe_url_count_query` (L54-L60) returning `{}` on failure unchanged; it is
   acknowledged design, not part of this Plan.
4. Confirm no other caller in this module reintroduces a broad `except Exception` that
   would mask a `sqlite3.Error` from the fatal-class probes.

### Method
No new symbol and no signature change. This is a preservation/regression-guard step: the
orchestrator refactor (seq 01) is the change; this layer is verified to remain a faithful
error-propagating source.

### Details
- Current `_check_fk_consistency` documents that it lets `sqlite3.Error` propagate so the
  schema-recognition check records a missing-table read as a diagnostic error. That
  contract is the one this Plan relies on; preserve it.
- `_check_embedding_dimension` computes dimension as `byte_length // 4` and compares to
  `get_embedding_dims()`. A `sqlite3.Error` here means the vec0 extension is unavailable or
  the column is absent; it must reach the orchestrator, not be converted to a clean `True`.
- `_safe_url_count_query` catches `Exception` and returns `{}` with explicit `noqa` markers
  (L59-L60); the `{}` signals DB corruption to `_collect_url_counts_and_mismatches`. Do not
  alter this.

## Compatibility considerations
No public symbol or signature changes. Consumers of this module (`check_rag_consistency`
in `scripts/db/rag_consistency.py`) see identical values on healthy databases; only the
error-propagation path is relied upon by the orchestrator refactor. The consumer
regression suite (`tests/agent/`, `tests/rag/`) must stay green.

## Security considerations
N/A: read-only consistency probes; no auth, secrets, or input mutation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py` — error-path and independence tests (see
  seq 05).
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- All three fatal-class probes propagate `sqlite3.Error`; none is wrapped in a swallowing
  handler.
- `sqlite-vec` unavailability surfaces as a propagated error, not a clean zero.
- `_safe_url_count_query` still returns `{}` on failure.

## Out of Scope
The orchestrator split (seq 01), the report status field (seq 03), consumer propagation
(seq 04), and the tests (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Preservation step; orchestrator change is seq 01. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by seq 05. |
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
- **Requirement ID**: `REQ-001` (probe exceptions and unavailable extension state propagate as verification failures), `REQ-003` (schema/FK/embedding checks continue independently)
- **Source issue**: issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-153113
- **Related target files**: scripts/db/rag_consistency_queries.py
