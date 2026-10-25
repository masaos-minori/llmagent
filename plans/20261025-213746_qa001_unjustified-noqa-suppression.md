# Plan: qa001 unjustified noqa suppression

## Goal
- Remove the repository's only unjustified lint-suppression comment (`# noqa: ARG001` at
  `tests/agent/test_session_restore.py:355`) so that
  `tools/check_suppression_justification.py` reports a clean baseline, without changing
  any test behavior.

## Priority
Medium

## Scope
- **In-Scope**:
  - Delete the `# noqa: ARG001` suppression from `tests/agent/test_session_restore.py:355`.
  - Re-run ruff, the affected test file, and `tools/check_suppression_justification.py` to
    confirm the removal is clean.
- **Out-of-Scope**:
  - Removing the unused `mock_llm_call` parameter from the `_make` fixture (the Issue's
    P3 shows the same signature already exists warning-free at `:366`; parameter removal
    is not required by any gate).
  - Any change to `pyproject.toml` ruff selection or to CI ruff scope (Issue P4/P5:
    neither tooling layer reaches tests/ today; leaving them unchanged is the verified
    safe state).
- **Dependencies**: N/A: none.

## Background
`tools/check_suppression_justification.py` enforces the suppression policy defined by
the `python-lint-typecheck` skill (suppressions are allowed only for false positives
and performance-critical exceptions, with a reason and a justification comment). The
Issue reports exactly one suppression in the repository violates that policy.

## Problem
`tests/agent/test_session_restore.py:355` carries `# noqa: ARG001` with no accompanying
justification. Verified at HEAD `b0415bd3d`: `check_suppression_justification.py`
reports 1 issue at this exact location, and `ruff check tests/agent/test_session_restore.py`
is clean when the noqa is removed (measured), because ruff's selection
(`["E", "W", "F", "I", "UP", "BLE001"]`) never selects `ARG`, CI ruff only covers
`scripts/`, and `tools/run_validation_gates.py` does not validate anything under
`tests/`. The suppression is therefore inert and resolvable directly — outcome (a) of
the Issue's Options section, not outcome (b).

## Reason for Change
The Issue (2026-10-25 review, head `2e87bad46`) flagged the suppression as the sole
remaining violation of the Step 4 suppression-justification policy. Leaving it keeps
the suppression audit baseline dirty and weakens the policy's enforcement signal.

## Implementation Intent
Comment-only deletion. No signature, fixture, or assertion changes. Validate with the
three existing tools (ruff, pytest, suppression checker) rather than adding new tooling.

## Requirements
- `REQ-001`: Remove the `# noqa: ARG001` suppression comment from
  `tests/agent/test_session_restore.py` without altering the `_make` signature or any
  test behavior.
- `REQ-002`: After removal, `ruff check tests/agent/test_session_restore.py`,
  `pytest tests/agent/test_session_restore.py`, and
  `check_suppression_justification.py` (issue count 0) must all pass, proving outcome
  (a) — no CI ruff or gate gap remains.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/agent/test_session_restore.py | Delete the `# noqa: ARG001` comment on line 355 | Only unjustified suppression in the repo; inert under current ruff selection | REQ-001, REQ-002 / AC-1, AC-2 | Issue P1–P3; `check_suppression_justification.py` reports 1 issue; `pyproject.toml` `[tool.ruff.lint] select` excludes ARG; measured `ruff check` clean after removal | tests/agent/test_session_restore.py (self) | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| tools/check_suppression_justification.py | Understand what counts as a justified suppression so the post-removal clean baseline is interpretable | REQ-002 |
| pyproject.toml | Confirm `[tool.ruff.lint] select` never selects `ARG` (why the noqa is inert) | REQ-002 |
| tests/agent/test_session_restore.py (line 366 region) | The identical signature at `:366` carries no noqa, proving removal cannot trigger tooling errors | REQ-001 |

## Acceptance Criteria
- `AC-1` (REQ-001): `grep -n "noqa" tests/agent/test_session_restore.py` returns no
  match; the diff touches only the comment text.
- `AC-2` (REQ-002): `uv run ruff check tests/agent/test_session_restore.py` exits 0;
  `uv run pytest tests/agent/test_session_restore.py -q` passes; `uv run python
  tools/check_suppression_justification.py` reports 0 issues.

## Tests
- `REQ-002`: Run the existing test file unchanged (`uv run pytest tests/agent/test_session_restore.py -q`)
  — behavior must be identical before and after the comment removal. No new tests:
  the change is comment-only.

## Documentation Impact
N/A: No `docs/*.md` describes this test file's fixture comments; the change removes a
suppression rather than altering documented behavior.

## Assumptions
- The live CI pipeline is the GitHub workflow set under `.github/workflows/` verified in
  the Issue (ruff scoped to `scripts/` only); no separate ad-hoc ruff invocation covers
  `tests/` with an `ARG`-selecting configuration.
- `mock_llm_call` remains an unused fixture parameter by design (mirrors the clean
  sibling fixture at `:366`); leaving it is not itself a violation.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | None. All five Issue claims (P1–P5) verified against source and measured tool runs at HEAD `b0415bd3d`. | N/A: no unresolved evidence gap | N/A | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/agent/test_session_restore.py | Comment-only deletion | None (test-only, no runtime consumer) | N/A: Path A skipped historical analysis | N/A: Path A skipped historical analysis | File is rsynced to `/opt/llm/tests/` by deploy.sh; no new dependencies; no service restarts required |

## Design
No design decision required: single comment deletion validated by existing gates
(ruff, pytest, suppression checker). Outcome (b) of the Issue (retaining the noqa
under a CI gap) was ruled out by measurement — no tooling layer selects `ARG` over
tests/, so there is no gap that would force keeping the suppression.

## Implementation steps

1. **Phase 1: Suppression removal**
   - [ ] Delete the `# noqa: ARG001` comment from `_make`'s signature (REQ-001; tests/agent/test_session_restore.py)
2. **Phase 2: Verification and deployment check**
   - [ ] Run `uv run ruff check tests/agent/test_session_restore.py` and `uv run pytest tests/agent/test_session_restore.py -q` (REQ-002; tests/agent/test_session_restore.py)
   - [ ] Run `uv run python tools/check_suppression_justification.py` and confirm 0 issues (REQ-002; tests/agent/test_session_restore.py)
   - [ ] Deployment validation: confirm the edited file is covered by deploy.sh's `tests/` rsync so the deployed copy converges on next deploy; no service restart needed (REQ-002; tests/agent/test_session_restore.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_session_restore.py | Static lint | `uv run ruff check tests/agent/test_session_restore.py` | exit 0, no findings |
| tests/agent/test_session_restore.py | Unit (existing suite, unchanged) | `uv run pytest tests/agent/test_session_restore.py -q` | all tests pass |
| tests/agent/test_session_restore.py | Policy gate | `uv run python tools/check_suppression_justification.py` | 0 issues reported |

## Risks
- **Risk**: Comment-only change; the only conceivable regression is a future tooling
  change that starts selecting `ARG` over `tests/`, which would flag the unused
  parameter again. → **Mitigation**: the unused parameter mirrors the already-clean
  fixture at `:366`; if `ARG` is ever selected repo-wide, both fixtures get fixed in
  the same pass. No action needed now.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `# noqa: ARG001` from tests/agent/test_session_restore.py | Completed | — | 2026-10-26 | Phase 1 implemented and verified in-session |
| 2 | ruff + pytest + suppression checker verification | Completed | — | 2026-10-26 | Phase 2 implemented and verified in-session |
| 3 | deploy.sh convergence check | Completed | — | 2026-10-26 | Phase 2 implemented and verified in-session |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blockers identified | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261025-210228_qa001_unjustified-noqa-suppression.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-213746
- **Related target files**: tests/agent/test_session_restore.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue P1–P3 (noqa at :355, no justification, clean sibling at :366) | tests/agent/test_session_restore.py | Phase 1 | AC-1 | Validation plan row 1 (ruff) | Explicit in issue |
| REQ-002 | Issue P4–P5 plus measured tool runs at HEAD b0415bd3d (clean ruff without noqa; suppression checker 1→0) | tests/agent/test_session_restore.py | Phase 2 | AC-2 | Validation plan rows 1–3 | Confirmed by repository evidence |