## Goal

Extend `check_workflow_definition` (`scripts/agent/services/workflow_schema.py`) so the
startup preflight rejects a malformed workflow definition file (invalid JSON, wrong
shape, missing required key or required stage) with a `RuntimeError` naming the file and
cause, instead of passing it through to fail later in the Orchestrator constructor.
Reuse the existing loader's validation rather than duplicating its rules.

## Scope

- In-Scope: after the existing existence check, load the definition via
  `WorkflowLoader(workflows_dir=target_dir).load("default")` and re-raise
  `WorkflowLoadError` plus scalar-coercion errors (`ValueError`/`TypeError`/`AttributeError`)
  as a `RuntimeError` naming the file and cause (REQ-001, REQ-002, REQ-003, REQ-004).
- Out-of-Scope: changing the loader's validation rules (`_validate`); changing the
  Orchestrator constructor; the schema preflight (`check_workflow_schema`); the
  signature/return type of `check_workflow_definition`; any other startup validation.

## Assumptions

- `WorkflowLoader.load("default")` resolves to `<target_dir>/default.json`, matching the
  preflight's existence check, so injecting `target_dir` keeps both consistent.
- Calling `load()` constructs a full `WorkflowDef` in memory (no write/DB/network side
  effects), acceptable for a startup preflight.
- No caller depends on `check_workflow_definition` succeeding for an invalid definition.

## Design decisions

- Reuse the loader's validation instead of duplicating `_validate` rules (issue
  constraint; DRY).
- Broaden the `except` beyond `WorkflowLoadError` to
  `(WorkflowLoadError, ValueError, TypeError, AttributeError)` so every malformed input
  yields the preflight `RuntimeError` (owner-resolved; see plan "Resolved decision").
  Without this, malformed scalar fields leak a raw `ValueError`/`AttributeError` from
  the preflight.
- Preserve the lazy-import pattern (avoid circular import at module load) by importing
  `WorkflowLoader` and `WorkflowLoadError` from `agent.workflow.workflow_loader` inside
  the function alongside the existing `WORKFLOWS_DIR` import.
- Keep the missing-file branch and its message byte-for-byte unchanged (REQ-004).
- `ValueError`/`TypeError`/`AttributeError` are builtins — no import needed.

## Alternatives considered

- Duplicate `_validate` logic in the preflight: rejected — violates the reuse constraint
  and drifts from the loader.
- Catch only `WorkflowLoadError`: rejected — malformed scalar fields raise
  `ValueError`/`AttributeError` from the loader's `int()`/`.get` calls, which would
  escape the preflight.
- Raise a custom exception type: rejected — callers (`startup_component_init._check_workflow_definition`,
  `orchestrator.py`) already handle `RuntimeError`/`WorkflowLoadError`; changing the type
  would require caller changes (out of scope).

## Implementation

### Target file

`scripts/agent/services/workflow_schema.py`

### Procedure

1. Extend `check_workflow_definition` in `scripts/agent/services/workflow_schema.py` to
   load via the loader and re-raise validation/scalar-coercion errors as `RuntimeError`
   naming file+cause; keep the missing-file message unchanged (REQ-001, REQ-002,
   REQ-003, REQ-004).
2. Add content-validation tests to `tests/agent/test_repl_health.py::TestCheckWorkflowDefinition`
   (malformed JSON, wrong shape, missing required key/stage) and update
   `test_present_file_passes` to a valid definition (REQ-001, REQ-002, REQ-003).
3. Run the full toolchain validation and confirm no production caller breaks (REQ-004).

### Method

Modify `check_workflow_definition` in place. After the existing
`if not workflow_file.exists(): raise ...` block, add a `try` that calls the loader and
an `except` that re-raises as `RuntimeError`.

```python
def check_workflow_definition(workflows_dir: Path | None = None) -> None:
    """Raise RuntimeError if the workflow definition file is missing or invalid."""
    from agent.workflow.workflow_loader import (  # lazy to avoid circular import
        WORKFLOWS_DIR,
        WorkflowLoader,
        WorkflowLoadError,
    )

    target_dir = workflows_dir if workflows_dir is not None else WORKFLOWS_DIR
    workflow_file = target_dir / "default.json"
    if not workflow_file.exists():
        raise RuntimeError(
            f"Workflow definition file not found: {workflow_file}. Deploy config/workflows/default.json to fix this."
        )
    try:
        WorkflowLoader(workflows_dir=target_dir).load("default")
    except (WorkflowLoadError, ValueError, TypeError, AttributeError) as exc:
        raise RuntimeError(
            f"Workflow definition invalid: {workflow_file}: {exc}"
        ) from exc
```

Key points:

- Add `WorkflowLoader` and `WorkflowLoadError` to the existing lazy import block — do
  NOT move it to module level (the circular-import guard requires the local import).
- The missing-file branch and its message are unchanged (REQ-004).
- `load("default")` reads `<target_dir>/default.json`, consistent with the existence
  check above.
- The re-raised message prepends the filename (which the loader's own messages omit)
  and chains via `from exc` for a clear traceback.

### Details

- Current code (`workflow_schema.py:22-33`) checks `.exists()` only; invalid JSON, wrong
  shape, and missing required stages pass it unchanged.
- Content validation lives in the loader: `_validate()` (`workflow_loader.py:60-97`)
  raises `WorkflowLoadError` for missing required keys, empty/duplicate stages, missing
  required stages (`plan`/`execute`/`verify`), and bad `retry_policy`; `load()`
  (`workflow_loader.py:107-119`) raises `WorkflowLoadError` on parse error and
  non-object JSON.
- Malformed scalar fields raise other exceptions the narrow `except WorkflowLoadError`
  would miss: `ValueError` from `int(policy["max_attempts"])` / `int(policy["backoff_sec"])`
  (`workflow_loader.py:90,123`) when the field holds a non-numeric string, and
  `AttributeError` from `s.get("id")` (`workflow_loader.py:68`) when a stage entry is
  not a dict. These are why the `except` is broadened.
- Call site `startup_component_init.py:_check_workflow_definition` (lines 88-94) catches
  `RuntimeError` and logs it; last line of defense `orchestrator.py:129` catches
  `(WorkflowLoadError, FileNotFoundError)` and re-raises `RuntimeError` at line 130.
  Failure remains fatal; the change only moves it earlier to preflight.
- The loader is side-effect free (pure read + in-memory construct), so calling it from
  the preflight is safe.

## Compatibility considerations

- Signature (`workflows_dir: Path | None = None`) and return type (`None`) are
  unchanged; the function still raises `RuntimeError`.
- `startup_component_init.py` expects `RuntimeError` (catches it at line 92);
  `orchestrator.py` catches `WorkflowLoadError`/`FileNotFoundError` independently. No
  caller change required.
- The missing-file `RuntimeError` message is unchanged, so
  `test_missing_file_raises` / `test_error_message_includes_remediation` keep passing
  (REQ-004).
- The malformed-definition `RuntimeError` message differs from the old (non-existent)
  one and from the Orchestrator's message; this is owner-open (UNK-01) but non-blocking
  — the new message names the file and cause.

## Security considerations

- No new attack surface: the function reads a local config file it already read before
  this change.
- The loader was already invoked by the Orchestrator at startup, so its behavior is
  unchanged; the preflight now invokes the same code path earlier.

## Rollback considerations

- Revert the added `try/except` block and the two extra imports; the original
  single-branch function is restored. No state or migration is touched.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/workflow_schema.py` | Unit: exercise `check_workflow_definition` with malformed/valid/missing definitions via tmp dirs. | `uv run pytest tests/agent/test_repl_health.py::TestCheckWorkflowDefinition` | All content-validation tests pass; existing missing-file tests unchanged. |
| `scripts/agent/workflow/workflow_loader.py` | Read-only reuse; no change. | — | Unchanged. |
| Whole suite | Regression. | `uv run pytest` | No regressions; production callers unaffected. |

## Completion criteria

- `check_workflow_definition(workflows_dir=tmp_path)` raises `RuntimeError` naming the
  file for invalid JSON (REQ-001) and for wrong-shape / missing-required-key /
  missing-required-stage definitions (REQ-002).
- A complete valid definition passes without raising (REQ-003).
- The missing-file `RuntimeError` message is byte-for-byte unchanged;
  `test_missing_file_raises` / `test_error_message_includes_remediation` pass (REQ-004).
- Full toolchain (`rules/toolchain.md`) passes with no new failures.

## Out of scope

- Changing the loader's `_validate` rules (`workflow_loader.py`).
- Changing the Orchestrator constructor or `check_workflow_schema`.
- Any public interface change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: `issues/20261008-150558_wfpreflight01_validate-the-workflow-definition-content-in-the-startup-preflight.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261009-173642_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-131312
- **Related target files**: `scripts/agent/services/workflow_schema.py`
