# Implementation Procedure: tests/agent/test_config_builders.py

## Goal

Update the pinned expected default in `_TOOL_DEFAULTS` from `["file_content"]` to
`["content", "old_text", "new_text"]` so the builder-path default test asserts the fixed
value.

## Scope

In scope:
- One expected-value change in `tests/agent/test_config_builders.py`.

Out of scope:
- The explicit-override case at `:192` (`["custom_field"]`) — verified untouched by the
  plan (REQ-004).
- Code defaults (procedures 01-02), config (procedure 03), behavior tests (procedures
  05-06), docs (procedure 07).

## Assumptions

- Assumption: the only pin of the default in this file is the `_TOOL_DEFAULTS` entry at
  `:155` (`"masked_fields": ["file_content"],`), consumed by
  `TestBuildToolConfig.test_empty_dict_returns_defaults` via `getattr` comparison.
  Verified by grep: the only other `masked_fields` occurrence is the override fixture at
  `:192`.
- Assumption: no other test file pins the default list value; the remaining
  `masked_fields` fixtures across `tests/agent/` pass `[]` or explicit lists and are
  unaffected. Verified by repo-wide grep (2026-10-25): all other fixtures are `[]`,
  explicit names, or `["custom_field"]`.

## Design decisions

- Decision: edit the pinned value in place rather than deriving the expectation from the
  dataclass default — the test's purpose is pinning the frozen literal against accidental
  drift.
- Decision: this pin update lands in the same phase as the code default changes (plan Phase
  2), not in the tests-first phase. Running it before procedures 01-02 turns the pin red by
  design; that is acceptable TDD sequencing but the plan's gate command runs after
  procedures 01-03.

## Alternatives considered

- Alternative: parameterize the pin over both config paths (dataclass vs builder).
  Rejected: `test_empty_dict_returns_defaults` already covers the builder path; adding a
  second pin duplicates coverage the plan did not ask for.
- Alternative: delete the pin and rely on the new behavior tests (procedures 05-06).
  Rejected: pins catch silent default drift; REQ-004 explicitly keeps it.

## Implementation

### Target file

`tests/agent/test_config_builders.py`

### Procedure

1. Open the `_TOOL_DEFAULTS` dict (starts around `:148`).
2. Replace the `masked_fields` entry.

### Method

Change from (verified at `:155`):

```python
    "masked_fields": ["file_content"],
```

to:

```python
    "masked_fields": ["content", "old_text", "new_text"],
```

No other lines in the file change; the override fixture at `:192` stays as is.

### Details

- `test_empty_dict_returns_defaults` iterates `_TOOL_DEFAULTS` and asserts
  `getattr(cfg, key) == value`, so the pin exercises the `_build_tool_config` fallback path
  (procedure 02).
- The dataclass direct-construction default is covered behaviorally by procedures 05-06.

## Compatibility considerations

- Until procedures 01-02 land, this pin makes `test_empty_dict_returns_defaults` fail — the
  expected red state in tests-first ordering; the plan Phase 2 gate command passes only
  after all of 01-04 are in.
- Fixture-based tests that pass explicit `masked_fields` (e.g. `:192`) are unaffected
  (AC-6).

## Security considerations

- No direct security change: this is the regression pin that prevents the fixed default
  from silently reverting to the inert one (REQ-004 supports REQ-001).
- No test secrets or masking semantics change in this file.

## Rollback considerations

- Rollback: revert the one pinned value together with the revert of procedures 01-03; the
  suite returns to green against the old defaults.
- No test data or fixture migration needed.

## Validation plan

1. `uv run pytest tests/agent/test_config_builders.py -q` green after procedures 01-02 land
   (plan Phase 2 gate).
2. Confirm the pin reads `["content", "old_text", "new_text"]` and `:192` still reads
   `["custom_field"]`.
3. Full gate: `uv run ruff check . && uv run mypy scripts/ tests/ --strict` (type checker
   treats the literal list as `list[str]`).

## Completion criteria

- `_TOOL_DEFAULTS["masked_fields"]` equals the frozen triple.
- `test_empty_dict_returns_defaults` passes against the new builder fallback.
- The explicit-override test still passes unchanged.

## Out of Scope

- Code defaults (procedures 01-02), `config/agent.toml` (procedure 03).
- New behavior tests (procedures 05-06) and docs (procedure 07).
- The `:192` override fixture.

## Execution Status

- [ ] Completed
- [ ] Partial — Blocked by: (state explicitly, including partial deploy state)

## Traceability

- Plan: `plans/20261024-221904_default-masked-fields-names-match-no-real-tool-argument.md`
- Plan section: Implementation Target Files — row 4 of 7
  (`tests/agent/test_config_builders.py`); Implementation steps Phase 2
- Requirements: REQ-004
- Acceptance criteria: AC-4, AC-6
- Procedure file:
  `implementations/20261025-004008_04_tests_agent_test_config_builders.py.md`
- Validation commands: `uv run pytest tests/agent/test_config_builders.py -q`
