## Goal
Bring `tests/agent/test_production_config_validator.py` in line with a validator that has no strict keys and no `security_profile` parameter, and add the new rejection cases (`REQ-001`, `REQ-003`, `REQ-007`).

## Scope
**Release unit**: strict-only-startup


## Assumptions
- The validator documents (rows 1) change `ProductionConfigValidator.validate(config, security_profile=..., known_tools=...)` to `validate(config, known_tools=None)`; this document assumes that signature. About 45 call sites in the file pass `security_profile="production"` or `SecurityProfile.PRODUCTION` (`rg -c security_profile` = 65 hits with the strict keys).
- Removed keys are rejected by the existing unknown-key check: `_get_valid_production_keys()` derives valid keys from dataclass fields, so once the two fields leave `ToolConfig` and the explicit `valid_keys.add("security_profile")` is deleted, all three keys produce `Unknown config keys: ...`.
- Empty `allowed_root` rejection in the validator applies when the key is present and empty (mirrors the `allowed_tools=[]` check); an absent key is rejected by the section builder (`config_section_builders.py`), not here, so the many small configs in this file do not need `allowed_root`.

## Design decisions
- Delete cases whose only subject is the removed behavior; keep every case that exercises tier consistency, allowed_tools, unknown keys, registry failure, approval risk floor.
- New cases assert the error text names the key (`Unknown config keys`, `allowed_root`), not exact full messages.

## Alternatives considered
Keeping `security_profile` as an ignored optional argument was rejected (`tools/check_compat_shims.py` forbids compatibility shims and `AC-07` requires the name to be gone).

## Implementation
### Target file
`tests/agent/test_production_config_validator.py`

### Procedure
- Delete `TestProductionConfigValidatorStrictKeys` (starts line 13), `TestProductionConfigValidatorSecurityProfileEnum` (line 235), and `TestSecurityProfileCoercion` (line 247) in full, and the `from shared.mcp_config import SecurityProfile` import (line 9).
- In every remaining `validate(...)` call remove the `security_profile=` argument (lines 24-381, 421-490 per `rg -n security_profile`), keeping `known_tools=` as a keyword.
- Remove `tool_definitions_strict`/`routing_drift_strict`/`security_profile` entries from config literals (around lines 415-418, 426, 439, 454, 467, 488); rename `test_valid_keys_only_no_errors` fixtures accordingly.
- In `test_valid_key_set_unchanged_after_schema_consolidation` (around line 520-529) replace `assert "security_profile" in keys` with `not in keys` and add `tool_definitions_strict`/`routing_drift_strict` `not in keys`.
- Add `TestRemovedKeysRejected` (new): parametrize over the three removed key names, `validate({key: True})`, assert an error contains `Unknown config keys` and the key name.
- Add `TestAllowedRootRejection` (new): `{"allowed_root": ""}` yields an error naming `allowed_root`; `{"allowed_root": "/opt/llm"}` yields none for that key.
- Keep the `allowed_tools=[]` error cases (around lines 186-232) unchanged apart from the argument removal; add one case asserting `validate({})` has no errors.

### Method
- Do edits with Edit; after the deletions run `uv run pytest tests/agent/test_production_config_validator.py -v` once the validator document is implemented, since the file cannot pass before the signature change.

### Details
- Plan wording gap (no extra file): this row's Plan text says "strict toggles" and cites REQ-001, but the file also uses `security_profile`/`SecurityProfile`, which `AC-07` requires to be absent from `tests/`; the same edit removes them. No additional target file is involved.
- `test_integration_real_config_agent_toml` (the `@pytest.mark.integration` case near the end) loads the real `config/agent.toml` and passes only after the config document lands in the same change.

## Compatibility considerations
Test-only. Order dependency: land with the validator, dataclass, registry, builder, and `config/agent.toml` documents (release unit).

## Security considerations
Keeps `allowed_tools=[]` as an error and adds `allowed_root` empty as an error; no check is weakened.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_production_config_validator.py -v`
- `uv run ruff format` and `uv run ruff check` on the file
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run pytest tests/agent tests/shared tests/integration -v` (full Phase 5 pass once every document is implemented)

## Completion criteria
- No reference to `security_profile`, `SecurityProfile`, `tool_definitions_strict` or `routing_drift_strict` remains except the removed-key rejection parametrization (`AC-01`, `AC-07`).
- Rejection tests for the three removed keys and for empty `allowed_root` pass (`AC-03`).

## Out of Scope
- The validator and builder source edits (their own documents).
- Reload-path coverage in `tests/agent/services/test_config_reload.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the strict/profile test classes and the `SecurityProfile` import; strip `security_profile=` from the remaining calls and the removed keys from config literals | Done | 20261110-172551 | 20261110-172551 | bulk conversion; 4 even_with_local_profile twins merged into production twins |
| 2 | Add `TestRemovedKeysRejected` (new) and `TestAllowedRootRejection` (new); update the valid-key-set assertions | Done | 20261110-172551 | 20261110-172551 | added as `TestRemovedKeysRejected` incl. allowed_root empty/absent/clean cases; `pytest -v`: 41 passed; ruff clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261110-172551 | 20261110-172551 | file-level ruff+pytest green; broader tests/agent red only for files importing SecurityProfile (rows 34/38/40/41 pending); full gate deferred to batch end |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Verification Findings
- (confirmed) strict-by-default already unconditional: `_REQUIRED_NOT_FALSE_KEYS` runs for every config; no profile gate remains in validator or drift detector.
- (confirmed) this is the only test file for `ProductionConfigValidator`.
- (corrected) the Assumption "validator rejects only a present-and-empty allowed_root" is stale vs the landed doc-01 code: the error is `allowed_root is empty or absent (the path jail would be disabled; set an absolute directory)`; tests assert empty AND absent rejection.
- (deviation) `ConfigValidationResult` has no `is_valid` attribute; the suggested snippets' `result.is_valid` assertions were rewritten against `result.errors`.
- (deviation) the 4 `even_with_local_profile` tests became exact duplicates of their twins after the profile arg was dropped; merged into single tests rather than keeping identical pairs.

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-007` (drop strict and profile cases; add removed-key and empty `allowed_root` rejection)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_production_config_validator.py`
