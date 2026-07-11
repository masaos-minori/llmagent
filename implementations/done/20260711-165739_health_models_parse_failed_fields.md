## Goal

Add explicit "JSON parse failed" signal to `McpHealthProbeResult` so downstream code
(watchdog logging, classification) can distinguish a malformed `/health` response body
from a genuinely empty/healthy one, without changing any existing field's meaning or
any of the 5 existing construction call sites.

## Scope

**In-Scope:**
- `scripts/agent/shared/health_models.py`: add two new fields to the
  `McpHealthProbeResult` frozen dataclass: `parse_failed: bool = False` and
  `parse_error: str | None = None`.
- Update the dataclass's docstring `Fields:` block to document the two new fields.

**Out-of-Scope:**
- Any change to `reachable`, `status_code`, `restart_recommended`,
  `operator_action_required`, or `body` field semantics.
- Any change to `_probe_mcp_health_detail()` or `_watchdog_check_http()` in
  `scripts/agent/repl_health.py` — covered by a separate implementation doc.
- Any change to `HealthCheckResult`, `ServiceWarning`, or `StartupCheckStatus` in the
  same file.

## Assumptions

- `McpHealthProbeResult` is `@dataclass(frozen=True)` today (confirmed by direct read
  of `scripts/agent/shared/health_models.py` lines 36-52).
- All 5 existing construction sites (`repl_health.py:51,64` in production code;
  `tests/test_watchdog.py:90,116,145` in tests) use keyword arguments exclusively, so
  adding two new fields *with defaults* is purely additive and requires no changes at
  those call sites.
- New fields must default to `False` / `None` respectively so that every pre-existing
  construction site (which does not pass them) continues to behave exactly as before.

## Implementation

### Target file

`scripts/agent/shared/health_models.py`

### Procedure

1. Open `scripts/agent/shared/health_models.py`.
2. Locate the `McpHealthProbeResult` dataclass definition (currently lines 36-52).
3. Add two new fields after the existing `body: dict[str, object]` field:
   - `parse_failed: bool = False`
   - `parse_error: str | None = None`
4. Update the class docstring's `Fields:` block to add one line each for
   `parse_failed` and `parse_error`, describing their meaning (see Details).
5. Do not reorder or modify any existing field.

### Method

Simple additive dataclass field addition. No new imports required — `str | None`
syntax is already valid in this module (`from __future__ import annotations` is
present at the top of the file).

### Details

- `parse_failed: bool = False` — `True` when `_probe_mcp_health_detail()` received an
  HTTP response but the response body could not be parsed as JSON (i.e. the
  `resp.json()` call raised an exception). Defaults to `False` for the unreachable
  case and for any successful-parse case.
- `parse_error: str | None = None` — short diagnostic string describing the parse
  failure (exception message plus a truncated raw-body excerpt), populated only when
  `parse_failed=True`. `None` in all other cases.
- Because both fields have defaults and the dataclass remains `frozen=True`, no other
  file needs to change as a direct result of this edit alone (field addition is
  backward compatible with keyword-argument construction).
- Field order in the dataclass body should place the two new fields last, after
  `body`, to minimize diff noise and make the additive nature of the change visible in
  review.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/shared/health_models.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/shared/health_models.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest tests/test_watchdog.py -v` | All pass — confirms existing keyword-argument construction sites still work unchanged with the new optional fields |
