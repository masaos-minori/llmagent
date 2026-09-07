## Goal
Create `tests/tools/test_check_canonical_source_conflicts.py`: one unit test per
already-implemented rule (`CANONICAL-001`, `-008`, `-010`, `-011`, plus the 5
Warnings) and integration tests against a temporary registry + temporary doc tree,
covering the 13 required test cases from the source Issue — implemented against
`tools/check_canonical_source_conflicts.py`'s **current, actual** `RegistryEntry`
shape, with the `CANONICAL-002`–`006`/`-009`/`-007` cases marked blocked pending
seq 01/seq 02's own landings (REQ-008).

## Scope
- In scope: new file `tests/tools/test_check_canonical_source_conflicts.py` only,
  covering the 9 rule-detection functions already implemented in
  `tools/check_canonical_source_conflicts.py` (`detect_duplicate_normative_sources`,
  `detect_multiple_canonical_specifications`, `detect_area_guide_contradiction`,
  `detect_legacy_precedence_reintroduction`, and the 5
  `detect_*` Warning functions), plus placeholder/skip-marked cases for the
  `CANONICAL-002`–`006`, `-009` (REQ-001, blocked on seq 01) and `CANONICAL-007`
  (REQ-004, blocked on seq 02) rules.
- Out of scope: `tests/tools/test_check_canonical_source_conflicts_routing.py`
  (already exists, already covers `classify_finding()` and
  `detect_duplicate_active_records()` — do not duplicate that coverage here);
  `tests/tools/test_check_docs_structure.py` — tracked in seq 04.

## Assumptions
- **Confirmed this cycle (2026-09-06)**: `tests/tools/test_check_canonical_source_conflicts_routing.py`
  already exists (104 lines, `TestClassifyFinding` + `TestDetectDuplicateActiveRecords`)
  — a narrower, already-landed test file covering only `classify_finding()` and
  `detect_duplicate_active_records()`. This row's new file must not re-test those
  two functions; it covers the 9 `RegistryEntry`-consuming rule functions the
  `_routing` file does not touch.
- Per seq 01 (`implementations/20260906-150421_01_tools_check_canonical_source_conflicts.py.md`,
  read this cycle): the tool's actual `RegistryEntry` fields are `id`, `target`,
  `claim_type`, `authority`, `precedence`, `status`, `effective_date`,
  `expiry_date`, `validation_ref`, `description` — **as they exist today**, before
  seq 01's own planned schema-reconciliation work lands. Tests for the 9
  already-working rule functions should therefore construct `RegistryEntry` objects
  using **today's actual field names**, not `M-01-04`'s registry schema
  (`decision_target`/`source_paths`/`area`/`notes`) — that reconciliation is seq 01's
  own future work, not yet landed, so testing against it now would test code that
  does not exist yet.
- Per seq 02 (unread by this row's own investigation — still an empty skeleton at
  the time of this cycle's read): the `CANONICAL-007` (duplicate ADR ID) integration
  is blocked on that row landing too.

## Design decisions
- Structure this file with one `TestClass` per rule (matching
  `tests/tools/test_check_docs_structure.py`'s existing per-concern class-split
  convention), directly unit-testing each `detect_*` function with hand-built
  `RegistryEntry` lists (no TOML file needed for these 9 unit tests — only the
  integration-level cases need a temporary registry file).
- For the `CANONICAL-002`–`006`/`-009` (REQ-001) and `CANONICAL-007` (REQ-004)
  cases: add `@pytest.mark.skip(reason="blocked on seq 01/seq 02 landing — see
  plans/20260905-165817_plan.md seq 01/02")`-marked stub tests with the intended
  assertions written as comments, rather than omitting them entirely — this keeps
  the file's eventual 13-case completeness visible and gives the next implementer a
  concrete starting point once the blockers clear, rather than requiring them to
  re-derive the test design from scratch.
- For the temporary-registry/temporary-doc-tree integration tests (covering "guide
  content generated from registry", "guide content conflicting with registry",
  "legacy recency-based authority statement"), use `pytest`'s `tmp_path` fixture to
  build a minimal TOML file and a minimal Markdown doc tree per case, matching how
  `tests/db/test_rag_consistency.py`-style tests in this repository already use
  temporary fixtures for similar isolation (per this session's earlier established
  convention).

## Alternatives considered
- Test all 9 rule functions only through the CLI (`detect_all_conflicts()`) rather
  than calling each `detect_*` function directly: rejected — direct per-function
  unit tests give clearer failure attribution (matching the Plan's own "one unit
  test per rule" requirement) and avoid needing a full temporary-registry file for
  every unit-level case.

## Implementation
### Target file
`tests/tools/test_check_canonical_source_conflicts.py`

### Procedure
1. Re-read `tools/check_canonical_source_conflicts.py`'s actual state immediately
   before writing tests — seq 01's schema-reconciliation work may have landed by
   then, changing `RegistryEntry`'s fields; if so, update this file's fixtures to
   match the landed schema rather than this document's snapshot.
2. Add `TestDetectDuplicateNormativeSources` (`CANONICAL-001`): construct 2
   `RegistryEntry` objects sharing `(target, claim_type)` with `precedence="normative"`
   — assert one `CANONICAL-001` conflict; construct a non-duplicate case — assert
   none.
3. Add `TestDetectMultipleCanonicalSpecifications` (`CANONICAL-008`): 2 entries with
   `claim_type="specification"` sharing a target — assert one `CANONICAL-008`
   conflict.
4. Add `TestDetectAreaGuideContradiction` (`CANONICAL-010`): an `area_guide`-claim-type
   entry and a `specification`-claim-type entry sharing a target, the latter
   `precedence="normative"` — assert one `CANONICAL-010` conflict (Medium severity,
   non-blocking per the tool's own current implementation).
5. Add `TestDetectLegacyPrecedenceReintroduction` (`CANONICAL-011`): an entry with
   `precedence="legacy_universal"` — assert one `CANONICAL-011` conflict (High,
   blocking).
6. Add one test class per Warning function (`CANONICAL-W-01` through `-05`),
   matching each function's own docstring'd condition (reference entry missing
   `validation_ref`; active reference/legacy entry with an expired `expiry_date`;
   active specification/acceptance_test entry missing `validation_ref`; entry with
   an unregistered `authority` value; non-normative entry whose `description`
   contains "authoritative"/"source of truth"/"must").
7. Add skip-marked stub tests for `CANONICAL-002` through `-006`, `-009` (REQ-001)
   and `CANONICAL-007` (REQ-004), each with a one-line comment naming which seq
   unblocks it.
8. Add integration tests using `tmp_path` for: one valid source (exit 0, no
   findings); duplicate normative sources; multiple implementation files for
   permitted runtime behavior (no conflict — confirm the tool's actual logic
   permits this, since REQ-005/AC5 in the M-01-04 Plan describes this case for
   `source_paths`, but this tool's own `RegistryEntry` has no equivalent list
   field today — mark this specific integration case `skip` too if the current
   schema genuinely has no multi-path concept, per Assumptions).

### Method
Confirmed this cycle (2026-09-06) via direct read: `tests/tools/test_check_canonical_source_conflicts_routing.py`
(104 lines) already exists and covers `classify_finding()`/`detect_duplicate_active_records()`
only; `tools/check_canonical_source_conflicts.py`'s 9 `detect_*` rule functions
(confirmed via seq 01's own read) have no existing test coverage.

### Details
No change to the existing `_routing.py` test file.

## Compatibility considerations
N/A: new test file only.

## Security considerations
Test fixtures must use synthetic placeholder content, never realistic-looking
sensitive data.

## Rollback considerations
New file — revert via `git rm tests/tools/test_check_canonical_source_conflicts.py`
if seq 01's landed schema differs enough from this document's assumptions to
require a substantially different fixture design.

## Validation plan
- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py -v` — all
  non-skipped cases pass; skipped cases report as `skipped`, not silently absent.
- `uv run pytest tests/tools/test_check_canonical_source_conflicts_routing.py -v` —
  regression check, unaffected by this new file.

## Completion criteria
- One passing test per already-implemented rule (9 functions).
- Skip-marked stubs exist for every blocked case (`CANONICAL-002`–`007`, `-009`),
  each naming its unblocking seq.
- No duplication of `_routing.py`'s existing coverage.

## Out of scope
- `tests/tools/test_check_canonical_source_conflicts_routing.py` — already exists,
  unmodified.
- `tests/tools/test_check_docs_structure.py` — tracked in seq 04.
- `tools/check_canonical_source_conflicts.py` itself — tracked in seq 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-06 | 2026-09-07 | Tests updated for new RegistryEntry schema |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-06 | 2026-09-07 | All tests pass (35 passed, 2 skipped) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-06 | 2026-09-07 | All tests pass (35 passed, 2 skipped) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No docs/00_index.md task-scope mapping for changed files |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260903-103028_m0105_implement-canonical-source-validation-and-ci-enforcement.md
- **Source plan**: plans/20260905-165817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150421
- **Related target files**: tests/tools/test_check_canonical_source_conflicts.py
