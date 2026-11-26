## Goal

Classify the module as `contract` (REQ-003 — module marker; REQ-008 — the High-priority backlog issue's
acceptance tests are authoritative).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `pytest` is already imported; the module docstring (`:1-6`) already carries the
  requirement citation for cliplc006 REQ-001, REQ-006, REQ-007.
- The cited assertions are the frozen launch spec and the fixed inheritable environment set (`:24`, `:96`),
  matching `scripts/mcp_servers/shell/shell_service_static_helpers.py:266-283`, where secrets are stripped.
- No characterization section, so the module does not mix kinds.

## Design decisions

- Module-level `pytestmark` only; the existing docstring citation is the requirement source the checker reads.

## Alternatives considered

- N/A: the rule decides the classification; no design choice remains.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_launch_spec.py`
### Procedure

- Add `pytestmark = pytest.mark.contract` after the imports.

### Method

- No assertion is changed.

### Details

- One line.

## Compatibility considerations

- The module is now selected by `-m contract`; the full suite is unchanged.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_http_lifecycle_launch_spec.py -q`.
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
| 1 | Add the marker per Procedure/Method/Details | Pending | — | — | |
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
- **Related target files**: `tests/agent/test_http_lifecycle_launch_spec.py`
