## Goal

Confirm the `tests/agent/test_llm_turn_runner.py` references to the sensitive-data refusal message remain valid after `REQ-003`/`REQ-004`; no edit is required if the message text is unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `REQ-004` keeps the no-key secret-refusal path: when no key is configured, `save()` raises `RuntimeError` with the fixed refusal message before persisting (`diagnostic_store.py` lines 162-167).
- `REQ-003` removes the `encrypt` argument and encrypts by policy (line 169); it does not touch the no-key refusal branch that emits the message.

## Design decisions
N/A: this row verifies an existing reference; it introduces no design decision.

## Alternatives considered
- **Reword the refusal message.** Not required: the message `"Sensitive information detected in diagnostic content without encryption enabled."` stays accurate once no key means encryption is genuinely not enabled.

## Implementation
### Target file
`tests/agent/test_llm_turn_runner.py`
### Procedure
- Verify the refusal message text is unchanged by `REQ-003`/`REQ-004`; if unchanged, make no edit.
### Method
- Confirm `diagnostic_store.py` still raises `"Sensitive information detected in diagnostic content without encryption enabled."` in the no-key branch (lines 162-167).
- Confirm the three references in `test_llm_turn_runner.py` (lines 392-393, 395-396, 420-421) still match that exact string. If they do, this file needs no change.

### Companion test files
N/A.

## Compatibility considerations
If `REQ-003`/`REQ-004` were to reword the refusal message, these three `side_effect` strings must be updated to match. Verification shows the message is unchanged, so no update is needed.

## Security considerations
The refusal message gates unredacted-secret persistence under the no-key policy (`REQ-004`); confirming the test still exercises the exact message keeps that guard regression-covered.

## Rollback considerations
Revert the commit.

## Validation plan
- Unit: `test_handle_llm_error_does_not_propagate_on_sensitive_refusal` and `..._midturn_refusal` still pass with the current message.
- Command: `uv run pytest tests/agent/test_llm_turn_runner.py`.

## Completion criteria
- `diagnostic_store.py`'s no-key refusal message is unchanged.
- The three `test_llm_turn_runner.py` references match it; no edit to this file.

## Out of Scope
- Changing the refusal message text (out of scope for `REQ-003`/`REQ-004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | No edit required if the refusal message is unchanged (verified) |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261111-163701_diagstore002_diagnostic-store-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261114-161816_diagstore002_diagnostic-store-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-170132
- **Related target files**: `tests/agent/test_llm_turn_runner.py`
