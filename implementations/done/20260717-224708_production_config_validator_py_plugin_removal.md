# Implementation: scripts/shared/production_config_validator.py (remove plugin_strict required-key entry)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 3, item 4)

Gap-filling note: matches the granularity of the existing `config_validators.py`
doc for this same plan step. Independent of other step-3 siblings (no import
relationship); can land in any order relative to them.

## Goal

`_REQUIRED_STRICT_KEYS` no longer lists `"plugin_strict"` as a key that must
be `true` in production.

## Scope

**In scope**: `scripts/shared/production_config_validator.py` — delete the
`"plugin_strict",` tuple entry (line 19) from `_REQUIRED_STRICT_KEYS`.

**Out of scope**: `"tool_definitions_strict"`/`"routing_drift_strict"` (the
other two entries in the same tuple) — unaffected; `_REQUIRED_NOT_FALSE_KEYS`
(a separate, currently-empty tuple) — unaffected; any validator function in
this file — this is a pure data-tuple edit, no function body changes.

## Assumptions

1. Confirmed by direct read (2026-07-17):
   ```python
   _REQUIRED_STRICT_KEYS = (
       "plugin_strict",
       "tool_definitions_strict",
       "routing_drift_strict",
   )
   ```
   at lines 18-22, a module-level tuple constant with exactly 3 entries.
2. This is a pure data change — removing an entry from a validation-required-keys tuple used by whatever function(s) iterate `_REQUIRED_STRICT_KEYS` to check production config (confirm the consuming function elsewhere in this file, e.g. a `validate_production_config()`-style function, still iterates the tuple generically without a plugin-specific branch — if it does have plugin-specific logic beyond membership in this tuple, that would be a discrepancy to report rather than silently work around).

## Implementation

### Target file

`scripts/shared/production_config_validator.py`

### Procedure

1. Delete `"plugin_strict",` from `_REQUIRED_STRICT_KEYS`, leaving:
   ```python
   _REQUIRED_STRICT_KEYS = (
       "tool_definitions_strict",
       "routing_drift_strict",
   )
   ```

### Method

Single-entry tuple deletion — no other code change, assuming (per Assumption 2) the consuming validator logic treats all `_REQUIRED_STRICT_KEYS` entries generically. Verify this assumption by reading the rest of the file before editing; if a plugin-specific branch exists elsewhere referencing `"plugin_strict"` by name (not just via the tuple), remove that too and note it in your implementation report as a discrepancy from this doc's stated scope.

### Details

- Do not touch `_REQUIRED_NOT_FALSE_KEYS` or any validator function signature.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No plugin references remain in this file | `grep -n "plugin" scripts/shared/production_config_validator.py` | 0 matches |
| Syntax/lint | `uv run ruff check scripts/shared/production_config_validator.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/production_config_validator.py` | no new errors |
| Targeted tests (expect failures until test-removal doc also lands) | `uv run pytest tests/test_production_config_validator.py -v` | pass once plugin-specific test cases are also removed |
