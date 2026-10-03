# Implementation Procedure — Remove dangling Known Issue references from ADR-003

## Goal

Remove the `CI-015` cross-reference clause from `ADR-003`'s `### Known Issues` (`REQ-001`). Resolve the `CI-003` cross-reference per `UNK-01` outcome (removed — `CI-003` resolved; `REQ-003`). If the bullet becomes empty after removals, delete it while preserving the `### Known Issues` header. Result invariant: no dangling-warning for `CI-003`, `CI-015` from `check_known_deviation_sync.py` (`REQ-001`, `REQ-003`).

## Scope

Single modification to `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`: remove two inline parenthetical clauses from the `### Known Issues` pointer bullet (line 472): drop `CI-015` (`REQ-001`), drop `CI-003` (`REQ-003`). If both clauses are gone, delete the now-empty pointer bullet.

## Assumptions

- The affected bullets are pure cross-reference pointers to `governance_03`, not normative ADR decisions, so removing an inline clause does not alter the ADR decision, invariant IDs, statuses, or dates.
- `governance_03` is the authoritative registry for Known Issue state; a pointer without a matching `#### <ID>` heading means the issue is no longer actively tracked there, which is the basis for treating `CI-015`/`CI-003` as removable.
- Removing a now-empty pointer bullet (when all its clauses are dropped) preserves the `### Known Issues` section header structure expected by the checker.
- `CI-003` is confirmed resolved (see `UNK-01` resolution: "treated as resolved; `CI-003` clause removed from `ADR-003`, no canonical entry restored").

## Design decisions

- Delete the entire `ID (description)` clause(s); never reformat an ID to keep full-width punctuation and evade `_ID_LOOKAHEAD_RE`.
- If a bullet's clauses are all removed, delete the whole bullet while preserving the `### Known Issues` header.

## Alternatives considered

- Restoring a `#### CI-003` heading in `governance_03` and retaining the ADR reference: rejected — `UNK-01` resolved to "resolved"; no canonical entry needed.
- Reformatting IDs to evade `_ID_LOOKAHEAD_RE`: explicitly prohibited by the Plan's constraint.

## Implementation

### Target file

`docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`

### Procedure

Remove two inline parenthetical clauses from the `### Known Issues` pointer bullet (line 472).

### Method

Edit — targeted text deletion.

### Details

1. Baseline: confirm current state of line 472 in `ADR-003`'s `### Known Issues` section.
2. From line 472, remove the `CI-015 (...)` clause (`REQ-001`).
   - `CI-015` is confirmed resolved (removed after test coverage was added; see `governance_03` line 118 and commit `ae00c05e`).
3. From the same line 472, resolve the `CI-003 (...)` clause per `UNK-01`: remove it (`REQ-003`).
   - `UNK-01` resolved to "resolved" (2026-10-02); `CI-003` clause removed from `ADR-003`, no canonical entry restored.
4. After both clauses are removed, check if the bullet is now empty. If so, delete the whole bullet while keeping the `### Known Issues` header.
5. Run `uv run python tools/check_known_deviation_sync.py` and confirm no dangling-warning for `CI-003`, `CI-015`, and no new findings (`REQ-001`, `REQ-003`).
6. Run `uv run pytest tests/tools/test_check_known_deviation_sync.py` (`REQ-001`, `REQ-003`).

## Compatibility considerations

None — documentation-only edit with no behavioral effect.

## Security considerations

None — documentation-only change.

## Rollback considerations

Simple revert via `git checkout -- docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`. No code impact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_known_deviation_sync.py` | Regression: ensure the four listed IDs no longer produce dangling warnings and no new findings appear | `uv run python tools/check_known_deviation_sync.py` | No `[WARNING]` for `CI-003`, `CI-015`; pre-existing out-of-scope findings unchanged |
| `tests/tools/test_check_known_deviation_sync.py` | Unit regression | `uv run pytest tests/tools/test_check_known_deviation_sync.py` | All pass; no assertion tied to the four removed references fails |
| `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md` | Documentation sanity (English text, no reformatting to evade lookahead) | manual read + checker | Bullet(s) edited cleanly; IDs not hidden via full-width punctuation |

## Completion criteria

- `REQ-001`, `REQ-003`: `uv run python tools/check_known_deviation_sync.py` reports no dangling-reference warning for `CI-003`, `CI-015`.
- No new `[ERROR]`/`[WARNING]` findings introduced by the edits.
- The two pre-existing dangling warnings and the two `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`) are left untouched (out of scope).

## Out of scope

- Pre-existing dangling warnings reported before translation (`EVENTBUS-001`, `EVENTBUS-003`, `EVENTBUS-004`, `EVENTBUS-009`, `EVENTBUS-010`, `INV-07`, `DESIGN-1`, `DESIGN-2`, `EVENTBUS-008`).
- The `_ID_LOOKAHEAD_RE` lookahead behavior in `tools/check_known_deviation_sync.py` itself.
- Any change to ADR decisions, invariant IDs, statuses, dates, or quoted code.
- The two `[ERROR]` status-mismatch findings (`CI-001` in `ADR-002`, `CI-016` in `ADR-004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — | Documentation-only; no test changes required |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Baseline check: CI-003 and CI-015 references already absent from ADR-003; no edits needed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation updates needed beyond this procedure |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20261001-125540_kdref001_resolve-dangling-known-issue-references-exposed-by-adr-translation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-182813_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-094716
- **Related target files**: docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md