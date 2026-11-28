## Goal

Build the MDQ security-posture view from the shared validated startup-configuration result instead of re-reading configuration, and keep the posture checks reading only non-sensitive state (REQ-007 single configuration source).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 6 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- Companion test row (SKILL.md conditions 1-4 hold): `tests/mcp_servers/mdq/test_mdq_health_posture.py`.
- Plan Gap recorded by this pass: no `Implementation steps` entry cites `tests/mcp_servers/mdq/test_mdq_health_posture.py`; the row is covered by the plan's Tests section (REQ-007), not by a step.
- `tests/mcp_servers/mdq/test_mdq_security_validation.py` is a related test but not a target row, so it is not a companion; it is run unchanged.
- The shared result is produced by `scripts/mcp_servers/mdq/startup_config.py` (seq 09); this document consumes it.

## Design decisions
- The posture functions take the validated result object, not a config dict, so the posture cannot diverge from what the service and health read.
- The gate outcome is unchanged: the same checks, the same reason codes, only a different input source.

## Alternatives considered
- N/A: the row only changes the input source; no alternative design is implied.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_security_validation.py`

### Procedure
- Change `configured_allowed_dirs()` (line 52) and `build_mdq_posture()` (line 242) to take the startup-configuration result instead of a `Mapping[str, object]` config dict.
- Keep the posture checks reading only non-sensitive state; no path or value is added to the posture output.

### Method
- The functions keep their existing check ids, which `tests/mcp_servers/mdq/test_mdq_security_validation.py::test_ids_match_the_frozen_contract` pins.

### Details
- The `schema_error` tuple the posture consumes today comes from `health_check._collect_dependencies()`; after seq 04 the failure is a reason code, so the posture input carries the code rather than the message.
- Step 3b correction (20261128): verified against current source. `configured_allowed_dirs()` is the only config-reading helper outside `build_mdq_posture()`; `_mdq_config_view()`, `validate_mdq_security()`, and the three path checks take the same input, so the signature change is applied to every function in the module, not only the two named here. `Mapping` stays imported for the `index_stats` parameter.
- Step 3b correction (20261128): the auth-token presence in the posture view cannot be read from `startup.values`, because `values` excludes the secret key, so presence is read from `startup.auth_token`. `run_startup_validation()` receives `startup.auth_token` instead of re-reading the dict.
- Step 3b correction (20261128): this row must execute before seq 04, not after it. `check_health()` passes the shared result to `build_mdq_posture()`, and the view needs the token field the result owns; a config dict cannot supply it, so seq 04 has no runnable input until the signature change lands.
- Step 3b correction (20261128): "run unchanged" does not hold for `tests/mcp_servers/mdq/test_mdq_security_validation.py`, because its `_cfg()` fixture supplied a config dict. The fixture now supplies an explicit `StartupConfig` (values mapping plus the token field), the dropped-key test drops a values key, and the endpoint test supplies that result to the server module instead of patching a configuration read that no longer exists. No assertion or check id is changed.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_health_posture.py`
  - Procedure: point the gate test at the shared startup-configuration result; the hand-made `schema_error` tuple is replaced by the result's field-path failure.
  - Step 3b correction (20261128): the test builds a `StartupConfig` with an empty values mapping, an empty `db_path`, and the token field, and the tuple becomes `("db_file", HEALTH_REASON_SERVER_UNAVAILABLE)`, the pair `check_health()` produces. The logged `check_id:reason_code` pairs are unchanged, so the gate assertion is unchanged.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_health_posture.py tests/mcp_servers/mdq/test_mdq_security_validation.py`

## Compatibility considerations
- N/A: the posture view is consumed only by the startup gate and the tests named in the plan.

## Security considerations
- The posture must not carry the configuration path or any configured value; the existing checks already report counts only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_security_validation.py tests/mcp_servers/mdq/test_mdq_health_posture.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The posture is built from the one shared result, with no independent configuration read in this module.
- The gate outcome and the check ids are unchanged.

## Out of Scope
- The startup loader (seq 09) and the health reason codes (seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | every posture function takes the shared result; token presence read from the result's token field |
| 2 | Add or update tests per Validation plan | Completed | 20261128 | 20261128 | Companion test file is covered by this document gate test builds a StartupConfig; the non-companion validation file supplies explicit values |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | targeted run 20261128: 35 passed (33 validation + 2 posture); ruff/mypy/bandit/lint-imports/module-size/docstrings Pass. Full sequence runs at the end of the release unit end-of-unit gate 20261128 as recorded in seq 01's gates row |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation is a separate row (seq 27) out of scope: documentation is seq 27 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-007 (single validated startup configuration result)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `scripts/mcp_servers/mdq/mdq_security_validation.py`, `tests/mcp_servers/mdq/test_mdq_health_posture.py`