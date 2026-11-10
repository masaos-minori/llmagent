## Goal
Drop the removed `security_profile` keyword from the two `ProductionConfigValidator.validate` calls in `tests/shared/test_shared_boundary_conditions.py`.

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- Row 01 removes the `security_profile` parameter from `ProductionConfigValidator.validate` (`production_config_validator.py:226`), so passing it raises `TypeError`.
- The Plan row cites `REQ-001`, but the hits (lines 166, 180) are `security_profile` (REQ-007, Plan Phase 3). Recorded; no Plan change needed.

## Design decisions
- Keep each test's other arguments (`known_tools=None`, `known_tools=set()`) so the assertions still mean what they say.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/shared/test_shared_boundary_conditions.py`

### Procedure
- Line 166: `validator.validate(config, known_tools=None)` (drop `security_profile="production"`).
- Line 180: `validator.validate(config, known_tools=set())`.

### Method
- Re-format with `uv run ruff format`: both calls now fit on one line.

### Details
- The file has no `tool_definitions_strict`/`routing_drift_strict` hits (the Plan row's count of 2 is the `security_profile` lines).

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/shared/test_shared_boundary_conditions.py -v`

## Completion criteria
- `security_profile` no longer appears in the file.
- The tests pass.

## Out of Scope
- Changing the validator signature (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/shared/test_shared_boundary_conditions.py` per Procedure/Method/Details | Done | 20261110-182600 | 20261110-183000 | Both calls rewritten to single-line `validator.validate(config, known_tools=...)`. |
| 2 | Run `uv run pytest tests/shared/test_shared_boundary_conditions.py -v` and fix remaining fixtures in this file only | Done | 20261110-183000 | 20261110-183000 | 11 passed; no other fixtures needed changes. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-183000 | 20261110-183000 | ruff check + ruff format clean. |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Anchors confirmed against HEAD (`git show`): `security_profile="production"` at lines 166 and 180 only; no strict-key hits in the file | Applied as written |
| VF-2 | An intermediate inspection (pre-edit) had seen a version of this file without the `security_profile` kwargs; at edit time the file was back at HEAD content (external revert observed in this session, see doc 36 blocker log) | Re-verified anchors against `git show HEAD` immediately before editing |

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
- **Requirement ID**: `REQ-001` (per the Plan row); the change itself removes `security_profile` (`REQ-007`)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/shared/test_shared_boundary_conditions.py`
