## Goal
Reword the two docstrings in `tests/agent/test_startup_config_error.py` that name `security_profile_val`, which `build_agent_config` no longer computes.

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- Row 05 removes the `security_profile_val` plumbing from `scripts/agent/config_builders.py`, so the docstrings would describe code that does not exist (AC-07 greps `security_profile`).
- The Plan's Phase 1 step does not cite this file's path, so the release-unit default is kept (the Plan's `### Release units` entry names the phase, not each file).

## Design decisions
- Docstring-only change; keep the test bodies and assertions.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/agent/test_startup_config_error.py`

### Procedure
- Class docstring (lines 14-15): say `build_agent_config() aborts before any config section is built when agent.toml is missing`.
- `test_missing_agent_toml_raises_config_load_error` docstring (line 22): replace `Execution never reaches security_profile_val computation.` with `Execution never reaches validation or section building.`

### Method
- Edit text only; no code change.

### Details
- `rg -n security_profile tests/agent/test_startup_config_error.py` returns nothing.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_startup_config_error.py -v`

## Completion criteria
- No `security_profile` text remains.
- The tests pass unchanged.

## Out of Scope
- Any behavior change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/agent/test_startup_config_error.py` per Procedure/Method/Details | Done | 20261110-184500 | 20261110-185000 | Both docstrings reworded; test bodies untouched. |
| 2 | Run `uv run pytest tests/agent/test_startup_config_error.py -v` and fix remaining fixtures in this file only | Done | 20261110-185000 | 20261110-185000 | 3 passed, no fixture changes needed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-185000 | 20261110-185000 | Final grep: no `security_profile` text remains; docstring-only change, ruff/mypy N/A beyond unchanged code (ruff check clean on re-run with the batch). |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchors confirmed: `security_profile_val` at lines 14 and 22 only; the file is otherwise docstring-stable | Applied as written |

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
- **Requirement ID**: `REQ-001` (per the Plan row); the change removes a `security_profile_val` reference (`REQ-007`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_startup_config_error.py`
