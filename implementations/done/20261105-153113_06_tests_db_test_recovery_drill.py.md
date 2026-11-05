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
- **Decision (resolved 2026-11-05, user-confirmed):** the drill currently runs only physical
  checks for rag (`_verify_rag_session`: integrity + `required_table_rag`, L91-L98) and does
  not run logical consistency verification. This Plan adds it:
  1. Wire a direct `check_rag_consistency` call in `_verify_rag_session` (guarded to
     `domain == "rag"`), NOT `_run_logical_verification`: its `sqlite3.Error` guardrail
     returns `(True, None)` and would contradict AC-004 for the extension-missing case.
  2. Upgrade the drill's rag fixture (`_RAG_DDL`) to a full plain RAG core schema (`chunks`,
     a `chunks_vec` with an `embedding BLOB` column, the fts5 tables + triggers — mirroring
     `tests/db/test_rag_consistency.py`, no external extension) so the healthy sweep verifies
     clean end-to-end; inject a report with an unverified flag only for the failure-path test.

## Design decisions

- Add a single `"rag_consistency"` boolean to the rag `verification` dict: `True` only when
  every dimension is verified and `rag_is_consistent`; `False` when any dimension is
  unverified or the report is inconsistent. This keeps the pass formula unchanged and the
  artifact schema additive.
- For the tests: the upgraded rag fixture exercises the healthy verified path end-to-end;
  the unverified-failure path is exercised by injecting a report with an unverified flag.

## Alternatives considered

- Adding per-dimension sub-keys versus one combined key. Chose one
  key: the drill reports a domain-level pass/fail, and AC-004 concerns the domain pass, not
  per-dimension drill reporting. Per-dimension detail lives in the recovery log (seq 04).
- Upgrading the drill fixtures to a full plain RAG core schema versus injecting a report for
  every path. Chose fixture upgrade for the healthy path (real end-to-end verification, no
  external extension needed) plus report injection for the unverified-failure path.

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
- Verification findings (2026-11-05, HEAD d6acadd14) on the drill wiring:
  - `_verify_rag_session` (`recovery_drill.py` L91-L98) is shared by the rag AND session
    domains; the consistency sub-key must be added only when `domain == "rag"`.
  - `test_verify_per_domain_reports_expected_verdicts` (`tests/db/test_recovery_drill.py`
    L250-L253) asserts the rag `verification` dict with an exact equality; it must be
    updated to include `"rag_consistency": True` (the session assertion is unchanged).
  - The drill's rag fixture (`_RAG_DDL`, only the `documents` table) cannot pass logical
    verification, so the healthy-sweep tests need either a fixture upgrade (add `chunks`,
    a `chunks_vec` with an `embedding BLOB` column, and the fts5 tables — the same plain
    schema `tests/db/test_rag_consistency.py` uses, no external extension required) or a
    verified-report patch injected in those tests.
  - The CLI subprocess tests drill only `workflow`, so they are unaffected.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261105-184806 | 20261105-184806 | `scripts/db/recovery_drill.py`: `_verify_rag_session` now adds `"rag_consistency"` (all flags false AND `rag_is_consistent`) only when `domain == "rag"`; direct `check_rag_consistency` on the isolated copy, per the user-confirmed decision (not `_run_logical_verification`). Fixture `_RAG_DDL` upgraded to the full plain RAG core schema. |
| 2 | Add or update tests per Validation plan | Completed | 20261105-184806 | 20261105-184806 | New: `test_rag_verified_fixture_passes_drill`, `test_rag_unverified_dimension_fails_drill` (report injection). `test_verify_per_domain_reports_expected_verdicts` rag dict updated with `"rag_consistency": True`. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261105-184806 | 20261105-184806 | tests/db 411 passed; tests/deploy 27 passed (interlock: see Blocker Log); ruff clean; lint-imports 6 kept/0 broken; mypy success (557 files, fresh cache). Immutability invariant test still green. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261105-184806 | 20261105-184806 | N/A: docs handled by seq 07. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | `tests/deploy/test_init_db_ledger_gate.py::test_recovery_drill_runs_under_flag_and_leaves_fixtures_untouched` failed: the drill now runs the fail-closed logical layer on rag, and that test's `documents`-only rag fixture made the drill FAIL. | Yes — interlock: upgraded its rag provisioner (`_provision_minimal_rag` → `_provision_rag_core`) to the plain RAG core schema; second failure (`no such column: chunk_index` diagnostic) fixed by completing the `chunks` columns to match the drill fixture. tests/deploy 27 passed. | 2026-11-05 |

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