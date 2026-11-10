## Goal
Give the `_cfg` helper in `tests/agent/test_tool_preparation.py` a non-empty `allowed_root`, since the approval section builder now rejects an empty one (`REQ-003`, fallout row added at the end-of-batch gate).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Lands after row 07 (`scripts/agent/config_section_builders.py` rejects an empty or absent `allowed_root`); measured: 12 tests in this file fail at the 20261110 end-of-batch `pytest tests/` gate, all with `ConfigReloadValidationError: allowed_root is empty or absent` from `_make_ctx`/`_cfg` (line 41 `"allowed_root": ""`).
- The tests exercise `prepare_tool_calls` (schema validation, approval, ordering), not the runtime path jail, so a permissive root preserves each test's intent; the deliberately empty `allowed_tools` is untouched — `prepare_tool_calls` does not consult it (the failures are build-time, not preflight denials).
- `_cfg` patches `ProductionConfigValidator`; the section-builder rejection is not covered by that patch, matching the row 82 finding.

## Design decisions
- Replace only `"allowed_root": ""` with `PERMISSIVE_ALLOWED_ROOT` from `tests.agent._config_test_defaults` (the shared non-empty root, `"/"`), same fixture pattern as rows 46/47/80/81/92/93.

## Alternatives considered
Listing `ALL_TOOL_NAMES` here too was rejected: no failure in this file comes from `allowed_tools`, and keeping the helper's other deliberately-empty values preserves the docstring's stated bypass concern. If a test turns out to need a non-empty `allowed_tools`, pass it through the existing `**overrides`.

## Implementation
### Target file
`tests/agent/test_tool_preparation.py`

### Procedure
- Add `from tests.agent._config_test_defaults import PERMISSIVE_ALLOWED_ROOT` to the import block.
- In the `defaults` dict of `_cfg`, replace `"allowed_root": "",` (line 41) with `"allowed_root": PERMISSIVE_ALLOWED_ROOT,`.
- Update the `_cfg` docstring only if it claims `allowed_root` is deliberately empty (it currently names `allowed_tools`/`tool_safety_tiers`/`approval_risk_rules`, which stay).

### Method
- Run the file; if any test still fails for a non-build reason, record it as a finding for the owning code row rather than loosening the assertion.

### Details
- Importing `_config_test_defaults` evaluates the registry at import time; other test files already do this, so no new ordering risk.

## Compatibility considerations
N/A: test-only change

## Security considerations
The fixture keeps asserting through real config construction; only the path-jail value changes.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_tool_preparation.py -v` (expect all 70 tests green)
- `uv run ruff check tests/agent/test_tool_preparation.py && uv run ruff format tests/agent/test_tool_preparation.py`

## Completion criteria
- No build-time `ConfigReloadValidationError` remains in this file.
- The file passes against the fail-closed code.

## Out of Scope
- Changing `prepare_tool_calls` or the section builder (rows 07/5x).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_tool_preparation.py` per Procedure/Method/Details | Done | 20261110-214000 | 20261110-214100 | Import `PERMISSIVE_ALLOWED_ROOT` added after the `shared.tool_spec` import (isort placement); `"allowed_root": ""` (line 41) replaced with `PERMISSIVE_ALLOWED_ROOT`. Docstring unchanged — it names only `allowed_tools`/tiers/rules, all kept. |
| 2 | Run `uv run pytest tests/agent/test_tool_preparation.py -v` and fix remaining fixtures in this file only | Done | 20261110-214100 | 20261110-214100 | 12 passed (was 12 failed pre-change; the file's 12 tests were the whole file). No `allowed_tools` override needed — confirmed the failures were purely build-time. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-214100 | 20261110-214100 | ruff check (isort fixed) + ruff format clean. |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchor confirmed: `"allowed_root": ""` at line 41 inside `_cfg` `defaults`; failure trace matches `config_section_builders.py:300` | Applied as written |
| VF-2 | Alternatives assessment confirmed: `prepare_tool_calls` never consults `allowed_tools`/`allowed_root`; empty `allowed_tools` kept, all tests green | No further change |

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
- **Related target files**: `tests/agent/test_tool_preparation.py`
