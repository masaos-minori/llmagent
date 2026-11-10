## Goal
Give the SSE-validation `_build` helper in `tests/agent/test_llm_client.py` a non-empty `allowed_root`, since the approval section builder now rejects an absent one (`REQ-003`, fallout row added at the end-of-batch gate).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands after row 07 (`scripts/agent/config_section_builders.py` rejects an empty or absent `allowed_root`); measured: 3 tests fail at the 20261110 end-of-batch `pytest tests/` gate — `TestAgentConfigSseValidation::test_zero_sse_heartbeat_timeout_is_valid`, `test_zero_sse_malformed_retry_is_valid`, `test_zero_sse_reconnect_max_is_valid` — all from `_build` calling `build_agent_config(base)` where the `base` dict carries no `allowed_root` key.
- The other SSE tests (negative-value raises) still pass because the raise happens in `AgentConfig.__post_init__` before the approval-section builder rejects the missing key; only the "is_valid" cases are red.
- `_build` patches `ProductionConfigValidator`; the section-builder rejection is not covered by that patch, matching the row 82 finding.

## Design decisions
- Add `"allowed_root": PERMISSIVE_ALLOWED_ROOT` to the `base` dict from `tests.agent._config_test_defaults` (the shared non-empty root, `"/"`), same fixture pattern as rows 46/47/80/81/92/93.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_llm_client.py`

### Procedure
- Add `from tests.agent._config_test_defaults import PERMISSIVE_ALLOWED_ROOT` to the import block of the `TestAgentConfigSseValidation` test area (module-level imports).
- In the `base` dict of `TestAgentConfigSseValidation._build`, add `"allowed_root": PERMISSIVE_ALLOWED_ROOT,` ahead of `**overrides`.

### Method
- Run the file; if any test still fails for a non-build reason, record it as a finding for the owning code row rather than loosening the assertion.

### Details
- Do not touch the module's other config-building fixtures: only these three tests were measured red; if other `_build`-style helpers in the file show the same absent-key pattern and turn red at the full gate, apply the same one-line fix in this file.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_llm_client.py -v` (expect all tests green)
- `uv run ruff check tests/agent/test_llm_client.py && uv run ruff format tests/agent/test_llm_client.py`

## Completion criteria
- No build-time `ConfigReloadValidationError` remains in this file.
- The file passes against the fail-closed code.

## Out of Scope
- Changing `llm_client.py`, `config_builders.py`, or the section builder.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_llm_client.py` per Procedure/Method/Details | Done | 20261110-214000 | 20261110-214100 | `PERMISSIVE_ALLOWED_ROOT` imported inside `_build` alongside the file's existing function-local `build_agent_config` import (VF-2); `"allowed_root": PERMISSIVE_ALLOWED_ROOT` added to the `base` dict ahead of `**overrides`. |
| 2 | Run `uv run pytest tests/agent/test_llm_client.py -v` and fix remaining fixtures in this file only | Done | 20261110-214100 | 20261110-214100 | 58 passed (was 3 failed: the three `test_zero_sse_*_is_valid` cases). No other `_build`-style helper in the file needed the Details branch. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-214100 | 20261110-214100 | ruff check (isort fixed) + ruff format clean. |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchor confirmed: the `base` dict of `TestAgentConfigSseValidation._build` carried no `allowed_root` key; only the three `is_valid` cases were red, matching the Assumption | Applied as written |
| VF-2 | This file imports `agent.*` inside `_build` (function-local), not at module level; the import was added locally to match the file's convention instead of the doc's "module-level imports" wording | Local import |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure (post-freeze fallout amendment, `tools/amend_plan.py`)
- **Requirement ID**: `REQ-003` (empty or absent `allowed_root` fails closed in test fixtures too)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_llm_client.py`
