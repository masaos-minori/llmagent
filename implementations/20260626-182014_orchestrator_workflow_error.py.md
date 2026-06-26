# Implementation: orchestrator.py — improve workflow_mode=required error messages

Source plan: `plans/20260626-180406_plan.md` — Phase 2

---

## Goal

Make `Orchestrator.__init__()` emit an actionable `RuntimeError` when `workflow_mode="required"` and the definition file is missing, including: the expected file path, the active mode, and a remediation hint. Also add a pre-load INFO log line as preflight visibility.

---

## Scope

**In-Scope**
- Add INFO log line before `WorkflowLoader().load()`: `"workflow: mode=%s attempting load from %s"`
- Update the RuntimeError message in the `except` block to include `path`, `mode`, and remediation
- `WorkflowLoader` already exposes the path in its error message; extract it or construct it independently

**Out-of-Scope**
- Changing `workflow_mode="required"` production default
- Adding soft fallback for `required` mode
- Changes to `WorkflowLoader` itself (error message already contains path)

---

## Assumptions

1. `WorkflowLoader.load()` raises `WorkflowLoadError(f"workflow file not found: {path}")` — the path is in the exception string (confirmed: workflow_loader.py:80).
2. The expected path can also be computed independently: `_WORKFLOWS_DIR / "default.json"` — or passed via `WorkflowLoader(workflows_dir)`.
3. The pre-load INFO log should show the directory path (`_WORKFLOWS_DIR`) even before the load attempt fails.
4. `orchestrator.py` imports `WorkflowLoader` and `WorkflowLoadError` from `agent.workflow.workflow_loader`.

---

## Implementation

### Target file
`scripts/agent/orchestrator.py`

### Procedure
Locate the `__init__` block at lines ~128–137 and:
1. Add import for `_WORKFLOWS_DIR` or compute expected path locally.
2. Add INFO log before load attempt.
3. Update RuntimeError message in except block.

### Method

**Current code (orchestrator.py ~128–137):**
```python
self._workflow_def: WorkflowDef | None = None
if self._workflow_mode != "disabled":
    try:
        self._workflow_def = WorkflowLoader().load()
    except (WorkflowLoadError, Exception) as exc:
        if self._workflow_mode == "required":
            raise RuntimeError(
                f"[workflow] mode=required but WorkflowLoader failed: {exc}. "
                "Check workflow definition file or set workflow_mode=auto in config."
            ) from exc
        logger.warning("WorkflowLoader failed — workflow tracking disabled")
```

**Updated code:**
```python
self._workflow_def: WorkflowDef | None = None
if self._workflow_mode != "disabled":
    loader = WorkflowLoader()
    expected_path = loader._dir / "default.json"
    logger.info(
        "workflow: mode=%s attempting load from %s",
        self._workflow_mode,
        expected_path,
    )
    try:
        self._workflow_def = loader.load()
    except (WorkflowLoadError, Exception) as exc:
        if self._workflow_mode == "required":
            raise RuntimeError(
                f"[workflow] Startup failed: mode=required but workflow definition not found.\n"
                f"  Expected file: {expected_path}\n"
                f"  Error: {exc}\n"
                f"  Fix: deploy the workflow definition file, or set workflow_mode=auto in config."
            ) from exc
        logger.warning(
            "WorkflowLoader failed (mode=%s) — workflow tracking disabled: %s",
            self._workflow_mode,
            exc,
        )
```

Note: `loader._dir` accesses `WorkflowLoader._dir` (private, but same module — acceptable for constructing the path display). Alternative: import `_WORKFLOWS_DIR` directly from `workflow_loader`.

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/orchestrator.py` | 0 errors |
| Type | `uv run mypy scripts/agent/orchestrator.py` | no new errors |
| Tests | `uv run pytest tests/test_orchestrator*.py -v` | all pass |
| Error message test | Add test: mode=required + mock WorkflowLoadError → RuntimeError message contains "Expected file:" | pass |
| Full suite | `uv run pytest -v` | all pass |
