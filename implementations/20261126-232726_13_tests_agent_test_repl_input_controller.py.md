## Goal

Classify the module as `contract` and give it the requirement citation the checker requires (REQ-003 — module
marker; REQ-008 — the High-priority backlog issue's acceptance tests are authoritative).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: no `pytestmark` and no citation today; `pytest` is already imported.
- Under the extended REQ-002 definition (owner decision), the requirement source for this module is the
  archived cliplc001 issue, so the citation must name `issues/done/20261119-145259_cliplc001_repl-input-controller.md`.
- The module's assertions are the acceptance tests for that issue's requirement (single stdin owner, one
  active request, outcome bound to its request), which is what makes it `contract` rather than
  `characterization`.

## Design decisions

- The citation is written in the module docstring as the requirement source, so the checker can read it from
  the AST without importing the module.

## Alternatives considered

- Classifying the module as `characterization` — rejected by the owner decision: the archived issue's recorded
  requirement is an accepted requirement source.

## Implementation
### Target file
`tests/agent/test_repl_input_controller.py`
### Procedure

- Add `pytestmark = pytest.mark.contract` after the imports.
- Add one docstring line naming the requirement source: the archived cliplc001 issue path.

### Method

- No assertion is changed.

### Details

- The docstring's existing one-line summary stays; the citation is appended as a second line.

## Compatibility considerations

- The module is now selected by `-m contract`; the full suite is unchanged.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_repl_input_controller.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`: the `contract` marker is justified by the citation.
- Sequence: lint → type → arch → security.

## Completion criteria

- The module carries `contract`, carries a requirement citation, and the checker reports no finding for it.

## Out of Scope

- The checker (document 02) and the authority-model wording (document 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker and the citation per Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | this row is the test itself |

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
- **Requirement ID**: `REQ-003` (module marker), `REQ-008` (authoritative acceptance tests)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/agent/test_repl_input_controller.py`
