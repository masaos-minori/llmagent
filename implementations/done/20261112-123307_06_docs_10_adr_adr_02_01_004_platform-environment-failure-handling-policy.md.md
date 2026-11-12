## Goal
Make ADR-004's INV-14 verification text cite the new startup-abort test and the registry tests alongside the `required` default tests (`REQ-005`, `REQ-008` / `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The line (about 291) reads `INV-14 ... verified by unit test (`tests/shared/test_mcp_config.py::TestRequiredDefault`)` (checked); the Plan's line 289 has drifted.
- The new test class is created by the `tests/agent/test_startup_validation.py` procedure (seq 01) and must exist before `check_adr_invariant_matrix.py` can pass on the new citation; the node id below follows that procedure's class name.
- Registry tests: `tests/shared/test_component_mandatoriness.py` (`UnknownComponentError` for `ghost_server`).

- Step 3a/3b corrections (2026-11-12): the INV-14 bullet is now at the Manual Review section's second-last bullet (the Plan's line number had drifted); the pending approval line omits the plan name; the ADR had zero headroom under its ceiling, so the ceiling (and the tools baseline) is re-recorded at 34555 in this cycle (user-approved scope extension: `tools/check_docs_structure.py`, `tools/check_module_size_tools_baseline.txt`). The cited test class exists (seq 01 is archived).

## Design decisions
- Keep `TestRequiredDefault` cited and add the abort evidence; do not claim more than the tests prove.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Procedure
1. Rewrite the INV-14 Manual Review bullet to cite the three test sources.
2. Append one `Current Decision Approval (pending)` line.

### Method
- New bullet: `INV-14 (no startup continuation with undefined mandatoriness) verified by unit tests: the default `required` handling (`tests/shared/test_mcp_config.py::TestRequiredDefault`), the registry (`tests/shared/test_component_mandatoriness.py`), and the unmocked startup abort (`tests/agent/test_startup_validation.py::TestComponentMandatorinessAbort`)`.
- Approval line: approver, date, scope 不明; tracked by adrrev012.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); none is written on a maintainer's behalf (UNK-04).
- Execute after seq 01; if the test node id differs from the implemented class name, use the implemented name.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` (only the intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- INV-14 verification cites the default, registry, and startup-abort tests, and every cited node exists; a marked pending approval line exists.

## Out of Scope
- Adding tests (seq 01); the index row (seq 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-171538 | 20261112-171538 | Changed: docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md; tools/check_docs_structure.py and tools/check_module_size_tools_baseline.txt (ceiling re-record, user-approved) |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-171538 | 20261112-173642 | ADR checkers (incl. matrix: cited nodes exist), docs checkers, tools gates pass; preservation reports only the intended test citation and Approval changes (ERROR by design); end-of-batch full suite pending End-of-batch full suite: 12129 passed, 3 failed (mdq-server import tests: database schema message, unrelated, failed in every run). One earlier run also failed the pinned citation-count test, fixed by the user-approved update to tests/test_run_cited_adr_tests.py |

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
- **Requirement ID**: `REQ-005` / `REQ-008` — INV-14 verification cites the startup-abort and registry tests; pending approval
- **Source issue**: issues/20261109-113220_adrrev015_adr-index-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104147_adrrev015_adr-index-matrix.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123307
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`