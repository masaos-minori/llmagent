## Goal
- Keep the token-less `MagicMock` servers of `tests/agent/test_startup.py` exercising the enabled-server path after the exemption lands, and correct the duplicated comment about empty-token configurations (`REQ-004`: set `is_disabled=False` on the token-less mocks; correct the comment).

## Scope
**Release unit**: mcp-auth-filter

- The duplicated `mcp_auth` comment and tests in `TestCheckServicesSeverityClassification`, plus two tests of `TestCheckServicesFatalErrorMessageWithRemediation`, in `tests/agent/test_startup.py`. The assertions are unchanged.

## Assumptions
- A `MagicMock` server's `is_disabled` is truthy, so after the production filter (earlier `seq`) a token-less mock is exempt unless `is_disabled=False` is set (checked in Step 3a).
- Token-less mocks exist in four tests: `test_mcp_auth_fatal_when_any_server_missing_token` (one mock), `test_mcp_auth_fatal_lists_all_offending_servers` (two), `test_fatal_error_message_includes_remediation` (one), and `test_fatal_error_message_format_with_multiple_outcomes` (two); the last two assert the fatal outcome's remediation text and message format and were found in Step 3a (Plan corrected).
- `test_mcp_auth_ok_when_all_servers_have_token` uses non-empty tokens and is unchanged.
- Until this procedure runs, the four tests fail against the new filter: an allowed red state of the release unit.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and the overlap with the configuration-only validation Plan is a recorded sequencing dependency.

## Design decisions
- Add `is_disabled=False` only to token-less mocks, keeping `MagicMock`; rewrite the comment with the same wording as its twin in `tests/agent/test_startup_severity_classification.py` so the two stay consistent.
- Do not touch the asserted remediation text: the production remediation string is unchanged.

## Alternatives considered
N/A: a mechanical adjustment fixed by the Plan.

## Implementation
### Target file
`tests/agent/test_startup.py`

### Procedure
1. Replace the comment block that starts `# Servers below use MagicMock rather than a real McpServerConfig`.
2. Change every token-less `MagicMock(auth_token="")` in the four tests above to `MagicMock(auth_token="", is_disabled=False)`.

### Method
Comment, Before:

```python
    # Servers below use MagicMock rather than a real McpServerConfig: row 1's
    # own `_validate_auth_token()` now rejects an empty auth_token at
    # construction time, so an empty-token McpServerConfig can no longer be
    # constructed at all -- this pipeline step is a defense-in-depth check for
    # a ctx assembled some other way (e.g. directly, as these unit tests do),
    # not a path reachable through a real Agent startup once row 1 lands.
```

Comment, After:

```python
    # Servers below use MagicMock rather than a real McpServerConfig. A real
    # enabled server cannot have an empty auth_token (`_validate_auth_token()`
    # rejects it at construction), so the enabled-offender cases build a mock
    # with is_disabled=False. A disabled server may have an empty token and is
    # exempt from the check; a MagicMock's is_disabled is truthy, so it must be
    # set explicitly.
```

Mocks: six occurrences of `MagicMock(auth_token="")` in the four tests become `MagicMock(auth_token="", is_disabled=False)`. Find them with `rg -n 'MagicMock\(auth_token=""\)' tests/agent/test_startup.py`; none may remain without `is_disabled=False`.

### Details
- Leave `MagicMock(auth_token="valid-token")` and `MagicMock(auth_token="also-valid")` as they are.
- Keep every assertion, including the remediation text comparison in `test_fatal_error_message_includes_remediation`.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: synthetic servers and empty or placeholder tokens only.

## Rollback considerations
Revert the commit; this file is part of the release unit, so reverting only it makes its four tests fail against the new filter.

## Validation plan
- `uv run pytest tests/agent/test_startup.py -q` passes in full (collected the file's tests).
- `rg -n 'MagicMock\(auth_token=""\)' tests/agent/test_startup.py` returns nothing.
- `uv run ruff format --check`, `uv run ruff check`, and `uv run python tools/check_mock_patch_targets.py` report no findings.

## Completion criteria
- The four tests still assert a fatal `mcp_auth` outcome, its remediation text, and the outcome format, and the whole file passes (`AC-4`).
- No token-less `MagicMock` server without `is_disabled=False` remains in the file, and the comment no longer claims an empty-token configuration cannot be constructed.

## Out of Scope
- The production filter, the twin tests in `tests/agent/test_startup_severity_classification.py`, the new tests, and the documentation (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the comment and the token-less mocks as described in Implementation > Procedure/Method | Completed | 20261104-165352 | 20261104-165352 |  |
| 2 | Run the whole file and confirm it passes | Completed | 20261104-165352 | 20261104-165352 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Validation plan | Completed | 20261104-165352 | 20261104-165352 |  |

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
- **Requirement ID**: `REQ-004` (existing mocks keep exercising the enabled-server path)
- **Source issue**: `issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095503_disabledauth001_disabled-server-auth-fatal.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-141805
- **Related target files**: `tests/agent/test_startup.py`