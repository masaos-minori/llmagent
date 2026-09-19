# config_section_reload's field validators raise a bare ValueError instead of ConfigReloadValidationError

## Priority
High

## Summary
`scripts/agent/services/config_section_reload.py`'s `reload_validated_section()` wraps
only the `dataclasses.replace(cfg, **changed_fields)` call in
`try/except ValueError as e: raise ConfigReloadValidationError(str(e)) from e`. The
subsequent loop that calls each field's `validator_fn(replaced)` is outside that
try/except, so when a validator (e.g. `config_validators.py`'s `_require_positive`)
rejects an out-of-range value, it raises a bare `ValueError` that propagates unwrapped.
14 tests in `tests/agent/services/test_config_reload.py` expect
`pytest.raises(ConfigReloadValidationError)` and fail because they observe the
underlying `ValueError` instead.

## Background
Confirmed via a `git worktree` checkout of `origin/master` at commit `df4a58671` that this
reproduces identically on that commit alone, unrelated to this session's own (Agent/
EventBus reference-table) work rebased on top of it afterward.

## Problem
Any caller of `ConfigReloadService.apply_config`/`apply_config_dict` that catches
`ConfigReloadValidationError` specifically (e.g. to translate it into an HTTP 400 or a
structured reload-rejection response) will not catch a validator-rejected value — it will
see an unhandled `ValueError` instead, which is either an unhandled crash or falls through
to a generic error path depending on the caller. This is a real correctness/error-handling
gap, not only a test-fixture issue.

## Reason for Change
Config reload validation errors (invalid `http_timeout`, `llm_max_tokens`,
`max_tool_turns`, `context_token_limit`, etc.) are exactly the kind of user-facing,
recoverable error that should surface through the documented
`ConfigReloadValidationError` type. Leaking the internal `ValueError` type breaks that
contract for every field with a `validator_fn` (as opposed to only a `dataclasses.replace`
type-level violation).

## Implementation Intent
Extend the existing `try/except ValueError` wrapping in `reload_validated_section()` to
also cover the `validator_fn(replaced)` call — either by moving the validator loop inside
the existing `try` block, or by wrapping it in its own equivalent `try/except ValueError as
e: raise ConfigReloadValidationError(str(e)) from e`. Keep the two failure paths
(dataclass-replace type violation vs. validator-rejected value) producing the same
exception type and an equally informative message; do not merge them into a single vague
message if the current separate messages carry useful distinguishing context.

## Target Files or Areas
- `scripts/agent/services/config_section_reload.py` (`reload_validated_section`)

## Required Changes
- Wrap the `for field_entry in registry_for(section_path): ... validator(replaced)` loop
  so a `ValueError` raised by any `validator_fn` is re-raised as
  `ConfigReloadValidationError(str(e)) from e`, matching the existing
  `dataclasses.replace` wrapping.

## Constraints
Preserve the existing behavior for the `dataclasses.replace` failure path exactly as-is —
only extend coverage to the validator loop.

## Acceptance Criteria
- `uv run pytest tests/agent/services/test_config_reload.py -q` reports 0 failures.
- A validator rejection (e.g. `http_timeout=0`) raises `ConfigReloadValidationError`, not a
  bare `ValueError`, verified by at least one of the now-passing tests.

## Testing Expectations
Run `uv run pytest tests/agent/services/test_config_reload.py -q`; also run the full
`uv run pytest tests/ -q` to confirm no new failures are introduced elsewhere.

## Documentation Impact
N/A: internal exception-handling fix; no documented public behavior changes (the
documented contract — validator rejections raise `ConfigReloadValidationError` — is being
restored, not changed).

## Out of Scope
Any other failing test file identified in the same investigation
(`tests/agent/test_orchestrator.py`, `tests/eventbus/test_eventbus_auth.py`,
`tests/agent/services/test_mcp_tool_discovery.py`,
`tests/mcp_servers/git/test_git_security_compliance.py`) — each is tracked as its own
issue.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — the mismatch and its fix location are both directly confirmed by reading
`config_section_reload.py`'s source.

## AI Implementation Instruction
Change only `reload_validated_section()` in `config_section_reload.py` to wrap the
validator-loop's `ValueError` the same way the `dataclasses.replace` call already is. Do
not change `config_validators.py`'s validators or any caller. Keep the diff minimal.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-164222
- **Related target files**: scripts/agent/services/config_section_reload.py
