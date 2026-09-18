# Add automated test coverage for ADR invariants currently verified only by code inspection

## Priority
Medium

## Summary
`docs/adr-index.md`'s "ADR Invariant Verification Matrix" and its supporting check (`tools/check_adr_invariant_matrix.py`) already exist and function correctly — the Matrix's own "Note" states most invariants are "verified via code inspection, but lack automated test coverage." This issue tracks adding that missing automated coverage for the 12 invariants currently marked "no test yet" / "Not verified" / lacking a "cross-cutting test", rather than building new infrastructure.

## Background
The Matrix mechanism itself is not the gap — `docs/adr-index.md` (lines 61-101) already documents 22 invariants (INV-001 through INV-022) with a `Verification Status` column, and `tools/check_adr_invariant_matrix.py` already verifies that any pytest node id cited in that column actually exists. What remains open is the underlying test-authoring work the Matrix's own rows already flag as missing.

## Problem
Re-verified against the current Matrix (`docs/adr-index.md`): the following invariants are marked as lacking automated coverage:
- INV-003 (ADR-002, config isolation) — confirmed in code, no test yet
- INV-005 (ADR-003, RuntimeToolRegistry sole routing authority) — confirmed in code, no test yet
- INV-006 (ADR-007, no stdio transport) — confirmed, no test yet
- INV-007 (ADR-005, `chunks_vec` deleted before `documents`) — confirmed in code, no test yet
- INV-008 (ADR-009, `normalized_content` must not appear in LLM output) — confirmed, no test yet
- INV-009 (ADR-009, FTS5 rebuild rules followed) — Not verified
- INV-010 (ADR-004, single common failure-handling policy) — no dedicated cross-cutting test
- INV-011 (ADR-004, safety/integrity failures fail-fast/fail-closed) — no cross-cutting test
- INV-012 (ADR-006, EventBus offsets strictly monotonic) — confirmed, no test yet
- INV-013 (ADR-006, no success response before event persistence) — Not verified
- INV-014 (ADR-010, no local fallback on normal empty RAG result) — confirmed, no test yet
- INV-015 (ADR-010, no local fallback on RAG 401/403) — **Potentially violated** per the Matrix's own note (see `issues/20260914-105139_ragsvc01_fallback-trigger-transport-errors-only.md`, which addresses the underlying behavior; this issue's scope is adding the missing regression test once that fix lands, not re-diagnosing the violation)

## Reason for Change
An invariant confirmed only by code inspection has no regression protection — a future change could silently violate it with no test failure to catch the regression. The Matrix's own Pipeline Mapping Summary states INV-001 through INV-015 and INV-018/INV-022 are intended to run in CI, but 11 of those currently have no test backing that intent.

## Implementation Intent
Add one automated test per listed invariant (unit or integration, per the Matrix's own "Type" column), then update that invariant's `Verification Status` cell in `docs/adr-index.md` to cite the new test's pytest node id, per the Matrix's existing citation convention (backtick-quoted `path/to/file.py::test_name`) — `tools/check_adr_invariant_matrix.py` will then verify the citation stays valid going forward.

## Target Files or Areas
- `docs/adr-index.md`
- `tests/shared/` (INV-003, INV-005, INV-006, INV-012)
- `tests/rag/` or `tests/db/` (INV-007, INV-008, INV-009, INV-014, INV-015)
- `tests/agent/` (INV-010, INV-011)
- `tests/eventbus/` (INV-013)

## Required Changes
- INV-015: add the regression test once `issues/20260914-105139_ragsvc01_fallback-trigger-transport-errors-only.md` lands (highest priority — the Matrix already flags this as "Potentially violated").
- INV-003, INV-005, INV-006, INV-007, INV-008, INV-012: add a unit test per invariant, each in the module already covering the relevant class/function (per the Matrix's "Source"-equivalent code references).
- INV-009, INV-013: add an integration test per invariant (Matrix "Type" already specifies Integration Test for both).
- INV-010, INV-011: add one cross-cutting test each, per the Matrix's own explicit callout that both still lack one.
- Update each invariant's `Verification Status` cell in `docs/adr-index.md` to cite the new test, once added and passing.

## Constraints
Do not weaken or reinterpret any invariant's stated behavior while adding its test — this issue adds regression coverage for behavior already confirmed correct by code inspection; it does not re-derive or renegotiate what the invariant requires. If a new test reveals an invariant is actually violated (beyond the already-known INV-015 case), stop and report it rather than silently "fixing" the test to pass.

## Acceptance Criteria
- Each of the 12 listed invariants has a passing automated test cited in `docs/adr-index.md`'s Matrix.
- `tools/check_adr_invariant_matrix.py` continues to pass (confirming each new citation resolves to a real path).
- No invariant's stated behavior was changed to make its new test pass, except where a genuine violation was found and reported separately (not silently patched).

## Testing Expectations
This issue's entire deliverable is new test coverage (see Required Changes) — run the full test suite plus `tools/check_adr_invariant_matrix.py` after each addition to confirm the citation resolves correctly.

## Documentation Impact
Update `docs/adr-index.md`'s Matrix `Verification Status` column for each invariant, incrementally as its test is added — do not batch all 12 updates until every test is written; update each row as its own test lands, so partial progress remains visible and traceable.

## Out of Scope
- Building new Matrix infrastructure or a new verification tool — both already exist and are working.
- Re-diagnosing INV-015's potential violation — that is `ragsvc01`'s scope; this issue only adds the regression test once that fix lands.
- Any invariant not listed above (INV-001, INV-016, INV-018 through INV-022) — those are already confirmed by test, or are explicitly non-test verification types (Operational Procedure, Manual Review) per the Matrix's own classification.

## Dependencies
INV-015's test depends on `issues/20260914-105139_ragsvc01_fallback-trigger-transport-errors-only.md` landing first. The other 11 invariants have no cross-issue dependency and can be added independently, in any order.

## Unresolved Questions
N/A: none — the Matrix itself already specifies each invariant's intended verification "Type" (Unit/Integration Test), which this issue follows rather than re-deciding.

## AI Implementation Instruction
Add tests incrementally, one invariant at a time, updating `docs/adr-index.md`'s Matrix row immediately after each test passes — do not wait to batch all 12 updates. If a new test reveals a genuine invariant violation beyond the already-known INV-015 case, stop and report it as a separate finding rather than adjusting the invariant's stated behavior or the test to make it pass. Do not touch INV-015 until `ragsvc01` has landed.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-112456
- **Related target files**: docs/adr-index.md, tests/shared/, tests/rag/, tests/db/, tests/agent/, tests/eventbus/
