## Goal
Add unit-test fixtures to `tests/tools/test_check_agent_docs_consistency.py` covering a valid and a stale bare snake_case reference and a non-`_db_path` config key, so the extended `check_docs_consistency.py` detection has regression coverage.

## Scope
- Modify exactly `tests/tools/test_check_agent_docs_consistency.py`: add fixtures/tests for the uncovered reference forms selected in Phase 1 (UNK-02).
- This row exists only if the mechanical branch is chosen (owner decision, REQ-001). If the owner records an accepted limit instead, leave this file unchanged.

## Assumptions
- The owner's decision is recorded before this executes (Plan REQ-001); this documents the mechanical-branch test sub-case so it can be applied once decided.
- The check emits at Warning level and passes on the current corpus; tests assert the new forms are reported (Warning) and valid forms are not.

## Design decisions
- Extend the existing test module (which already covers `check_function_references` and other generic checks) with focused fixtures for the uncovered forms.
- Keep fixtures minimal: one valid (defined) and one stale (undefined) reference per uncovered form.

## Alternatives considered
- A separate test module: rejected — the named `tests/tools/test_check_docs_consistency.py` does not exist; the real module is `test_check_agent_docs_consistency.py`, which already holds the generic-check tests.
- Recording an accepted limit instead: out of scope for this row — only applies if the mechanical branch is not chosen.
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`tests/tools/test_check_agent_docs_consistency.py`

### Procedure
1. Confirm the owner's decision is recorded (REQ-001). If absent, stop and report; do not infer.
2. Confirm the mechanical branch was chosen (else skip this file).
3. Identify the exact uncovered forms implemented in `check_docs_consistency.py` (UNK-02).
4. Add a fixture with a valid (defined) bare snake_case name and a stale (undefined) one; assert the stale one is reported at Warning and the valid one is not.
5. If non-`_db_path` config keys were added, add a valid/stale config-key fixture pair.
6. Run the suite; confirm green.

### Method
- Locate the existing generic-check tests (they import `check_function_references`). Add new test methods following the same `tmp_path` fixture pattern, calling the relevant check function with a small docs dir containing the fixture references.

### Details
- Verified at planning time: the module imports `check_function_references` (L24) and already contains `test_*` methods for link/file-ref checks. The exact uncovered forms are a Phase 1 decision (UNK-02). If implementing requires a file not listed in `Implementation Target Files`, that is an additional-target-file discovery — stop and report `Blocked`.

## Compatibility considerations
- Tests target the tool's public check functions; keep signatures compatible. Existing tests must stay green.

## Security considerations
N/A: test-only additions over in-memory fixtures; no secrets, network, or access changes.

## Rollback considerations
Revert the commit that edits this test module.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| New fixtures | Unit | `uv run pytest tests/tools/test_check_agent_docs_consistency.py` | Stale uncovered forms reported (Warning); valid forms clean; existing suite green |

## Completion criteria
- Fixtures for a valid and a stale uncovered reference exist and pass.
- Existing `test_check_agent_docs_consistency` suite is green.
- `ruff`, `mypy`, `bandit` pass on any changed tool.

## Out of Scope
- Writing tests for forms outside the selected uncovered set.
- Testing a blocking gate (none is introduced).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add valid/stale fixtures for the uncovered reference forms | Pending | — | — | Only if the mechanical branch is chosen (REQ-001) |
| 2 | Run the existing suite + lint/type/bandit | Pending | — | — | Depends on step 1 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (mechanical / accept-limit) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` and `REQ-003` — fixture tests for valid/stale bare snake_case references and non-`_db_path` config keys
- **Source issue**: `issues/20261021-100351_identmatch_extend-identifier-matching-to-snake_case-names-and-config-keys-in-docs-verification.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-125149_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-135205
- **Related target files**: `tests/tools/test_check_agent_docs_consistency.py`
