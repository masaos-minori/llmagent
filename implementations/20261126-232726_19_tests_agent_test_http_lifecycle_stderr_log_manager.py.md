## Goal

Mark the requirement-cited assertion as `contract` and the rotation tests as `characterization` (REQ-003 — a
module that mixes both kinds carries per-test markers).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `pytest` is already imported; the only requirement citation is at `:221` (REQ-005,
  `open_log` rejects an invalid server key before touching the filesystem).
- The rotation tests at `:145-160` lock rename-only rotation, matching
  `scripts/agent/http_lifecycle_stderr_log_manager.py:111-129`; no requirement source defines rotation
  semantics, so those tests are `characterization`.
- The classification holds until cliplc009's copy-and-truncate rotation lands; after that the module becomes
  `contract` under the incremental rule.

## Design decisions

- Module-level `pytestmark = pytest.mark.contract` for the cited assertion, with per-test
  `@pytest.mark.characterization` on the rotation tests, so the mixed part is explicit.

## Alternatives considered

- Marking the whole module `characterization` — rejected: `:221` is traceable to a requirement source, so the
  module mixes kinds rather than being purely observational.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_stderr_log_manager.py`
### Procedure

- Add `pytestmark = pytest.mark.contract` after the imports.
- Add `@pytest.mark.characterization` to the rotation tests at `:145-160`.

### Method

- No assertion is changed.

### Details

- The rotation tests are the only tests without a requirement source in this module.

## Compatibility considerations

- The module appears in both `-m` selections; the full suite is unchanged.
- cliplc009 also targets this module for assertion changes — judged compatible, since this row adds markers
  only.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_http_lifecycle_stderr_log_manager.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`: the mixed module is detected through its per-test
  markers.
- Sequence: lint → type → arch → security.

## Completion criteria

- Every test in the module resolves to exactly one kind, the `contract` part carries a citation, and the
  checker reports no finding.

## Out of Scope

- The rotation semantics owned by cliplc009.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the markers per Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (per-test markers for a mixed module)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/agent/test_http_lifecycle_stderr_log_manager.py`
