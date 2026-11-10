## Goal
Delete the "non-production mode is rejected" regression and the strict/profile arguments from `tests/integration/test_production_security_regression.py` while keeping the production-only checks (`REQ-001`, `REQ-007`).

## Scope
**Release unit**: strict-only-startup


## Assumptions
- `test_production_only_rejects_local_mode` (line 35-47) asserts `SecurityProfile` has no `LOCAL` member; with the enum deleted it has no subject and is removed (Plan REQ-007).
- `test_strict_configuration_validation_via_real_startup` (line 53-?) still has value as a validator regression on tier consistency and `allowed_tools=[]`; its strict-key arguments and assertions are removed.
- The auth probe `_AUTH_PROBE_SCRIPT` (line 289-299) calls `attach_auth_middleware(app, sys.argv[2])` with a non-empty token and does not pass `accept_all_for_tests`; it stays untouched and must remain valid after the `server.py` change.

## Design decisions
- Keep one test of the real validator; drop discovery-fixture attributes that no longer exist (`security_profile`, `tool_definitions_strict`).

## Alternatives considered
Replacing the deleted regression with an assertion that the removed key is rejected was rejected here: row 19 owns removed-key rejection.

## Implementation
### Target file
`tests/integration/test_production_security_regression.py`

### Procedure
- Delete `test_production_only_rejects_local_mode` and the REQ-001 section comment that introduces it.
- In `test_strict_configuration_validation_via_real_startup`: remove the two strict keys from `config` (lines 62-63), call `validate(config, known_tools={"real_tool"})` (drop `security_profile="production"`), and replace the assertions on `tool_definitions_strict`/`routing_drift_strict` in `joined` (lines 72-73) with assertions on `unknown_tool` and `allowed_tools`.
- In the two discovery tests (around lines 170-250) remove `SecurityProfile` from the local import blocks (lines 178, 225), delete `security_profile=SecurityProfile.PRODUCTION` (lines 200, 245) and `tool_definitions_strict=False` from the `tool=types.SimpleNamespace(...)` (lines 203, 248), keeping `tool_definitions=[]`.

### Method
- `uv run ruff check` flags the now-unused imports; remove them.

### Details
- Plan wording gap (no extra file): this row's Plan text says "strict toggles" and cites REQ-001, but the file also uses `security_profile`/`SecurityProfile`, which `AC-07` requires to be absent from `tests/`; the same edit removes them. No additional target file is involved.
- The required-server FATAL and optional-server WARNING expectations come from server reachability, not strictness, so they are unchanged.

## Compatibility considerations
Test-only; release unit because the dataclass fields these fixtures set are removed in the same change.

## Security considerations
Removes a test that guarded an enum that no longer exists; the production validator and auth probe coverage stay.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/integration/test_production_security_regression.py -v`
- `uv run ruff format` and `uv run ruff check` on the file
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run pytest tests/agent tests/shared tests/integration -v` (full Phase 5 pass once every document is implemented)

## Completion criteria
- No `SecurityProfile`, `security_profile`, `tool_definitions_strict` or `routing_drift_strict` remains; the auth probe test passes; the file passes (`AC-01`, `AC-07`).

## Out of Scope
- `scripts/mcp_servers/server.py` change (own document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the local-mode regression and rewrite the validator regression without strict/profile arguments | Done | 20261110-172551 | 20261110-172551 | module docstring's test list updated too |
| 2 | Remove profile and strict attributes from the two discovery tests | Done | 20261110-172551 | 20261110-172551 | see Verification Findings for the corrected expectation |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 20261110-172551 | — | file-level ruff+pytest green (8 passed, 1 skipped); mypy deferred to the code-batch end gate |

### Verification Findings
- (corrected) the Details claim "the required-server FATAL and optional-server WARNING expectations are unchanged" is stale for `test_optional_mcp_failure_disables_only_that_tool`: after the discovery change (doc 03), the tool-definition check has no non-strict bypass, so an all-unreachable fixture produces a FATAL finding. The test was rewritten to the canonical semantics already asserted by `tests/agent/services/test_mcp_tool_discovery.py::test_unreachable_non_required_server_tool_definition_check_is_fatal`: escalation-axis WARNING + FATAL "cannot validate tool definitions".
- (confirmed) the auth probe test passes unchanged against `attach_auth_middleware(app, token)` after the `server.py` change (doc 11).

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
- **Requirement ID**: `REQ-001` (and `REQ-007`: delete the profile regression)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/integration/test_production_security_regression.py`
