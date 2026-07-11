# Implementation: `scripts/agent/workflow/workflow_loader.py` — Narrow `_SUPPORTED_BACKOFF` to `{"fixed"}`

## Goal

Remove `"exponential"` from `_SUPPORTED_BACKOFF`, since it is accepted at validation time but has zero effect on runtime behavior (confirmed: `_run_execute_with_retry()` in `workflow_engine.py` reads `policy.backoff_sec` directly and never branches on `policy.backoff`). This closes the "config value silently behaves differently from its name" gap.

## Scope

**In scope:**
- `scripts/agent/workflow/workflow_loader.py`: narrow `_SUPPORTED_BACKOFF` from `{"fixed", "exponential"}` to `{"fixed"}`.

**Out of scope:**
- The validation error message string itself (line 88-90) — no code change needed; it already interpolates `sorted(_SUPPORTED_BACKOFF)`, so it automatically reflects the narrowed set.
- `workflow_engine.py` — no behavior change; it never read `.backoff` for branching, so narrowing the accepted set does not change engine behavior for any currently-valid config.
- `config/workflows/default.json` — already uses `"fixed"` exclusively (separate implementation doc covers its `retry`-stage removal).

## Assumptions

- Confirmed via full-file read of `workflow_engine.py`: `_run_execute_with_retry()` (line 194) uses `wait = policy.backoff_sec` directly; no other reference to `.backoff` exists anywhere in that file.
- Confirmed via `grep -r "exponential" config/ scripts/`: no code anywhere constructs a workflow JSON with `"backoff": "exponential"`, and `config/workflows/default.json` (the only workflow file in the repo) already uses `"fixed"`.
- Narrowing the set is backward compatible for the only real file (`default.json`) and fails loudly (via `WorkflowLoadError`) rather than silently for any future file that sets `"exponential"` — a safe, discoverable failure mode per the plan's risk assessment.

## Implementation

### Target file

`scripts/agent/workflow/workflow_loader.py`

### Procedure

1. Locate the `_SUPPORTED_BACKOFF` module-level constant (currently `{"fixed", "exponential"}`, ~line 48).
2. Change it to `_SUPPORTED_BACKOFF = {"fixed"}`.
3. Do not touch the validation branch/error-message code at lines 88-90 — it already reads from `_SUPPORTED_BACKOFF` dynamically via `sorted(_SUPPORTED_BACKOFF)`.
4. Do not touch `_REQUIRED_STAGES` or any other constant in this file.

### Method

Single-line constant edit:

```python
_SUPPORTED_BACKOFF = {"fixed"}
```

No control-flow change; the existing `if policy_backoff not in _SUPPORTED_BACKOFF: raise WorkflowLoadError(...)` branch (or equivalent) continues to work unmodified, now rejecting `"exponential"` as an unsupported value.

### Details

- Verify the error message produced for a rejected `"exponential"` value now reads `"...must be one of: fixed"` (single-element sorted list), not a stale hardcoded string.
- No import changes required.
- Keep line length under 120 chars per `rules/coding.md`.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `workflow_loader.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/workflow/workflow_loader.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/workflow/` | No new errors |
| Tests | `uv run pytest tests/test_workflow_loader.py -v` | All pass, including updated `test_invalid_backoff_value_rejected` asserting `"exponential"` is now rejected with an error message listing only `"fixed"` |
| Regression | `uv run pytest tests/ -k "workflow" -q` | No new failures |
| Manual grep | `grep -rn "exponential" config/ scripts/ docs/` | No matches remain outside historical/archival records |
