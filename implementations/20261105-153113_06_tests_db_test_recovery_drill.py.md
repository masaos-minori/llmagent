## Goal

Make the recovery drill consume the fail-closed RAG consistency contract: the drill's rag
verification must reflect an unverified dimension (probe error or unavailable `sqlite-vec`) as
a verification failure in the audit artifact, not a pass. Add a drill test asserting this
(REQ-004, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The drill derives each domain's pass from
  `ok = integrity AND all(verification.values())` (`scripts/db/recovery_drill.py`
  `run_drill`, L282-L284). Adding a truthy/`False` consistency sub-key to the rag
  `verification` dict therefore drives pass/fail without changing that formula.
- The report carries per-dimension unverified flags (`scripts/db/models.py`, seq 03); the drill
  reads them via `check_rag_consistency` on the restored database.
- **Open decision (Need confirmation):** the drill currently runs only physical checks for rag
  (`_verify_rag_session`: integrity + `required_table_rag`, L91-L98) and does not run logical
  consistency verification. This Plan adds it. Two follow-on questions must be decided:
  1. Reuse `_run_logical_verification` (`scripts/db/recovery.py`), whose `sqlite3.Error`
     guardrail returns `(True, None)` so a verification gap never aborts a completed physical
     restore — versus a direct `check_rag_consistency` that surfaces an unverified state.
     Reusing the guardrail would contradict AC-004 for the extension-missing case.
  2. The drill fixtures (`tests/db/test_recovery_drill.py`) use minimal core tables without
     vec0/`rag_corpus_meta`, so full logical verification marks the healthy sweep unverified.
     Either upgrade the fixtures or, for the unit test, inject a report with an unverified
     flag.

## Design decisions

- Add a single `"rag_consistency"` boolean to the rag `verification` dict: `True` only when
  every dimension is verified and `rag_is_consistent`; `False` when any dimension is
  unverified or the report is inconsistent. This keeps the pass formula unchanged and the
  artifact schema additive.
- For the test, inject a report with an unverified flag rather than rewriting every fixture, so
  the healthy-sweep test stays green while the unverified path is exercised.

## Alternatives considered

- Adding per-dimension sub-keys versus one combined key. Chose one
  key: the drill reports a domain-level pass/fail, and AC-004 concerns the domain pass, not
  per-dimension drill reporting. Per-dimension detail lives in the recovery log (seq 04).
- Upgrading the drill fixtures to a full vec0 schema versus injecting a report. Chose injection
  for the unit test (isolated, fast); fixture upgrades can follow if end-to-end coverage is
  desired.

## Implementation
### Target file
`tests/db/test_recovery_drill.py`

### Procedure
1. Wire the drill's rag domain to the fail-closed report (in
   `scripts/db/recovery_drill.py`, `__init__`-adjacent to this doc's sibling
   `scripts/db/recovery_verification.py` seq 04). In `_verify_rag_session`, after the existing
   physical checks, run `check_rag_consistency` on the isolated database and add
   `"rag_consistency": <bool>` to the returned dict — `True` only when all unverified flags are
   `False` and `rag_is_consistent(report)`; otherwise `False`. (Resolve the two open decisions
   above before landing.)
2. Confirm the healthy-sweep assertion (`ok is True`) still holds: the healthy sweep must have
   every dimension verified. If the minimal fixtures cannot pass logical verification, upgrade
   them (add `rag_corpus_meta`, a `vec0`-compatible `chunks_vec` with a valid embedding) or gate
   the consistency check behind extension availability.
3. Add a test that injects a report with one unverified flag set and asserts the drill's rag
   artifact records a verification failure (`artifact["verification"]["rag_consistency"]` is
   `False`, and `run_drill` returns `False` for that domain). Patch
   `db.recovery_drill.check_rag_consistency` (or the verification step) to return such a report.
4. Add a test that a fully verified report yields `rag_consistency: True` and a passing drill.
5. Confirm the live databases are never mutated (existing immutability invariant).

### Method
Additive sub-key to the rag verification dict plus two drill tests (unverified-fails,
verified-passes) using report injection.

### Details
- Current `_verify_rag_session` returns `{"integrity": ..., "required_table_rag": ...}`. The
  pass formula (`run_drill`, L282-L284) ANDs every value, so a new `False` sub-key fails the
  domain without touching other domains.
- The physical-restore-completion guarantee lives in `_run_logical_verification`, not in the
  drill's artifact recording. The drill still writes its artifact and completes the physical
  restore; the logical unverified state is surfaced in the artifact's `verification` dict.
- Injecting a report (rather than rebuilding fixtures) keeps the healthy-sweep test
  green while still exercising the fail-closed branch.

## Compatibility considerations
Test-only change for the assertions; the drill wiring is additive (one new verification sub-key).
A fully verified restored database drills identically to before. The recovery test suite
(`tests/db/test_db_recovery.py`, `tests/db/test_recovery_drill.py`) must stay green.

## Security considerations
N/A: tests only; sandboxed file-based fixtures under `tmp_path`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_recovery_drill.py` — full module green, including the new
  unverified-fails and verified-passes cases.
- `uv run lint-imports` (0 broken contracts), `uv run ruff check .`, `uv run mypy scripts/`.

## Completion criteria
- The drill's rag verification includes a consistency sub-key that is `False` when any dimension
  is unverified (AC-004).
- Tests exist for the drill consuming an unverified dimension and for the healthy path, and they
  fail if the fail-closed behavior regresses (AC-005).
- The healthy sweep still passes and live DBs stay untouched.

## Out of Scope
Defining the unverified flags (seq 03), populating them (seq 01), recovery-side consumer
branching (seq 04), and the RAG consistency tests (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Drill wiring + tests. |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document. |
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
- **Requirement ID**: `REQ-004` (recovery drill consumes explicit failure states), `REQ-005` (drill tests for unverified dimensions)
- **Source issue**: issues/20261104-143443_ragverify001_complete-fail-closed-rag-consistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-230307_ragverify001_complete-fail-closed-rag-consistency.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-153113
- **Related target files**: tests/db/test_recovery_drill.py
