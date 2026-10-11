## Goal

Add content-validation tests for `check_workflow_definition` to
`tests/agent/test_repl_health.py::TestCheckWorkflowDefinition`, and update
`test_present_file_passes` so it writes a complete valid definition (the current `"{}"`
fixture is now invalid under content validation). This exercises the real function's
content-validation path (REQ-001, REQ-002, REQ-003).

## Scope

- In-Scope: add `test_malformed_json_raises`, `test_missing_required_key_raises`,
  `test_missing_required_stage_raises` to `TestCheckWorkflowDefinition`; update
  `test_present_file_passes` to write a complete valid definition instead of `"{}"`
  (REQ-001, REQ-002, REQ-003).
- Out-of-Scope: changing `check_workflow_definition` implementation
  (`scripts/agent/services/workflow_schema.py` — covered by the sibling implementation
  procedure); the wrapper `_check_workflow_definition` in
  `tests/agent/test_startup_workflow_preflight.py`; any other test class.

## Assumptions

- `check_workflow_definition(workflows_dir=tmp_path)` loads `<tmp_path>/default.json` via
  `WorkflowLoader(workflows_dir=tmp_path).load("default")`, so writing the fixture to
  `tmp_path / "default.json"` exercises the real path.
- A complete valid definition must contain `name`, `version`, three required stages
  (`plan`/`execute`/`verify`), a valid `retry_policy`, and `require_approval: true` to
  pass `_validate()`.

## Design decisions

- Put the content-validation tests in `TestCheckWorkflowDefinition` (real-function tests
  belong where the real function is exercised with real tmp files), not in a new file.
- Use real tmp files (`tmp_path / "default.json"`) rather than mocking the loader, so the
  tests exercise the actual loader validation the preflight relies on.
- Update `test_present_file_passes` in place (a necessary consequence of the change, not
  a regression) rather than deleting it.

## Alternatives considered

- New test file for workflow preflight: rejected — the real function already has a
  dedicated class (`TestCheckWorkflowDefinition`); adding another file fragments coverage.
- Mock `WorkflowLoader.load`: rejected — would not exercise the real validation the
  preflight depends on.

## Implementation

### Target file

`tests/agent/test_repl_health.py`

### Procedure

1. Add content-validation tests to `tests/agent/test_repl_health.py::TestCheckWorkflowDefinition`
   (malformed JSON, wrong shape, missing required key/stage) and update
   `test_present_file_passes` to a valid definition (REQ-001, REQ-002, REQ-003).
2. Run the full toolchain validation and confirm no production caller breaks (REQ-004).

### Method

Within `class TestCheckWorkflowDefinition:` (currently at line 887), add three new test
methods and edit `test_present_file_passes` (currently at line 897).

Update `test_present_file_passes` to write a complete valid definition:

```python
def test_present_file_passes(self, tmp_path) -> None:
    """A complete valid default.json raises no exception."""
    (tmp_path / "default.json").write_text(
        '{'
        '"name": "default", "version": "1.0.0", '
        '"stages": ['
        '{"id": "plan", "timeout_sec": 30, "retryable": false}, '
        '{"id": "execute", "timeout_sec": 120, "retryable": true}, '
        '{"id": "verify", "timeout_sec": 10, "retryable": false}'
        '], '
        '"retry_policy": {"max_attempts": 3, "backoff_sec": 1}, '
        '"require_approval": true'
        '}'
    )
    check_workflow_definition(workflows_dir=tmp_path)  # must not raise
```

Add the following new methods to the same class:

```python
def test_malformed_json_raises(self, tmp_path) -> None:
    """Invalid JSON raises RuntimeError naming the file (REQ-001)."""
    (tmp_path / "default.json").write_text("{ this is not valid json ")
    with pytest.raises(RuntimeError) as exc_info:
        check_workflow_definition(workflows_dir=tmp_path)
    assert "default.json" in str(exc_info.value)


def test_missing_required_key_raises(self, tmp_path) -> None:
    """Missing a required key raises RuntimeError (REQ-002)."""
    (tmp_path / "default.json").write_text(
        '{"name": "default", '
        '"stages": ['
        '{"id": "plan", "timeout_sec": 30, "retryable": false}, '
        '{"id": "execute", "timeout_sec": 120, "retryable": true}, '
        '{"id": "verify", "timeout_sec": 10, "retryable": false}'
        '], '
        '"retry_policy": {"max_attempts": 3, "backoff_sec": 1}, '
        '"require_approval": true}'
    )
    with pytest.raises(RuntimeError) as exc_info:
        check_workflow_definition(workflows_dir=tmp_path)
    assert "default.json" in str(exc_info.value)


def test_missing_required_stage_raises(self, tmp_path) -> None:
    """Missing a required stage raises RuntimeError (REQ-002)."""
    (tmp_path / "default.json").write_text(
        '{"name": "default", "version": "1.0.0", '
        '"stages": ['
        '{"id": "plan", "timeout_sec": 30, "retryable": false}, '
        '{"id": "execute", "timeout_sec": 120, "retryable": true}'
        '], '
        '"retry_policy": {"max_attempts": 3, "backoff_sec": 1}, '
        '"require_approval": true}'
    )
    with pytest.raises(RuntimeError) as exc_info:
        check_workflow_definition(workflows_dir=tmp_path)
    assert "default.json" in str(exc_info.value)
```

Notes:

- The missing-key fixture omits `version` (keeps name/stages/retry_policy/require_approval);
  `_validate()` raises `WorkflowLoadError("missing required key: 'version'")`, which the
  preflight re-raises as `RuntimeError`.
- The missing-stage fixture includes only `plan`/`execute` (drops `verify`);
  `_validate()` raises `WorkflowLoadError("required stages missing: verify")`.
- The malformed-JSON fixture contains invalid JSON so `orjson.loads` fails inside `load()`.
- All three assert `"default.json"` appears in the message; the preflight message format
  is `Workflow definition invalid: {workflow_file}: {exc}`, so the tmp path is present.

### Details

- Current `test_present_file_passes` (line 897-900) writes `"{}"`, which now fails
  `_validate()` (missing `name`/`version`/`stages`/`retry_policy`) and would fail unless
  updated — a necessary consequence of the change, not a regression.
- `pytest` is already imported in this module (used throughout `test_repl_health.py`);
  confirm the import is present before adding `pytest.raises` calls.
- Existing `test_missing_file_raises` (line 890) and
  `test_error_message_includes_remediation` (line 902) must remain green unchanged
  (REQ-004).
- `tests/agent/test_startup_workflow_preflight.py` patches
  `agent.startup_component_init.check_workflow_definition` and exercises only the
  wrapper `_check_workflow_definition`; it does not exercise the real function's content
  path, so content-validation tests belong here, not there.

## Compatibility considerations

- Only adds/modifies tests within `TestCheckWorkflowDefinition`; no production code changes.
- `test_present_file_passes` keeps its name and purpose (valid definition passes); only
  its fixture content changes.
- Existing assertions in `test_missing_file_raises` / `test_error_message_includes_remediation`
  are untouched.

## Security considerations

- N/A: test-only change; no runtime or attack-surface impact.

## Rollback considerations

- Remove the three new test methods and revert `test_present_file_passes` to write
  `"{}"`; the class returns to its prior state. No production or migration impact.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_repl_health.py` | Unit: run `TestCheckWorkflowDefinition` including the new content-validation tests. | `uv run pytest tests/agent/test_repl_health.py::TestCheckWorkflowDefinition -v` | All content-validation tests pass; existing missing-file tests unchanged. |
| Whole suite | Regression. | `uv run pytest` | No regressions; production callers unaffected. |

## Completion criteria

- `test_malformed_json_raises` passes and asserts `RuntimeError` with the file path in
  the message (REQ-001).
- `test_missing_required_key_raises` / `test_missing_required_stage_raises` pass and
  assert `RuntimeError` (REQ-002).
- Updated `test_present_file_passes` passes with a complete valid definition (REQ-003).
- `test_missing_file_raises` / `test_error_message_includes_remediation` still pass
  unchanged (REQ-004).

## Out of scope

- Changing `check_workflow_definition` implementation (`scripts/agent/services/workflow_schema.py`).
- Modifying `tests/agent/test_startup_workflow_preflight.py`.
- Any production-code or public-interface change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261011-155040 | Validated per toolchain; 16 pre-existing unrelated eventbus failures; new-test-name false positives; no docs/00_index.md mapping |
| 2 | Add or update tests per Validation plan | Completed | — | 20261011-155040 | Validated per toolchain; 16 pre-existing unrelated eventbus failures; new-test-name false positives; no docs/00_index.md mapping |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261011-155040 | Validated per toolchain; 16 pre-existing unrelated eventbus failures; new-test-name false positives; no docs/00_index.md mapping |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261011-155040 | Validated per toolchain; 16 pre-existing unrelated eventbus failures; new-test-name false positives; no docs/00_index.md mapping |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: `issues/20261008-150558_wfpreflight01_validate-the-workflow-definition-content-in-the-startup-preflight.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261009-173642_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-131312
- **Related target files**: `tests/agent/test_repl_health.py`