## Goal

Give the new checker a validation gate so a taxonomy violation is caught locally before the CI lint job
(REQ-004 — the checker runs as a local fast gate).

## Scope
**Release unit**: taxonomy mechanism

## Assumptions

- Confirmed in Step 3a: `tools/_validation_gate_defs.py:650-655` shows the `Gate` shape (`name`, `command`,
  `source`, `mode`, `patterns`) and the `check_conftest_integrity` precedent with `tests/` patterns.
- `tests/tools/test_run_validation_gates.py:948-970` fails when a CI lint command has no gate or reviewed
  exception, so the gate and the CI step (document 07) must land together.
- The gate is a routing gate here; `rules/toolchain.md` (document 06) documents the sequence the checker is
  part of, and no test ties a toolchain.md command to `tools/_validation_gate_toolchain.py`.

## Design decisions

- `MODE_FAST`: the checker is a scan over test module sources, cheap enough for the fast gate, and it must
  run on a `tests/` change, not only in full mode.
- Patterns cover `tests/**` plus `pyproject.toml`, because the marker registration the checker reads lives
  there.

## Alternatives considered

- A full-mode-only gate — rejected: a `tests/` change is the common case, and full mode is the slower path.

## Implementation
### Target file
`tools/_validation_gate_defs.py`
### Procedure

- Add one `Gate` entry to `ROUTING_GATES`: `name="check_test_taxonomy"`,
  `command=(("uv", "run", "python", "tools/check_test_taxonomy.py"),)`, `source=SOURCE_ROUTING`,
  `mode=MODE_FAST`, `patterns=("tests/**", "pyproject.toml")`.

### Method

- Place it next to `check_conftest_integrity` so the test-family gates stay grouped.

### Details

- No exception entry is needed in `tests/tools/test_run_validation_gates.py`, because the gate covers the CI
  lint command.

## Compatibility considerations

- `tests/tools/test_run_validation_gates.py` reads the gate list; adding an entry must not change the
  existing selection expectations.

## Security considerations

- N/A: gate definition only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/tools/test_run_validation_gates.py -v` (validation reference; that file is not
  a row of the Plan's target table).
- Gate — `uv run python tools/run_validation_gates.py`.

## Completion criteria

- The CI lint command for the checker has a gate, and the fast-mode selection includes it on a `tests/`
  change.

## Out of Scope

- The checker itself (document 02) and the CI step (document 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the gate entry per Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | no companion row; existing coverage |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (the checker runs as a local fast gate)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tools/_validation_gate_defs.py`
