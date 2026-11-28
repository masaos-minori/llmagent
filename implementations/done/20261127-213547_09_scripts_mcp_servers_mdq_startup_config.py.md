## Goal

Create the single module that loads and validates the production configuration once and exposes the immutable result shared by service, authentication, health, and posture (REQ-007 single configuration source).

## Scope
**Release unit**: N/A: not part of a release unit (Plan step 2 is not listed in any `### Release units` entry)

## Assumptions
- Companion test row (SKILL.md conditions 1-4 hold): `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`.
- `tests/mcp_servers/mdq/test_mdq_config.py` is covered by seq 23, which is not a companion of this row.
- Today three independent loads read the configuration at import: `_load_auth_token()` in `scripts/mcp_servers/mdq/mdq_server.py` (line 77), `MdqService.__init__()` in `scripts/mcp_servers/mdq/mdq_service.py` (line 57), and `_collect_dependencies()` in `scripts/mcp_servers/mdq/health_check.py` (line 114). Each applies its own fallback.
- UNK-04 (non-blocking): no mode flag or new configuration key; the test path supplies explicit values.
- `deploy/deploy.sh` already copies `config/mdq_mcp_server.toml` (line 165), so no deploy change is needed.

## Design decisions
- The module is policy-only: the single I/O is the loader call; no logging of values; errors name field paths only.
- Missing production configuration is a pre-bind failure: the result is produced before the server binds, and no fallback path exists.
- The result is immutable (a frozen mapping or dataclass) so consumers cannot diverge.

## Alternatives considered
- Keep per-module loads and add a shared cache — rejected: each caller applies its own fallback, which is the behavior the requirement removes.

## Implementation
### Target file
`scripts/mcp_servers/mdq/startup_config.py` (new)

### Procedure
- Define `load_startup_config()` (new) that calls `ConfigLoader().load("mdq_mcp_server.toml")` once and returns the validated result.
- Define `StartupConfig` (new) as the immutable result type consumed by `mdq_service.py` (seq 02), `mdq_server.py` (seq 01), `health_check.py` (seq 04), and `mdq_security_validation.py` (seq 05).
- Propagate `ConfigMissingError`, `ConfigParseError`, and `ConfigReadError` from `scripts/shared/config_loader.py` without catching them.

### Method
- Field-path-only error text comes from `ConfigFieldTypeError` in `scripts/shared/config_field_types.py`, which never echoes the configured value.
- The configuration path itself must not appear in the message, so the module formats its own message from the field path rather than reusing the loader exception text.
- Step 3b correction (verified 20261128): `ConfigLoader._load_single()` embeds the resolved filesystem path in every loader exception message (`Config file not found: {path}`, lines 149-156), so "propagate without catching" and AC-6 conflict. Resolved by re-raising the same exception class with a message built from the field path and `from None`, so the path-bearing cause is not carried. The exception type is unchanged, so callers that catch `ConfigMissingError`/`ConfigParseError`/`ConfigReadError` keep working.
- Step 3b correction: `db_path` and `auth_token` are the two keys outside `MdqConfig`, so they are validated here with `strict_str()`; the `MdqConfig` keys stay with seq 06.
- Step 3b correction: the secret keys (`auth_token`) are excluded from `values`, because a frozen dataclass `repr()` would otherwise put the token into any log line that prints the result. `auth_token` is also `field(repr=False)`.
- Step 3b correction: the module holds no module-level result and no cache; `mdq_server.py` (seq 01) calls `load_startup_config()` once at import and passes the result to service construction, health, and the posture gate. A shared cache was rejected by this document's Alternatives, so "loaded once" is a wiring property, not a module property.

### Details
- The auth token is read from the same result; the value is never logged.
- The module does not import `scripts/agent`, so the import-linter contract stays satisfied.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`
  - Procedure: replace `test_load_auth_token_returns_empty_on_config_missing_error` with the pre-bind failure expectation; `test_collect_dependencies_records_config_error` becomes a field-path-only expectation.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`
  - Step 3b correction (20261128): the two replacements assert behavior of `mdq_server._load_auth_token()` and `health_check._collect_dependencies()`, which are changed by seq 01 and seq 04. While the new module has no consumer, those two tests still describe current source and cannot be replaced without breaking the behavior lock, so they stay and the replacement is recorded in seq 01 and seq 04. Replacement landed 20261128 when seq 01 and seq 04 consumed the result: the two tests are replaced by `TestConsumersDoNotDegradeAConfigError`, which pins that the server has no empty-token fallback and that the health path reports no `config` dependency, because a missing production configuration raises before bind. What is added here is `TestStartupConfigPreBindFailure` (8 tests) for the module itself: no fallback, field-path-only messages for the three loader errors, one loader call, immutable result, no value echo, and the token absent from `repr()`.

## Compatibility considerations
- Startup behavior changes for a deployment that relies on the removed fallbacks; seq 11 states the currently-implicit keys explicitly so the values stay the same.

## Security considerations
- Startup errors must contain no paths or secrets (AC-6).
- The auth token value is never written to a log or an error message.

## Rollback considerations
- N/A: delete the new file and revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- One load and one validated result serve service, authentication, health, and posture.
- Missing production configuration fails before bind.
- Startup errors name field paths only.

## Out of Scope
- The strict type primitives (seq 06) and the configuration file content (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | `load_startup_config()` and `StartupConfig` created; loader errors re-raised with field-path-only messages (see Method); secret keys excluded from `values` |
| 2 | Add or update tests per Validation plan | Completed | 20261128 | 20261128 | `TestStartupConfigPreBindFailure` added (8 tests); the two existing degradation tests stay until seq 01 and seq 04 consume the module |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | `uv run pytest tests/mcp_servers/mdq/test_mdq_config_error_degradation.py` 9 passed; ruff/bandit/lint-imports/mypy/test-taxonomy Pass end-of-unit gate 20261128 as recorded in seq 01's gates row |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation is a separate row (seq 27) |

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
- **Related target files**: `scripts/mcp_servers/mdq/startup_config.py`, `tests/mcp_servers/mdq/test_mdq_config_error_degradation.py`