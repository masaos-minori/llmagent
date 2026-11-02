## Goal
- Add the `ROUTING_GATES` mapping entry for the new routing row so `drift_report()` passes (`REQ-006`).

## Scope
- In scope: one `Gate` entry. Out of scope: `drift_report()`, selection logic, hook parity, and tests (the existing drift test covers it).

## Assumptions
- Step 3a verification: `ROUTING_GATES` entries are `Gate(name, command, source, mode, patterns)`; a token containing `<`, `[`, `]`, or `...` makes the run report `Not available` while the mapping stays (module docstring; the `check_workitem_structure` entry with `<path>` is the precedent). A gate with no `patterns` is never auto-selected.
- The argv MUST equal the seq 07 Run cell tokens exactly: `("uv", "run", "python", "tools/amend_plan.py", "<plan>", "--file", "<path>")`, giving id `amend_plan:<plan>` on both sides.
- Overlap (Step 2): also a target of `plans/20261102-081312_flowimp010_artifact-commit-split.md` and of the Plans filed from flowimp001, 003, and 005. Judged compatible (Plan A7, A7a): each adds an entry or touches other functions; whichever lands second rebases. Anchor: after the `check_workitem_structure` entry; locate by `name`.
- Requires seq 07 in the same change; `drift` fails if either lands alone. `tools/amend_plan.py` is created by seq 01 (acceptable earlier-`seq` reference).

## Design decisions
- `patterns=()`: the trigger is a planning-time event, not a path set, so fast mode never auto-selects it; `mode=MODE_FAST`, `source=SOURCE_ROUTING`.

## Alternatives considered
- Path patterns such as `plans/**`: rejected, a placeholder gate cannot run unattended and the trigger is a discovery during a cycle.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
1. Locate the `check_workitem_structure` `Gate` in `ROUTING_GATES` by its `name` and insert the new `Gate` directly after it.

### Method
- `amend_plan` (new) gate: `Gate(name="amend_plan", command=(("uv", "run", "python", "tools/amend_plan.py", "<plan>", "--file", "<path>"),), source=SOURCE_ROUTING, mode=MODE_FAST, patterns=())`, in the file's one-token-per-line formatting, with a one-line comment that it is a manual planning-time tool with placeholders.

### Details
- No other edit; the entry goes inside the existing tuple.

## Compatibility considerations
- N/A: additive entry; the runner reports `Not available` for it by design.

## Security considerations
- N/A: argv list, no shell; the placeholders block auto-invocation.

## Rollback considerations
- N/A: revert the commit together with seq 07.

## Validation plan
- `uv run python tools/run_validation_gates.py drift`: no unmapped checker (AC-7).
- `uv run pytest tests/tools/test_run_validation_gates.py -v`
- `uv run ruff format tools/run_validation_gates.py`; `uv run ruff check tools/run_validation_gates.py`; `uv run mypy tools/run_validation_gates.py`; `uv run bandit tools/run_validation_gates.py`

## Completion criteria
- The entry exists, `drift` and the drift test pass with seq 07 applied, and the lint sequence is clean (AC-7).

## Out of Scope
- `drift_report()`, hook parity, selection logic, other gates, and edits to `tests/tools/test_run_validation_gates.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the `amend_plan` (new) `Gate` entry after `check_workitem_structure` | Pending | — | — |  |
| 2 | Run `drift` and `tests/tools/test_run_validation_gates.py` | Pending | — | — | Needs seq 07 applied |
| 3 | Run format, ruff, mypy, and bandit on the file (`routing.md` "Adding a new tool") | Pending | — | — |  |

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
- **Requirement ID**: `REQ-006` (gate mapping entry so `drift` passes)
- **Source issue**: issues/20261030-191737_flowimp011_plan-amend-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081027_flowimp011_plan-amend-tool.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085611
- **Related target files**: tools/run_validation_gates.py
