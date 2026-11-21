## Goal

Create `tests/shared/test_mcp_dedup_identity.py` as test-first evidence (Plan Phase 1) for the store identity and start-state matrix: first initialization, lost, replaced, legacy-or-unverified, schema mismatch, and operator resolution — written and confirmed failing against the current store before row 01 lands (REQ-005..REQ-007; AC-4, AC-5).

## Scope
**Release unit**: N/A: lands alone in Plan Phase 1 (test-first; the rollover units cover Phases 2-4)

## Assumptions
- The file is new; the containing directory `tests/shared/` exists.
- Phase 1 failure evidence (loss indistinguishable from first start today; `touch()` resolves an empty file; no identity exists to classify) is recorded in this document's Execution Status notes and mirrored into the Plan's Phase 1 notes (UNK-05 answer).
- Legacy fixtures are built from the pre-change single-table DDL (`tool_call_state`, `user_version = 0`); they are created inline in the test file, not imported from `scripts/`, so they remain stable after row 01 rewrites `_SCHEMA`.

## Design decisions
- Each case asserts the classification of a store open, not internal helpers: the contract is the start state surfaced to callers (REQ-006).
- Operator resolution is tested through its public operation (Plan D-4): validates state, archives the old file, creates a new generation, logs the decision; the removed `touch()` path is asserted absent (empty file alone never resolves, REQ-007).

## Alternatives considered
- Extending `TestLostOrRecreatedDetection` inside `tests/shared/test_mcp_dedup.py` instead of a new file: rejected — the Plan freezes the new file as its own target row, and Phase 1 needs a standalone failing-first artifact separable from the Phase 3 suite rewrite (row 09).

## Implementation
### Target file
`tests/shared/test_mcp_dedup_identity.py` (new)
### Procedure
Write the identity/loss matrix suite against today's store, then keep it as the Phase 3 gate.
### Method
1. First initialization: no DB, no marker -> creation writes `store_meta` + `user_version = 1` + marker atomically (AC-4/REQ-005).
2. DB-only deletion (marker present) -> `lost` (AC-4).
3. Marker-only deletion (DB present, healthy identity) -> classified as marker-state asymmetry, not silently `healthy` (AC-4).
4. DB replacement with a foreign store UUID -> `replaced` (AC-4).
5. Legacy fixture DB (no identity row, `user_version = 0`) -> `legacy_or_unverified`, never `first_initialization` and never `healthy` (AC-4).
6. Schema mismatch (drifted column shape on an otherwise valid identity) -> typed mismatch surfaced as the `store_error` taxonomy, not a raw `RuntimeError` (REQ-006).
7. Side-effecting-call blocking per state feeds AC-5 at store level (dispatcher-level refusal matrix lives in row 02's companion).
8. Operator resolution: legal states resolve to a new generation (generation counter increments in the new identity; decision log line asserted); creating an empty file alone does not resolve; illegal states refuse resolution (REQ-007, AC-5).
### Details
- Phase 1 run records: today a recreated empty DB is indistinguishable from first use (`lost_or_recreated` sentinel gate only), `resolve_lost_store` + `touch()` resolves an empty file, and no identity row exists anywhere.

## Compatibility considerations
- Against current code the suite fails by design in Phase 1; from Phase 2 on it is a passing regression member.

## Security considerations
- N/A: test suite.

## Rollback considerations
- N/A: the file is additive; revert deletes it.

## Validation plan
- Phase 1: `uv run pytest tests/shared/test_mcp_dedup_identity.py` — confirm and record failures.
- Phase 3+: same command green.

## Completion criteria
- AC-4/AC-5 store-level guarantees pass after row 01 lands; Phase 1 evidence recorded; legacy fixtures pin the pre-change shape.

## Out of Scope
- Concurrency races (row 10), dispatcher refusal mapping (row 02), docs runbook (row 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the suite (new file) against current code | Completed | 20261121-104530 | 20261121-104703 | Suite written: 13 tests, 4 classes; legacy fixture inline. |
| 2 | Run Phase 1 evidence pass and record failures (feeds UNK-05 answer) | Completed | — | 20261121-104703 | Phase1 evidence: 13/13 FAILED (AttributeError start_state/DedupStoreError/resolve_store; OperationalError no such table store_meta; resolve_lost_store still present; user_version pin 0). Current store has no identity row, marker, or start-state classification; touch() shape present in source. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-111007 | Targeted suite green after row 01 landed (10: 9/9, 11: 13/13; combined 22/22). ruff check/format green. mypy scope excludes tests/shared per pyproject files list. |

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
- **Requirement ID**: REQ-005..REQ-007
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `tests/shared/test_mcp_dedup_identity.py`