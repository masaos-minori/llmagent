## Goal
Remove the removed strict keys from the validator fixture in `tests/shared/test_config_loader.py` (`REQ-001`).

## Scope
**Release unit**: strict-only-startup

## Assumptions
- Lands in the same change as, or after, the code rows it exercises (Plan rows 01-16 and 75); a test edit alone leaves the suite red until the code row lands.
- The Plan's Phase 1 step does not cite this file's path, so the release-unit default is kept (the Plan's `### Release units` entry names the phase, not each file).
- After `scripts/agent/production_config_validator.py` (row 01) drops the keys, the validator reports them as unknown, so leaving them in the payload would make this test fail.

## Design decisions
- Keep the test's intent (known keys pass in production) and shrink the payload to the real dataclass field.

## Alternatives considered
N/A: test-only change

## Implementation
### Target file
`tests/shared/test_config_loader.py`

### Procedure
- In `test_known_keys_pass_in_production` (around line 488) delete the two payload entries `"tool_definitions_strict": True` and `"routing_drift_strict": True` (lines 497-498) and the comment fragment `include required strict keys` (line 493).

### Method
- The payload becomes `{"llm_url": "http://localhost:8080"}`; the assertion `len(result.errors) == 0` is unchanged.

### Details
- If the validator still reports an error for this minimal payload after row 01, the cause is in row 01, not here; do not re-add keys.

## Compatibility considerations
N/A: test-only change

## Security considerations
N/A: test-only change

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/shared/test_config_loader.py -v`

## Completion criteria
- Neither strict key appears in the file.
- `test_known_keys_pass_in_production` passes with the shrunken payload.

## Out of Scope
- Adding the removed-key rejection test (it lives in `tests/agent/test_production_config_validator.py`, row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tests/shared/test_config_loader.py` per Procedure/Method/Details | Done | 20261110-172551 | 20261110-172551 | payload rewritten; see Verification Findings |
| 2 | Run `uv run pytest tests/shared/test_config_loader.py -v` and fix remaining fixtures in this file only | Done | 20261110-172551 | 20261110-172551 | 50 passed; ruff clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 20261110-172551 | — | file-level green; full gate deferred to batch end |

### Verification Findings
- (corrected) the Method's shrunken payload `{"llm_url": ...}` fails `len(result.errors) == 0` against the landed row-01 validator, which rejects an absent `allowed_root`. The payload was changed to `{"llm_url": ..., "allowed_root": "/opt/llm"}` — same resolution as doc 25's known-keys test. The Details' "do not re-add keys" was written before row 01 landed and does not anticipate the now-required `allowed_root`.

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
- **Related target files**: `tests/shared/test_config_loader.py`
