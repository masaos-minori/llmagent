# Implementation: `scripts/agent/workflow/models.py` — Correct `RetryPolicy.backoff` Field Comment

## Goal

Update the inline comment on `RetryPolicy.backoff` (currently `# "fixed" | "exponential"`) to `# "fixed"` only, matching the narrowed `_SUPPORTED_BACKOFF` set in `workflow_loader.py`. Also confirm `workflow_engine.py`'s module docstring requires no edit (already correct).

## Scope

**In scope:**
- `scripts/agent/workflow/models.py`: `_RetryPolicyJson`'s `backoff: str` field comment (~line 67).

**Out of scope:**
- `scripts/agent/workflow/workflow_engine.py`: module docstring (line 3: `"""Stage transition engine: plan -> execute -> [approval gate] -> verify -> (retry loop)."""`) — confirmed accurate as-is (describes retry as a parenthetical loop, not a named stage); **no edit required**. This document exists only to record that confirmation; no procedure/method section applies to that file.
- `RetryPolicy.backoff`'s type (`str`) — no change; still a plain string, not a `Literal["fixed"]`, since that type-narrowing was not requested by the plan and is a larger change than a comment fix.
- Any other field or class in `models.py`.

## Assumptions

- Confirmed by direct read: `models.py::_RetryPolicyJson.backoff` currently carries the comment `# "fixed" | "exponential"` documenting accepted values, consistent with the (now-narrowed) `_SUPPORTED_BACKOFF` in `workflow_loader.py`.
- Confirmed by direct read: `workflow_engine.py`'s module docstring already never names `retry` as a stage — it uses "(retry loop)" as a parenthetical describing the execute-stage retry mechanism, which remains accurate after the `default.json` `retry`-stage-entry removal (a stage entry was removed from config, not a runtime concept from the engine).
- This is a comment-only change with zero runtime/behavior impact — mypy/ruff will not flag anything since comments are not type- or lint-checked content (aside from line length).

## Implementation

### Target file

`scripts/agent/workflow/models.py`

### Procedure

1. Locate `_RetryPolicyJson.backoff: str` and its trailing/inline comment (~line 67).
2. Change the comment from `# "fixed" | "exponential"` to `# "fixed"`.
3. Leave the field's type annotation (`str`) and all other fields/classes untouched.
4. No corresponding edit needed in `workflow_engine.py` — verify its docstring text at implementation time and leave unmodified.

### Method

Single-line comment edit:

```python
backoff: str  # "fixed"
```

(replacing the previous `backoff: str  # "fixed" | "exponential"` or equivalent inline form — match existing exact formatting/spacing when applying).

### Details

- English-only comment per `rules/coding.md`.
- No suppression markers (`# noqa`, `# type: ignore`) involved.
- Keep line length under 120 chars.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `models.py` (and the confirmation-only check for `workflow_engine.py`):

| Check | Tool | Target |
|---|---|---|
| Type check | `uv run mypy scripts/agent/workflow/` | No new errors |
| Tests | `uv run pytest tests/test_workflow_models.py -v` | All pass |
| Regression | `uv run pytest tests/ -k "workflow" -q` | No new failures |
| Manual grep | `grep -rn "exponential" scripts/agent/workflow/` | No matches remain |
| Manual confirm | Read `workflow_engine.py` module docstring | Confirms no `retry`-as-stage wording present; no edit applied |
