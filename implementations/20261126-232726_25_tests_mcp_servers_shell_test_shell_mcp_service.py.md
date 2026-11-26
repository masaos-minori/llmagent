## Goal

Mark the requirement-cited assertions as `contract`, mark the pass-through case as `characterization`, and
correct the header that presents the pass-through as a guard contract (REQ-003 — mixed module; REQ-007 — a
characterization assertion MUST NOT be presented as normative).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `pytest` is already imported; the module's only requirement citation is REQ-004 at
  `tests/mcp_servers/shell/test_shell_mcp_service.py:318` (the `run_command` audit record).
- `:93-96` locks the empty-allowlist/empty-denylist pass-through in
  `scripts/mcp_servers/shell/shell_service.py:342-350`, which contradicts the documented default-deny filter at
  `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:67`.
- The header at `:1-6` lists `_filter_env` as a guard method without distinguishing the pass-through case, so it
  reads as a contract for behavior no requirement source defines.

## Design decisions

- Module-level `pytestmark = pytest.mark.contract` for the requirement-cited assertions, with per-test
  `@pytest.mark.characterization` on the pass-through test.
- The header states the pass-through as recorded behavior, not as the guard contract, so the reader can tell the
  two kinds apart without running the checker.

## Alternatives considered

- Changing the assertion to match the documented default-deny filter — rejected: that is a behavior change, and
  the conflict is owned by the documentation and the shell service, not by this row.

## Implementation
### Target file
`tests/mcp_servers/shell/test_shell_mcp_service.py`
### Procedure

- Add `pytestmark = pytest.mark.contract` after the imports.
- Add `@pytest.mark.characterization` to `test_no_filters_returns_env_unchanged` at `:93-96`.
- Rewrite the header so the pass-through case is described as recorded behavior with no requirement source.

### Method

- No assertion is changed.

### Details

- The header keeps the two guard methods it already names; only the pass-through wording changes.

## Compatibility considerations

- The module appears in both `-m` selections; the full suite is unchanged.
- The code-versus-document conflict itself is not resolved here; it stays a Known Issue until the shell service
  or the documentation is changed by its owner.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/mcp_servers/shell/test_shell_mcp_service.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`: the mixed module is detected through its per-test
  markers.
- Sequence: lint → type → arch → security.

## Completion criteria

- Every test in the module resolves to exactly one kind, the `contract` part carries a citation, the header no
  longer presents the pass-through as a contract, and the checker reports no finding.

## Out of Scope

- Resolving the default-deny conflict in `scripts/mcp_servers/shell/shell_service.py` or
  `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the markers and correct the header per Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/tool-gates.md` documentation gates and `rules/toolchain.md`) | Pending | — | — | this row is the test itself |

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
- **Requirement ID**: `REQ-003` (per-test markers for a mixed module), `REQ-007` (characterization wording)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/mcp_servers/shell/test_shell_mcp_service.py`
