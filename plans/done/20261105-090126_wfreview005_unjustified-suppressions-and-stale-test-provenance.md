## Goal
- Correct the `TestFencingGateAC7` docstring in `tests/agent/workflow/test_stale_recovery_lease.py` so every path it cites exists and its statement of the gate's meaning matches the repository, and confirm that the suppression checker stays at 0 issues.

## Priority
Medium

## Scope
- **In-Scope**: rewrite the docstring references of `TestFencingGateAC7`; re-run `tools/check_suppression_justification.py` and the two affected test files as confirmation.
- **Out-of-Scope**: implementing `AttemptFencedError` or the `finish_attempt` fence; auditing other files for suppression hygiene; any change to test behavior or to the suppression lines.
- **Dependencies**: `N/A: none`. The Issue names wfrecovery001 as open; it is archived (`issues/done/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`, with `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`), so nothing blocks this Plan.

## Background
Adversarial review (2026-11-03) reported two unjustified suppressions and a docstring that cites a nonexistent procedure document.

## Problem
Verified in Step 2, with two corrections to the Issue:
- The suppression half is already resolved. `uv run python tools/check_suppression_justification.py` prints `All checks passed`; both lines carry an em-dash justification (`# noqa: F401 — the import itself is the assertion` at the `AttemptFencedError` import, and `# type: ignore[arg-type] — deliberately passes a non-str ...` in `tests/shared/test_json_utils.py`). Commit `7f00a5d85` ("fix(tests): unblock CI lint on master (#14)") introduced both. No change is needed there.
- The docstring half is still stale. The docstring says the gate is "gated on the wfrecovery001 plan (Pending in plans/done/)" and ends with `See implementations/done/20261031-212239_wfrecovery001_recovery-dag.md`, which does not exist. `AttemptFencedError` is still absent from `scripts/` (`rg` finds nothing), so the gate test's premise holds.
- The Issue lists the wfrecovery001 issue as open under `issues/`; it is under `issues/done/`.

Existing artifacts verified to exist: `issues/done/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`, `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`, `implementations/done/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md` (the conditional `finish_attempt` procedure that the plan for this test file cites), and `implementations/done/20261101-163219_12_tests_agent_workflow_test_stale_recovery_lease.py.md` (the procedure for this test file).

## Reason for Change
The gate test exists to force a review when the fence lands; a docstring that points to nothing breaks that traceability.

## Implementation Intent
Edit only the class docstring: state that the fence is not yet implemented, and cite the four existing paths above. Do not touch code or the suppression lines.

## Requirements
- `REQ-001`: The `TestFencingGateAC7` docstring cites only repository paths that exist (the four listed in Problem) and states that the fence is not yet implemented, without the "Pending in plans/done/" wording.
- `REQ-002`: The change is comment-level: the test file's tests, imports, and suppression lines are unchanged, and `tools/check_suppression_justification.py` reports 0 issues afterward.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/agent/workflow/test_stale_recovery_lease.py` | Fencing gate test | Replace the stale citation in the `TestFencingGateAC7` docstring | REQ-001, REQ-002 / AC-1, AC-2, AC-3 | Class docstring cites `implementations/done/20261031-212239_wfrecovery001_recovery-dag.md`; `ls` finds no such file (checked in Step 2) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tests/shared/test_json_utils.py` | Confirms its suppression is already justified; unchanged | REQ-002 |
| `tools/check_suppression_justification.py` | The checker whose result is the acceptance evidence | REQ-002 |
| `issues/done/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` | Cited artifact | REQ-001 |
| `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` | Cited artifact | REQ-001 |
| `implementations/done/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md` | Cited artifact | REQ-001 |
| `implementations/done/20261101-163219_12_tests_agent_workflow_test_stale_recovery_lease.py.md` | Cited artifact | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-001): every path in the docstring resolves (`ls` on each path exits 0).
- AC-2 (REQ-002): `uv run python tools/check_suppression_justification.py` reports 0 issues.
- AC-3 (REQ-002): `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py tests/shared/test_json_utils.py` passes, and `git diff` of the file shows only docstring lines changed.

## Tests
- `REQ-001`, `REQ-002`: no new tests; run the two affected test files and the suppression checker (Validation plan).

## Documentation Impact
N/A: in-file docstring only; no `docs/*.md` is affected.

## Assumptions
- The fence stays unimplemented until a later piece of work lands it; if a follow-up Issue exists or is filed, the docstring may name it then (see UNK-01).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the fence is still scheduled: `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` carries it, but its `Execution Status` rows are all `Pending` and `AttemptFencedError` is absent from `scripts/` | No `Execution Status` change or open Issue after 2026-11-01 (`rg` in Step 3 finds no open Issue or Plan naming it) | The owner decides whether to resume that Plan or file a follow-up Issue; the docstring cites only existing artifacts and states the current fact | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/agent/workflow/test_stale_recovery_lease.py` | Modify | Low: docstring only | N/A | N/A | None (tests are not deployed) |

## Design
Path A (1 file, no interface or schema change). No consumer scan: no symbol, schema, or constant changes. The Issue's suppression work is already complete, so the Plan narrows to the docstring and records the evidence, rather than re-doing it.

## Implementation steps
1. **Phase 1: Docstring correction**
   - [ ] Rewrite the `TestFencingGateAC7` docstring references (REQ-001; `tests/agent/workflow/test_stale_recovery_lease.py`)
2. **Phase 2: Verification**
   - [ ] Run the suppression checker and the two test files; confirm `git diff` is docstring-only (REQ-002; `tests/agent/workflow/test_stale_recovery_lease.py`). No deploy step: nothing under `scripts/` or `config/` changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/workflow/test_stale_recovery_lease.py` | Existing tests as behavior lock | `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py tests/shared/test_json_utils.py` | Pass |
| same | Suppression governance | `uv run python tools/check_suppression_justification.py` | 0 issues |
| same | Lint | `uv run ruff check tests/agent/workflow/test_stale_recovery_lease.py` | Clean |

Validation quality baseline: `N/A: no Python target under scripts/ or tools/`.

## Risks
- **Risk**: The docstring is edited from the stale Issue text and re-cites an archived path as open → **Mitigation**: the four cited paths were verified to exist in `done/` directories in Step 2; AC-1 re-checks them.
- **Risk**: A reader treats the docstring as proof the fence is planned → **Mitigation**: it states only the verified current fact (fence absent), and UNK-01 records the unresolved ownership.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the docstring references | In Progress | — | — |  |
| 2 | Verify with checker and tests | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261105-092940_01_tests_agent_workflow_test_stale_recovery_lease.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261103-134148_wfreview005_unjustified-suppressions-and-stale-test-provenance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261105-090126
- **Related target files**: `tests/agent/workflow/test_stale_recovery_lease.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes 3; docstring citation checked with `ls` | `tests/agent/workflow/test_stale_recovery_lease.py` | Phase 1 | AC-1 | path-resolution check | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes 1, 2, 4 (already satisfied: checker reports `All checks passed`) | `tests/agent/workflow/test_stale_recovery_lease.py` | Phase 2 | AC-2, AC-3 | suppression checker; pytest | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261105-092940 -->