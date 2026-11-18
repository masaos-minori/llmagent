## Goal

Repoint the orchestrator: `tools/run_validation_gates.py` imports `TOOLCHAIN_GATES` from `tools/_validation_gate_toolchain.py` instead of the definition module (Plan REQ-001; AC-1 keeps `_ALL_GATES` composition and gate behavior identical).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the import block edit only.
- Out of scope: the new module (seq 01 document); the definition module's removals and mappings (seq 02 document); the identity test and message updates (seq 04 document).

## Assumptions

- The runner is 23696 B with 880 B of headroom (re-measured 20261118); one added import line stays far under the 24576 B limit (Plan row 3 evidence, corrected at plan revalidation).
- `SOURCE_TOOLCHAIN`, `MODE_FULL`, `Gate`, `ROUTING_GATES`, and the argv helpers keep coming from `tools._validation_gate_defs.py`; only `TOOLCHAIN_GATES` changes source (Plan REQ-001).
- The tests import `TOOLCHAIN_GATES` from this orchestrator (the `noqa: F401` re-export comment records that), so the re-export role must survive the move.

## Design decisions

- Add a separate `from tools._validation_gate_toolchain import TOOLCHAIN_GATES  # noqa: F401 — re-exported for tests/tools/test_run_validation_gates.py` line and drop `TOOLCHAIN_GATES` from the `tools._validation_gate_defs` import list; `_ALL_GATES: tuple[Gate, ...] = (*ROUTING_GATES, *TOOLCHAIN_GATES)` stays untouched (Plan Assumptions: the move is behavior-neutral because the composition and order are kept).

## Alternatives considered

- Have the new module re-export everything and the runner import only from it: rejected — the plan keeps the definition module as the home of the helpers and routing table (REQ-001), and it would obscure the import direction the cycle test asserts (seq 04 document).

## Implementation
### Target file
`tools/run_validation_gates.py`
### Procedure
1. In the `from tools._validation_gate_defs import (...)` block (lines 51-63 at revalidation time), delete the `TOOLCHAIN_GATES,` entry.
2. Add directly after that block: `from tools._validation_gate_toolchain import TOOLCHAIN_GATES  # noqa: F401 — re-exported for tests/tools/test_run_validation_gates.py`.
3. Land this change in the same commit as seq 01, 02, and 04 (Plan Phase 1); run `uv run pytest tests/tools/test_run_validation_gates.py -v` after all four land.

### Method
- One import removed, one added; no gate selection, report, or drift logic touched.

### Details
- Keep the existing `SOURCE_TOOLCHAIN` entry's `noqa: F401` re-export comment in the defs import block (tests import it from here).
- The module docstring and `_ALL_GATES` need no edit: neither hardcodes the definition module as the toolchain table's home (checked 20261118).

## Compatibility considerations

- The commit skill, the drift pre-commit hook, and the test module run this orchestrator (Plan Affected areas: blast radius Medium); its behavior is unchanged because the imported object is the same table content moved verbatim.
- Import direction stays one-way: this module imports both gate modules; the gate modules import neither the runner nor each other in a cycle (seq 01 and seq 04 documents carry the cycle guard).

## Security considerations

- N/A: an import edit only.

## Rollback considerations

- Restore the previous import block; the runner works against the pre-move definition module again (same commit revert as seq 01/02/04).

## Validation plan

- `uv run python tools/run_validation_gates.py drift` → parity report (AC-3; after Phase 2 lands the two new rows).
- `uv run pytest tests/tools/test_run_validation_gates.py -v` → identity test passes against the new module (AC-1, seq 04 document).
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` → passes (AC-6).

## Completion criteria

- `TOOLCHAIN_GATES` is imported from `tools._validation_gate_toolchain`; the test suite's identity test and the toolchain parity tests pass; the size gate passes (AC-1, AC-6).

## Out of Scope

- `tools/_validation_gate_toolchain.py` (seq 01), `tools/_validation_gate_defs.py` (seq 02), `tests/tools/test_run_validation_gates.py` (seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-102014 | 20261118-103141 | import repointed: TOOLCHAIN_GATES now from tools._validation_gate_toolchain with the noqa F401 re-export comment; ruff --fix wrapped the import to satisfy I001 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261118-103141 | Covered by the seq 04 document N/A: covered by the seq 04 document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261118-103141 | file-level ruff format/check, mypy: clean; test_reexported_gate_definitions_are_the_same_objects passes against the new module; runner 23820 B under the limit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261118-103141 | Module rows are the seq 07 document N/A: module rows are the seq 07 document |

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
- **Requirement ID**: `REQ-001` (import from the new module), `REQ-006` (size gates)
- **Source issue**: issues/20261117-123333_wftool004_orphan-tool-routing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125207_wftool004_orphan-tool-routing.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-043152
- **Related target files**: `tools/run_validation_gates.py`