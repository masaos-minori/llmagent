## Goal

Classify the module as `contract` (REQ-003 — module marker; REQ-008 — the High-priority backlog issue's
acceptance tests are authoritative).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `pytest` is already imported; the module docstring (`:1-8`) already carries the
  requirement citation for cliplc006 REQ-004, so no citation is added.
- The cited assertions are `:463` (strict confinement is the default, no variable set) and `:534` (only the
  literal `permissive` restores the basename allowlist), which match the requirement recorded in
  `issues/done/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`.
- The module has no characterization section, so it does not mix kinds.

## Design decisions

- Module-level `pytestmark` only; the existing docstring citation is the requirement source the checker reads.

## Alternatives considered

- N/A: the rule decides the classification; no design choice remains.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_command_validator.py`
### Procedure

- Add `pytestmark = pytest.mark.contract` after the imports.

### Method

- No assertion is changed; the docstring citation stays as it is.

### Details

- One line.
- Step 3b note (2026-11-27): the cited assertions are at `:464` and `:539` (the class docstrings of
  `TestCommandValidatorStrictConfinement` at 463 and `TestCommandValidatorPermissiveOptIn` at 538); the plan's
  `:463`/`:534` are the class lines. The docstring citation is at line 5. No change to the procedure.

## Compatibility considerations

- The module is now selected by `-m contract`; the full suite is unchanged.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_http_lifecycle_command_validator.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`.
- Sequence: lint → type → arch → security.

## Completion criteria

- The module carries exactly one taxonomy marker, no assertion changed, and the checker reports no finding.

## Out of Scope

- The checker (document 02) and the authority-model wording (document 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker per Procedure/Method/Details | Completed | 20261127-114755 | 20261127-114755 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-114755 | 20261127-114755 | this row is the test itself this row is the test itself |

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
- **Related target files**: `tests/agent/test_http_lifecycle_command_validator.py`