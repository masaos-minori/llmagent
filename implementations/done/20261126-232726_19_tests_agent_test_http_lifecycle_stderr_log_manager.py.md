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
- Step 3b correction (2026-11-27): that condition is already met — cliplc009's copy-and-truncate rotation
  landed in batch 1, and the rotation tests now carry the requirement citation themselves at `:265` and `:285`
  (REQ-006 / AC-3), so they are `contract`, not `characterization`. The module has four citations, not one:
  `:138`, `:265`, `:285`, `:362`; the plan's `:221` is the REQ-005 citation, now at `:362`. The implementation
  reference is stale: rotation is copy-and-truncate at `scripts/agent/http_lifecycle_stderr_log_manager.py:127-143`,
  not rename-only at `:111-129`. The module no longer mixes kinds, so no per-test marker is added.
- Step 3b note (2026-11-27, owner decision): the uncited tests outside the rotation block (`TestReadTail`,
  `TestStderrLogManagerInit`, `TestOpenLog`, `TestGetLogPath`, `TestForget`, `TestClear`) are not individually
  marked; the marker set is the block named by the plan.

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
- No per-test marker: the rotation tests are requirement-cited (Step 3b correction above).

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
| 1 | Add the markers per Procedure/Method/Details | Completed | 20261127-114755 | 20261127-114755 |  |
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
- **Requirement ID**: `REQ-003` (per-test markers for a mixed module)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/agent/test_http_lifecycle_stderr_log_manager.py`