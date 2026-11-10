## Goal
Make `_make_turn_ctx` in `tests/integration/test_rag_turn_integration.py` allow the tools under test, since the default `AgentConfig()` has an empty `allowed_tools` that now denies every tool (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- Measured: 5 tests (the `f01`-`f05` cases) fail under deny-on-empty. `ctx.cfg` is a plain `AgentConfig(memory=...)` (line 117), not built through `build_agent_config`, so the load-time rejection does not apply and only `allowed_tools` must change.
- The RAG tools carry no path arguments, so the empty default `allowed_root` is not exercised here.

## Design decisions
- Derive the allowed list from the tools the test already declares in `risk_none_for`; no new constant is needed.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/integration/test_rag_turn_integration.py`

### Procedure
- In `_make_turn_ctx` (line 104), after `ctx.cfg.tool.serial_tool_calls = True` (line 119) add `ctx.cfg.tool.allowed_tools = list(risk_none_for)`.

### Method
- One line plus a short comment: empty `allowed_tools` denies, so the tools under test are listed explicitly.

### Details
- the `f05` case (`test_f05_mixed_success_and_timeout_in_same_round`) passes two tools (`ok_tool`, `timeout_tool`) via `risk_none_for`, so both are allowed.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/integration/test_rag_turn_integration.py -v`

## Completion criteria
- The five tests pass against the fail-closed code.

## Out of Scope
- Switching to `build_agent_config`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/integration/test_rag_turn_integration.py` per Procedure/Method/Details | Done | 20261110-212000 | 20261110-212100 | Added `ctx.cfg.tool.allowed_tools = list(risk_none_for)` right after `serial_tool_calls = True` in `_make_turn_ctx`, with a one-line REQ-002 comment. |
| 2 | Run `uv run pytest tests/integration/test_rag_turn_integration.py -v` and fix remaining fixtures in this file only | Done | 20261110-212100 | 20261110-212100 | 5 passed (the measured five `f01`-`f05` deny-on-empty failures cleared), including `f05` with both `ok_tool`/`timeout_tool` allowed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-212100 | 20261110-212100 | ruff check + ruff format clean. |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchors confirmed: `_make_turn_ctx` at line 104, `ctx.cfg = AgentConfig(memory=...)` at line 117, `serial_tool_calls = True` at line 119; the plain `AgentConfig()` bypasses the load-time rejection as the Assumption states | Applied as written |
| VF-2 | Empty default `allowed_root` not exercised: all calls in the file target `rag_pipeline_search` / fake tools with no path arguments, matching the Assumption | No root change needed |

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
- **Requirement ID**: `REQ-002` (non-empty `allowed_tools`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/integration/test_rag_turn_integration.py`
