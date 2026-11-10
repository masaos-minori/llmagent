## Goal
Drop the removed `routing_drift_strict` toggle from the `_make_ctx` fixture of `tests/agent/test_startup_mcp_starter.py` (`REQ-001`: strict is the only behavior).

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- The Plan's Phase 1 step does not cite this file's path, so the release-unit default is kept (the Plan's `### Release units` entry names the phase, not each file).
- `check_routing_drift(ctx, *, strict=...)` in `scripts/agent/services/routing_drift.py` is not a Plan target and keeps its `strict` argument, so the function-level `check_routing_drift` tests at the top of the file stay valid; if the maintainer later removes that argument, this document needs a revision and `routing_drift.py` needs a Plan amendment (reported as a possible additional target in the cycle report).

## Design decisions
- Remove the fixture line only; the fixture's `cfg` is a `MagicMock`, and `check_routing_drift` receives strictness as an argument, so the attribute was never read here.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_startup_mcp_starter.py`

### Procedure
- In `_make_ctx` (line 20) delete `cfg.tool.routing_drift_strict = False`.

### Method
- Single-line deletion; leave `test_routing_drift_non_strict_returns_warnings` (line 22), `test_routing_drift_strict_raises` (line 43) and the other `check_routing_drift` tests unchanged.

### Details
- Confirm with `rg -n routing_drift_strict tests/agent/test_startup_mcp_starter.py` that nothing remains.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_startup_mcp_starter.py -v`
- `uv run ruff check tests/agent/test_startup_mcp_starter.py`

## Completion criteria
- `routing_drift_strict` no longer appears in the file.
- The file's tests pass.

## Out of Scope
- Removing the `strict` argument of `check_routing_drift` (not a Plan target).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_startup_mcp_starter.py` per Procedure/Method/Details | Pending | — | — | |
| 2 | Run `uv run pytest tests/agent/test_startup_mcp_starter.py -v` and fix remaining fixtures in this file only | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (strict toggles removed)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_startup_mcp_starter.py`
