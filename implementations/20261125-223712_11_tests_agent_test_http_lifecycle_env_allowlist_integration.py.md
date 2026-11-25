## Goal

Replace the static allowlist-alignment gate with a per-server credential gate, and start every shipped subprocess server under its own minimal environment (REQ-006 per-server environment, REQ-007 designated credentials, REQ-009 tests written before the implementation).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file's premise is the wildcard model: it imports `_DEFAULT_ALLOWED_ENV_VARS` (`:31`), matches names against it (`:153`), and starts real children with `CommandValidator().filter_env({})` (`:183`, `:301`). All three are removed by rows 2-3, so the gate is retargeted rather than extended.
- The existing server-entry mapping and shipped-config classification cases (`:214`, `:265`) already enumerate every shipped subprocess server and stay as the enumeration source.

## Design decisions

- The gate becomes per-server: for each shipped server, build its child environment through `build_child_env` (row 2) from the real `config/agent.toml` entry, and compare the resulting key set against that server's own derived tokens plus its declared `credential_env` (AC-3).
- Real-child startup is kept: the minimal environment is proven by a child that actually imports, which is what surfaces a missing variable and resolves UNK-03.

## Alternatives considered

Keeping the static "every `${ENV:...}` reference is allowlisted" check was rejected: it pins the wildcard model it was written to protect, and it cannot express "this server, and not that one".

## Implementation
### Target file
`tests/agent/test_http_lifecycle_env_allowlist_integration.py`
### Procedure
Replace the pattern-alignment cases with per-server key-set cases and retarget the real-child startup to the minimal environment.

### Method
- Delete the `_DEFAULT_ALLOWED_ENV_VARS` import (`:31`), the pattern-matching helper (`:153`), and `test_config_env_refs_are_all_allowlisted` (`:197`); replace them with `test_each_shipped_server_env_is_exactly_its_own` (new), which asserts the exact key set per shipped server.
- Add `test_github_token_only_for_designated_servers` (new): `GITHUB_TOKEN` appears for `github` and `cicd` and for no other shipped server (REQ-007).
- Add `test_no_server_receives_another_servers_token` (new): with every shipped server's tokens present in the parent, each child environment holds only its own two derived tokens (AC-3).
- Retarget the real-child fixture (`:176-195`) to build the environment through `build_child_env` instead of `filter_env` (`:183`), and keep `test_each_subprocess_server_starts_under_filtered_env` (`:234`) as the startup gate for every shipped server.
- Rewrite `test_filter_env_keeps_other_process_tokens_out_of_the_child` (`:296-301`) as the per-server equivalent, and keep `test_allowlist_does_not_admit_denylisted_loader_vars` (`:208`) and `test_other_process_references_are_not_allowlisted` (`:287`) against the narrowed runtime set.
- Update the module docstring's gate questions (`:7`) to the per-server model.

### Details
- Keep `test_missing_token_breaks_the_child_import` (`:250`) as the negative control that proves the gate is real.
- Assert the startup audit line contains key names only, never a value.

## Compatibility considerations

The file is the only importer of `_DEFAULT_ALLOWED_ENV_VARS` outside the validator module, so removing the wildcard patterns (row 3) requires this change in the same unit.

## Security considerations

N/A: this row only asserts the guarantees rows 1-3 and 6 implement.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle_env_allowlist_integration.py`
- Expected outcome before rows 1-3 and 6 land: the retargeted cases fail (Plan Phase 1)

## Completion criteria

- Every shipped subprocess server's child environment is exactly its fixed runtime set plus its own two tokens plus its declared `credential_env` names.
- `GITHUB_TOKEN` appears for `github` and `cicd` only, and every shipped server starts under its minimal environment.
- No case imports `_DEFAULT_ALLOWED_ENV_VARS` or calls `filter_env`.

## Out of Scope

- Implementing `build_child_env` (row 2) and the narrowed allowlist (row 3).
- The `credential_env` values themselves (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test cases described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1: expected to fail until rows 1-3 and 6 land |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (per-server minimal environment), REQ-007 (`GITHUB_TOKEN` only for designated servers), REQ-009 (tests written before the implementation)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `tests/agent/test_http_lifecycle_env_allowlist_integration.py`
