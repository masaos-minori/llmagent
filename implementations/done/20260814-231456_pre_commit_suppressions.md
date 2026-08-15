## Goal

Resolve `check-suppression-justify` pre-commit hook failure for 6 unjustified `# type: ignore` suppressions in test files by adding em-dash justified comments following the convention established in `rules/coding.md`.

## Scope

**In-Scope:**
- Add em-dash justified comments to `# type: ignore` suppressions in 6 test file locations
- Remove unnecessary `# type: ignore` suppressions where no longer needed
- Verify pre-commit hook passes after changes

**Out-of-Scope:**
- Modifying pre-commit configuration to bypass checks
- Changes to production logic beyond adding missing imports
- `git-exc-import-guard` — already resolved (both `scripts/mcp_servers/git/git_service.py` and `scripts/shared/git_helper.py` have `import git.exc`)
- Full repo-wide scan of all `# type: ignore` suppressions — only the 6 known locations

## Assumptions

- The `# type: ignore` suppressions exist because mypy cannot infer types from `git.exc` exceptions or similar type inference gaps
- Em-dash format follows the convention established in `rules/coding.md`: `# type: ignore[error-code]  # <justification>`
- The 6 known locations are the only ones causing pre-commit hook failures

## Design decisions

- Direct addition of em-dash justifications rather than removing suppressions — the suppressions are necessary for valid type checking
- No migration path needed since the suppressions are legitimate

## Alternatives considered

- Remove the `# type: ignore` suppressions entirely — rejected because they suppress real mypy errors
- Fix the underlying type inference issues — rejected because it would require broader changes to the codebase
- Update pre-commit configuration to allow unjustified suppressions — rejected because it defeats the purpose of the check

## Implementation

### Target files

`tests/shared/test_tool_spec.py`, `tests/shared/test_tool_transport_invoker_merge.py`

### Procedure

1. **Phase 1: Resolve known locations**
   - [ ] Add em-dash justification to `tests/shared/test_route_resolver.py:267`
   - [ ] Add em-dash justification to `tests/shared/test_tool_spec.py:49`
   - [ ] Add em-dash justification to `tests/shared/test_tool_transport_invoker_merge.py:46`
   - [ ] Add em-dash justification to `tests/shared/test_tool_transport_invoker_merge.py:47`
   - [ ] Add em-dash justification to `tests/shared/test_tool_transport_invoker_merge.py:63`
   - [ ] Add em-dash justification to `tests/shared/test_tool_transport_invoker_merge.py:72`

2. **Phase 2: Verification**
   - [ ] Run `uv run pre-commit run --all-files` to verify all hooks pass
   - [ ] Confirm no unjustified suppressions remain in tested files: `rg '# type: ignore' tests/shared/test_tool_spec.py tests/shared/test_tool_transport_invoker_merge.py tests/shared/test_route_resolver.py | grep -v '\[.*—'`

### Method

Edit — add em-dash justifications.

### Details

#### `tests/shared/test_route_resolver.py:267`

Current line:
```python
{"name": None, "server_key": "file_read"},  # type: ignore[typeddict-item]  # deliberately malformed: exercises the defensive skip path
```

The suppression exists because `None` is passed where a `str` is expected in a TypedDict key. The mypy error is `typeddict-item` because `None` does not match the `str` type for the `name` field. The current comment explains intent but lacks the required em-dash separator.

Proposed change:
```python
{"name": None, "server_key": "file_read"},  # type: ignore[typeddict-item]  # deliberately malformed input — exercises the defensive skip path
```

#### `tests/shared/test_tool_transport_invoker_merge.py:46`

Current line:
```python
invoker._transports["srv"] = mock_transport  # type: ignore[assignment]
```

The suppression exists because `mock_transport` is an `AsyncMock` that duck-types `HttpTransport`. The mypy error is `assignment` because the type checker infers `_transports` values as `HttpTransport` but `AsyncMock` is not assignable.

Proposed change:
```python
invoker._transports["srv"] = mock_transport  # type: ignore[assignment]  # AsyncMock duck-types HttpTransport
```

#### `tests/shared/test_tool_transport_invoker_merge.py:47`

Current line:
```python
invoker._record_success = MagicMock()  # type: ignore[method-assign]
```

The suppression exists because `MagicMock` is used as a spy/mock for `_record_success`. The mypy error is `method-assign` because `MagicMock` is not assignable to a method attribute.

Proposed change:
```python
invoker._record_success = MagicMock()  # type: ignore[method-assign]  # spy mock for _record_success
```

#### `tests/shared/test_tool_transport_invoker_merge.py:63`

Current line:
```python
invoker._transports["srv"] = mock_transport  # type: ignore[assignment]
```

Same pattern as line 46 — `AsyncMock` duck-types `HttpTransport`.

Proposed change:
```python
invoker._transports["srv"] = mock_transport  # type: ignore[assignment]  # AsyncMock duck-types HttpTransport
```

#### `tests/shared/test_tool_transport_invoker_merge.py:72`

Current line:
```python
invoker._record_transport_error = MagicMock(return_value=sentinel)  # type: ignore[method-assign]
```

Same pattern as line 47 — `MagicMock` used as a spy/mock for `_record_transport_error`.

Proposed change:
```python
invoker._record_transport_error = MagicMock(return_value=sentinel)  # type: ignore[method-assign]  # spy mock for _record_transport_error
```

## Compatibility considerations

- None — these are test-only changes with no impact on production behavior.
- The em-dash justification format is consistent with the project convention.

## Security considerations

N/A — adding comments to existing suppressions does not introduce security risks.

## Rollback considerations

- Simple git revert of the change restores the original suppressions without justifications.
- No database migrations or config changes involved.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_route_resolver.py` | Unit — confirm em-dash added | `rg '# type: ignore' tests/shared/test_route_resolver.py | grep -v '\[.*—'` | No output (no unjustified suppressions) |
| `tests/shared/test_tool_spec.py` | Unit — confirm em-dash added | `rg '# type: ignore' tests/shared/test_tool_spec.py | grep -v '\[.*—'` | No output (no unjustified suppressions) |
| `tests/shared/test_tool_transport_invoker_merge.py` | Unit — confirm em-dash added | `rg '# type: ignore' tests/shared/test_tool_transport_invoker_merge.py | grep -v '\[.*—'` | No output (no unjustified suppressions) |
| Project-wide | Integration — pre-commit hook | `uv run pre-commit run --all-files` | Hook passes |
| Project-wide | Integration — no regressions | `uv run pytest` | All tests pass |

## Out of scope

- Removal of `LlmTransportErrorHandler.resolve_retryable()` — handled in separate implementation procedure document.
- Removal of `TestResolveRetryable` in `tests/shared/test_llm_transport_errors.py` — handled in separate implementation procedure document.
- Full repo-wide scan of all `# type: ignore` suppressions — only the 6 known locations per plan.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260814-222518_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-231456
- Related target files: test_route_resolver.py, test_tool_spec.py, test_tool_transport_invoker_merge.py
