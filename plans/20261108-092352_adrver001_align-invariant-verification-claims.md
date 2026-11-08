## Goal
- Make each reviewed ADR verification claim (ADR-004, ADR-008 and ADR-010 rows and their index matrix rows) state its actual evidence and coverage limits using the existing matrix statuses, and add two focused tests for the highest-risk gaps: the stage order of the in-process fallback re-execution (ADR-010 INV-05) and byte-identity of a corrupt database under Dry Run (ADR-008 INV-16).

## Priority
Medium

## Scope
- **In-Scope**: the Verification sections of ADR-010 and ADR-008; the ADR Invariant Verification Matrix rows of `docs/10_adr/adr_01_index.md` for ADR-004, ADR-008 and ADR-010 (and the ADR-002 rows only to keep them in sync with the ADR-002 body); one new test through the `augment()` fallback path; one strengthened existing stage-order test; one new Dry Run byte-identity test; explicit procedure and record for any invariant that stays `Partial` or `Manual`.
- **Out-of-Scope**: a full test-suite redesign; mandatory automation of every architectural rule; new authority or evidence registries; architectural policy changes (they stay in the four dependency Plans); correcting claims of ADRs other than those named, which are filed as separate Issues when found.
- **Dependencies**: the final mappings depend on four Plans that edit the same documents; their sequencing is below. Phase 1 (tests) does not depend on them.
  - **Depends on**: plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md | phase 1 | ADR-010 decision table and corrected wording must exist before the ADR-010 Verification rows are finalized.
  - **Depends on**: plans/20261108-091719_adrrag002_reconcile-adr-010-contract.md | phase 3 | ADR-010 invariant wording must be final before INV rows are mapped.
  - **Depends on**: plans/20261108-092007_adrdb001_clarify-adr-008-scope.md | phase 4 | ADR-008 final wording and its size reduction must land before its Verification rows and the size ceiling are touched.
  - **Depends on**: plans/20261108-092140_adrcfg001_clarify-adr-002-isolation.md | phase 3 | ADR-002 security-claim wording must be final before the ADR-002 index rows are synchronized.

## Background
Verified against the current files and tests (checked in Step 2):
- ADR-010 states that INV-05 is covered by `tests/rag/test_rag_http_mode.py::test_in_process_fallback_sets_result_source_fallback`, which stubs `RagPipeline.run` and asserts only the result source, status code and a fallback reason; no test asserts the stage sequence on fallback. The existing `tests/rag/test_stage_lifecycle.py::TestStageExecutionOrder::test_stage_order_with_mocked_stages` patches `_run_stage` and asserts only that the result is a `PipelineRunResult`, so its class and test names claim an order check it does not make.
- ADR-008 states INV-16 is covered by three Dry Run tests and notes "no test asserts byte-identity of a corrupt DB under Dry Run". The tests patch `_run_integrity_check` and use a mocked `DbConfig` that points at non-existent `/tmp/*.db` paths (`tests/db/test_db_recovery.py` L20-52, L249-258, L569-593, L1463-1500), so no real database file is touched.
- The index legend (`docs/10_adr/adr_01_index.md` L160-163) already defines the convention: `Confirmed` / `Partial` / `Manual` / `Not verified`, plus evidence kinds `Static` and `Runtime-observed`, and requires a `Cadence:` and an `Expected evidence:` field in every `Manual` and `Partial` cell (enforced by `tools/check_adr_invariant_matrix.py`). No new vocabulary is needed.
- The matrix and the ADR bodies disagree: the matrix row `ADR-008 INV-01` states "Each DB has its own schema creation and recovery path", but ADR-008 INV-01 states that `rag.sqlite` is the canonical store (the statement matches INV-09), and the ADR-008 Verification row maps INV-01 to INV-04 to the same schema-creation/recovery evidence. The index has two rows for `ADR-004 INV-07, INV-10` with different statements and different statuses (`Confirmed` for an MCP-posture statement, `Partial` for the safety/integrity statement); the ADR-004 body marks both invariants `Partial by phase`. The index itself says a mismatch is resolved by correcting the matrix to the ADR body.
- ADR-004 INV-15/INV-16 and ADR-014 rows are deliberate `Manual` controls with a stated procedure, cadence and expected evidence; they are kept as they are.
- Not in the Issue: `docs/10_adr/adr_01_index.md` is 31492 bytes against a 31174-byte ceiling in `tools/check_docs_structure.py`, so the CI-run structure check already fails on the unmodified file; ADR-008 has the same condition (34604 versus 34206 bytes, see the `adrdb001` Plan).

## Problem
A stub-based or mock-based test does not establish full coverage, and a matrix row whose statement does not match its ADR body claims evidence for a different invariant. Accepted status and verification completeness are separate dimensions, and the current text sometimes blurs them.

## Reason for Change
Verification reports must describe actual evidence, limits and residual risk. It is Medium because it concerns testability and documentation accuracy, not a confirmed runtime defect. Final mappings need the four dependency Plans, so this work is sequenced after them.

## Implementation Intent
Inventory the existing invariant-to-evidence mappings in place (the ADR Verification sections and the matrix), read each cited test's assertions, classify each reviewed claim with the existing statuses, correct overstated or mismatched claims in the ADRs and the matrix, add the two focused tests, and keep justified manual reviews with their procedure and record. Create no registry and weaken no invariant.

## Requirements
- `REQ-001`: Every matrix row for ADR-004, ADR-008 and ADR-010 states the same invariant and the same status as its ADR body: the ADR-008 INV-01 row is corrected, the duplicate `ADR-004 INV-07, INV-10` rows are reconciled to the ADR-004 body, and the ADR-002 rows follow the final ADR-002 wording; statuses use only `Confirmed`, `Partial`, `Manual` and `Not verified`.
- `REQ-002`: A new test drives `augment()` through an HTTP transient failure and asserts the in-process stages run in the order MQE, search, RRF, rerank (augment as the pipeline defines it), and `test_stage_order_with_mocked_stages` asserts the stage order its name states, without weakening any existing assertion.
- `REQ-003`: The ADR-010 Verification section cites the new evidence for INV-05, states what the tests still do not cover (for example real stage behavior behind the mocks), and the matrix mirrors it with the status that evidence supports.
- `REQ-004`: A new test creates a real corrupt SQLite file under `tmp_path`, runs `recover_corruption(..., dry_run=True)`, and asserts the file's bytes are unchanged and no archive, sidecar or restore artifact is created.
- `REQ-005`: The ADR-008 Verification section maps INV-01 to INV-04 to evidence that matches those invariants, cites the new test for INV-16, and keeps the remaining limit visible.
- `REQ-006`: Every invariant that remains `Partial` or `Manual` among the reviewed rows has a defined procedure, `Cadence:` and `Expected evidence:` in the matrix, and the justified manual reviews (ADR-004 INV-15/INV-16, ADR-014) are unchanged.
- `REQ-007`: After the edits `docs/10_adr/adr_01_index.md` is at or below 31174 bytes and ADR-008 at or below 34206 bytes, reached without removing any invariant, reference or evidence.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/rag/test_rag_http_mode.py` | RAG HTTP-mode and fallback behavior tests | Add the fallback stage-order test | `REQ-002` / AC-02 | `test_in_process_fallback_sets_result_source_fallback` at L81 stubs `run` (checked in Step 2); `RagPipeline.augment()` at `scripts/rag/pipeline.py` L240-330 (checked in Step 3) | the test itself | Verified |
| `tests/rag/test_stage_lifecycle.py` | Stage lifecycle tests | Make `test_stage_order_with_mocked_stages` assert the order of `_run_stage` calls | `REQ-002` / AC-02 | L82-88 asserts only `isinstance(result, PipelineRunResult)`; `_run_stage` is called per stage at `scripts/rag/stage_lifecycle.py` L119 (checked in Step 2) | the test itself | Verified |
| `tests/db/test_db_recovery.py` | Recovery tests | Add the Dry Run byte-identity test with a real corrupt file | `REQ-004` / AC-04 | Dry Run tests at L249, L569, L583, L1463 patch `_run_integrity_check` and use `mock_db_cfg` paths `/tmp/*.db` (checked in Step 2) | the test itself | Verified |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | ADR-010 Verification | Update the INV-05 row and the Manual Review list to the real evidence and limits | `REQ-003` / AC-03 | Verification row at L219 and Manual Review at L241 (checked in Step 2) | `tests/rag/test_rag_http_mode.py`, `tests/rag/test_stage_lifecycle.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | ADR-008 Verification | Correct the INV-01 to INV-04 row; update the INV-16 row | `REQ-005`, `REQ-007` / AC-05, AC-07 | Verification rows at L309 and L313; ADR-008 INV-01 at L250 (checked in Step 2) | `tests/db/test_db_recovery.py` | Verified |
| `docs/10_adr/adr_01_index.md` | ADR Invariant Verification Matrix | Correct mismatched rows, reconcile the duplicate ADR-004 rows, add `Partial` rows with Cadence and Expected evidence where needed, keep the ceiling | `REQ-001`, `REQ-006`, `REQ-007` / AC-01, AC-06, AC-07 | Rows at L177-L197, legend at L158-L161; 31492 bytes versus a 31174 ceiling (checked in Step 2) | `tools/check_adr_invariant_matrix.py` (checker, run unchanged) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | ADR body for ADR-004 INV-07 and INV-10 (`Partial by phase`, L255, L258) and INV-15/INV-16 manual review; no change planned | `REQ-001`, `REQ-006` |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | ADR-002 body whose final wording the ADR-002 matrix rows must follow | `REQ-001` |
| `scripts/db/recovery.py` | `recover_corruption()` and Dry Run behavior | `REQ-004` |
| `scripts/rag/stage_lifecycle.py` | Stage loop calling `_run_stage` (L107-L119) | `REQ-002` |
| `scripts/rag/pipeline.py` | `augment()` fallback path and `run()` | `REQ-002` |
| `tools/check_adr_invariant_matrix.py` | Enforces cited-node existence and the Cadence and Expected evidence fields | `REQ-001`, `REQ-006` |
| `tools/check_docs_structure.py` | Holds the size ceilings that `REQ-007` must meet | `REQ-007` |
| `tests/shared/test_config_loader.py` | Evidence cited by the ADR-002 matrix rows | `REQ-001` |

## Acceptance Criteria
- AC-01 (`REQ-001`): For every reviewed matrix row the statement and status equal the ADR body's; the duplicate ADR-004 rows are gone; only the four defined statuses appear.
- AC-02 (`REQ-002`): The new test fails if the fallback runs the stages in another order or skips one, and the strengthened lifecycle test fails on a reordering; both pass on the current code.
- AC-03 (`REQ-003`): The ADR-010 INV-05 row cites the new nodes, names the remaining unverified scope, and the matrix status matches (`Confirmed` only if the evidence covers the whole invariant, otherwise `Partial` with Cadence and Expected evidence).
- AC-04 (`REQ-004`): The new test fails if Dry Run alters the file bytes or creates an archive or sidecar, and passes on the current code; if a real corrupt-file Dry Run cannot be built, INV-16 is recorded `Partial` with that reason.
- AC-05 (`REQ-005`): The ADR-008 INV-01 to INV-04 row cites evidence for those invariants; the INV-16 row cites the new node and its remaining limit.
- AC-06 (`REQ-006`): Each `Partial` or `Manual` reviewed row has `Cadence:` and `Expected evidence:`; `check_adr_invariant_matrix.py` reports no WARNING or ERROR for them.
- AC-07 (`REQ-007`): `wc -c` of the index is at most 31174 and of ADR-008 at most 34206; `check_docs_structure.py` reports no size finding for either.
- AC-08: The implementation report lists every test run with its result and every skipped or unexecuted check; no node is cited as `Confirmed` unless it ran and passed in that run.

## Tests
- New test in `tests/rag/test_rag_http_mode.py` (`REQ-002`): fallback stage order through `augment()`.
- Strengthened `tests/rag/test_stage_lifecycle.py::TestStageExecutionOrder::test_stage_order_with_mocked_stages` (`REQ-002`).
- New test in `tests/db/test_db_recovery.py` (`REQ-004`): Dry Run on a real corrupt file under `tmp_path` leaves bytes and directory contents unchanged.
- Existing suites `tests/rag` and `tests/db` run unchanged for regression (`REQ-002`, `REQ-004`); matrix and ADR corrections (`REQ-001`, `REQ-003`, `REQ-005` to `REQ-007`) are checked by the documentation checkers.

## Documentation Impact
Yes. ADR Verification sections (ADR-010, ADR-008) and the index matrix (`docs/10_adr/adr_01_index.md`): actual evidence, coverage limits, residual risk, and the procedure and record for manual verification. Driven by `REQ-001`, `REQ-003`, `REQ-005`, `REQ-006`, `REQ-007`. Located through `docs/10_adr/adr_01_index.md` itself. English only.

## Assumptions
- The index legend's four statuses and the `Cadence:`/`Expected evidence:` rule are the repository convention (confirmed in Step 2); no new labels are introduced.
- A real corrupt SQLite file can be produced in `tmp_path` and `recover_corruption()` can be pointed at it through a patched `DbConfig` (falsifiable at implementation; UNK-04 records the fallback).
- Sequencing dependency on the four Plans, which edit the same ADRs and the index: phase 1 (tests) runs first and independently; phases 2 and 3 run after the dependency phases listed in Scope. Overlap with `adrrag001` and `adrrag002` on ADR-010, and with `adrdb001` on ADR-008, is a sequencing dependency, not a design conflict.
- Verification text added to ADR-010 and ADR-008 is concise enough to stay within their size limits (ADR-010 is 21207 bytes; ADR-008 must end at or below its ceiling after the `adrdb001` reduction).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The four dependency Plans are open (all rows Pending) and edit the same ADRs and the index | Implementation status of the four Plans | Implement their listed phases first (`Depends on` above); phase 1 of this Plan can start earlier | False |
| UNK-02 | Which claims beyond ADR-010 INV-05 and ADR-008 INV-16 are overstated | An inspection of every reviewed row's cited assertions | Phase 2 and Phase 3 inspect the ADR-004, ADR-008 and ADR-010 rows and record each finding; an overstated claim outside those ADRs is filed as a separate Issue | False |
| UNK-03 | Whether the 31174-byte index ceiling should be raised if condensing cannot reach it without losing content | Owner decision on the ceiling in `tools/check_docs_structure.py` | Stop and report at implementation if `REQ-007` cannot be met without removing evidence; the checker is not edited here | False |
| UNK-04 | Whether a real corrupt-file Dry Run test can be built with the current `recover_corruption()` and `DbConfig` seams | Implementation attempt | If infeasible, record INV-16 as `Partial` with Cadence and Expected evidence and report why | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/rag/test_rag_http_mode.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `tests/rag/test_stage_lifecycle.py` | Modify | Low | 1 | N/A | not applicable (rsynced) |
| `tests/db/test_db_recovery.py` | Modify | Low | 8 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_06_010_rag-fallback.md` | Modify | Medium | 4 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Medium | 6 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | Modify | High | 26 | N/A | not applicable (rsynced) |

## Design
Classification: Path B, because the change touches 6 files (more than 3).

Analysis (Path B, all four recorded):
- Architecture: only test files and documents change; no `scripts/` import or module boundary changes, so `lint-imports` is not run (no Python file under `scripts/` is a target; checked in Step 3).
- Dependency: the matrix is read by `tools/check_adr_invariant_matrix.py` and the ADR bodies are the canonical record; the index is cited by every ADR and by `tools/check_docs_structure.py` (size ceiling). The new tests have no importers.
- Historical: 30-day churn from `git log` (table above); `adr_01_index.md` is the highest-churn row, so its edits are kept to the named rows. Bus factor not measured (`git-fame` not run).
- Operational: tests use `tmp_path` and mocks only; no port, running process or shared database is touched, so no lock check is needed.
- Persisted schema and consumer scan: not applicable (no schema, public API or shared constant change).

Design decisions:
1. Classification uses the index's existing statuses and the rule that an ADR body wins over the matrix; no new registry or label is added. Alternative considered: a per-invariant evidence file; rejected by the Issue's Out of Scope.
2. INV-05 evidence is two tests that together cover the claim: a fallback-path test that asserts the in-process stage order, and a strengthened lifecycle test that asserts the stage order itself. If the combined evidence still does not cover real stage behavior behind mocks, the status is `Partial` and the unverified scope is named. Alternative considered: marking `Confirmed` on the new test alone; rejected because the Issue forbids verifying on a reference alone.
3. INV-16 evidence is a real-file byte-identity test, since the existing tests never touch bytes. A tolerant fallback (UNK-04) keeps the claim honest if the seam is missing.
4. Manual reviews stay as deliberate decisions; only missing Cadence or Expected evidence fields are added.

## Implementation steps
1. **Phase 1: Focused tests** (independent of the four dependency Plans)
   - [ ] Add the fallback stage-order test (`REQ-002`; `tests/rag/test_rag_http_mode.py`)
   - [ ] Strengthen the lifecycle stage-order test (`REQ-002`; `tests/rag/test_stage_lifecycle.py`)
   - [ ] Add the Dry Run byte-identity test (`REQ-004`; `tests/db/test_db_recovery.py`)
2. **Phase 2: ADR Verification sections** (after the dependency Plans' phases listed in Scope)
   - [ ] Update the INV-05 row and the Manual Review list (`REQ-003`; `docs/10_adr/adr_02_06_010_rag-fallback.md`)
   - [ ] Correct the INV-01 to INV-04 row and update the INV-16 row (`REQ-005`; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`)
3. **Phase 3: Index matrix sync and size**
   - [ ] Correct mismatched rows, reconcile the duplicate ADR-004 rows, add Cadence and Expected evidence where a row is `Partial` or `Manual`, and meet the ceiling (`REQ-001`, `REQ-006`, `REQ-007`; `docs/10_adr/adr_01_index.md`)
4. **Phase 4: Verification**
   - [ ] Run the Validation plan commands and report every skipped or unexecuted check (`REQ-001` to `REQ-007`; all target files). No deploy step: no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| New and strengthened tests | Unit/Integration | `uv run pytest tests/rag/test_rag_http_mode.py tests/rag/test_stage_lifecycle.py tests/db/test_db_recovery.py` | Pass |
| RAG and DB regression | Regression | `uv run pytest tests/rag tests/db` | Pass; skipped tests reported |
| Added tests | Format, lint | `uv run ruff format tests/rag/test_rag_http_mode.py tests/rag/test_stage_lifecycle.py tests/db/test_db_recovery.py`; `uv run ruff check` on the same files | Clean |
| Matrix and ADRs | Cited nodes, structure, preservation, references | `uv run python tools/check_adr_invariant_matrix.py`; `uv run python tools/check_adr_reference.py`; `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_adr_structure.py` | No ERROR; no WARNING for reviewed rows |
| Documents | Quality and size | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/10_adr/adr_01_index.md docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md docs/10_adr/adr_02_06_010_rag-fallback.md` | No findings, including size |
| Documents | Content policy and language | `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_japanese.py` | No findings |
| Toolchain for added tests | Per `rules/toolchain.md` completion checklist, including diff-cover where applicable | the sequence in `rules/toolchain.md` | Pass or reported as not applicable |

## Risks
- **Risk**: Editing the same ADR sections as the four dependency Plans causes conflicting edits → **Mitigation**: run phases 2 and 3 only after the listed dependency phases and take their final wording as the base.
- **Risk**: A new test asserts a stage order that the code does not guarantee and turns flaky or over-specified → **Mitigation**: assert only the documented order of the stage class names from `_run_stage` calls and run the test repeatedly once.
- **Risk**: The Dry Run test touches a real path outside `tmp_path` → **Mitigation**: patch `DbConfig` to `tmp_path` files only and assert the directory listing is unchanged.
- **Risk**: Index and ADR-008 edits push past the size ceilings that already fail at HEAD → **Mitigation**: `REQ-007`; condense duplicated rows first (the duplicate ADR-004 rows shrink the index); stop and report if impossible (UNK-03).
- **Risk**: A claim is downgraded to `Partial` without a procedure and the matrix checker warns → **Mitigation**: every downgrade carries `Cadence:` and `Expected evidence:` (`REQ-006`).
- **Risk**: Marking `Confirmed` from a reference rather than a run → **Mitigation**: AC-08 requires the evidence to have passed in the implementation run.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Focused tests | Pending | — | — | |
| 2 | ADR Verification sections | Pending | — | — | |
| 3 | Index matrix sync and size | Pending | — | — | |
| 4 | Verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261107-050705_adrver001_align-invariant-verification-claims.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-092352
- **Related target files**: `tests/rag/test_rag_http_mode.py`, `tests/rag/test_stage_lifecycle.py`, `tests/db/test_db_recovery.py`, `docs/10_adr/adr_02_06_010_rag-fallback.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1-3, 8; index L160-L197 | `docs/10_adr/adr_01_index.md` | Phase 3 | AC-01 | `check_adr_invariant_matrix.py`; `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 5, 7; `test_rag_http_mode.py` L81; `test_stage_lifecycle.py` L82-88 | `tests/rag/test_rag_http_mode.py` | Phase 1 | AC-02 | New fallback stage-order test | Confirmed by repository evidence |
| REQ-002 | Required Changes 5, 7; `test_stage_lifecycle.py` L82-88 | `tests/rag/test_stage_lifecycle.py` | Phase 1 | AC-02 | Strengthened lifecycle stage-order test | Confirmed by repository evidence |
| REQ-003 | Required Changes 4, 6; ADR-010 L219, L241 | `docs/10_adr/adr_02_06_010_rag-fallback.md` | Phase 2 | AC-03 | `check_adr_invariant_matrix.py`; full read-through | Confirmed by repository evidence |
| REQ-004 | Required Changes 5, 7; `test_db_recovery.py` L20-52, L249-258, L569-593 | `tests/db/test_db_recovery.py` | Phase 1 | AC-04 | New Dry Run byte-identity test | Confirmed by repository evidence |
| REQ-005 | Required Changes 4, 6; ADR-008 L250, L309, L313 | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 2 | AC-05 | `check_adr_invariant_matrix.py`; full read-through | Confirmed by repository evidence |
| REQ-006 | Required Changes 7-8; index legend L158-L161 | `docs/10_adr/adr_01_index.md` | Phase 3 | AC-06 | `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-007 | Derived from verification (not in the Issue); `check_docs_structure.py` run on HEAD | `docs/10_adr/adr_01_index.md` | Phase 3 | AC-07 | `wc -c`; `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-007 | Derived from verification (not in the Issue); ADR-008 size 34604 versus 34206 | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 2 | AC-07 | `wc -c`; `check_docs_structure.py` | Confirmed by repository evidence |
