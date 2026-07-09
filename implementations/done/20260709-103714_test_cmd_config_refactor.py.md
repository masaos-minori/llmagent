# Implementation: H-9 — test_cmd_config_refactor.py deferred example relabel

Source plan: `plans/20260709-095933_plan.md` (H-9, Implementation step 2).

## Goal

Replace the MCP-flavored example string in the generic `[DEFER]` rendering
test so it no longer implies MCP auth_token changes can still be deferred
(they cannot, after H-4).

## Scope

**Target**: `tests/test_cmd_config_refactor.py`, lines 151-181
(`TestCmdReloadDeferred::test_deferred_items_rendered`).

## Assumptions

1. This test patches `ConfigReloadService` entirely (constructing
   `ConfigReloadOutcome(deferred=["mcp/svc.auth_token"])` by hand) — it never
   calls the real classification function, so this is a pure relabel with no
   behavioral change to what's being tested (generic `[DEFER]` rendering in
   `cmd_config.py`).
2. `grep -rn "mcp/svc.auth_token"` outside this file and the `plans/*.md`
   cross-references matches nothing else that needs updating (verified
   while planning H-9).

## Implementation

### Target file

`tests/test_cmd_config_refactor.py`

### Procedure

#### Step 1: Replace the example string

Line 161:
```python
outcome = ConfigReloadOutcome(deferred=["mcp/svc.auth_token"])
```
→
```python
outcome = ConfigReloadOutcome(deferred=["example_field"])
```

Lines 179-180:
```python
assert "[DEFER]" in out
assert "mcp/svc.auth_token" in out
assert "Deferred (next connection)" in out
```
→
```python
assert "[DEFER]" in out
assert "example_field" in out
assert "Deferred (next connection)" in out
```

### Method

- Pure string substitution at 3 lines; no structural change to the test.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Old example gone | `grep -n "mcp/svc.auth_token" tests/test_cmd_config_refactor.py` | no matches |
| Test run | `uv run pytest tests/test_cmd_config_refactor.py -k deferred -v` | passes |
