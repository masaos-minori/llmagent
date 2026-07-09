# Implementation: H-10 — test_config_builders.py github_server_url rejection test

Source plan: `plans/20260709-100244_plan.md` (H-10, Implementation step 8).

## Goal

Add a test proving `build_agent_config()` raises `ConfigLoadError` with an
actionable message when the config contains the removed `github_server_url`
key.

## Scope

**Target**: `tests/test_config_builders.py` — add to the class containing
`test_config_with_workflow_mode_key_raises` (lines 159-165), which already
covers the same `_FORBIDDEN_KEYS`-style rejection pattern.

Depends on `implementations/20260709-103717_config_builders.py.md`.

## Assumptions

1. `_MIN_CFG` (module-level fixture dict, used via `{**_MIN_CFG, ...}`
   spread) is a minimal valid config that `build_agent_config()` accepts —
   verified by its use in `test_config_with_workflow_mode_key_raises` and
   `test_config_with_workflow_require_approval_key_raises` (lines 159-165),
   which follow the identical pattern this new test needs.

## Implementation

### Target file

`tests/test_config_builders.py`

### Procedure

#### Step 1: Add the test

Insert after `test_config_with_workflow_require_approval_key_raises`
(line 165):

```python
    def test_config_with_github_server_url_key_raises(self) -> None:
        with pytest.raises(ConfigLoadError, match="github_server_url"):
            build_agent_config({**_MIN_CFG, "github_server_url": "http://old"})
```

Optionally also assert the actionable replacement message is present:

```python
    def test_config_with_github_server_url_key_message_mentions_replacement(self) -> None:
        with pytest.raises(ConfigLoadError, match="mcp_servers.github"):
            build_agent_config({**_MIN_CFG, "github_server_url": "http://old"})
```

### Method

- Two additive test methods, following the exact existing pattern in this
  class — no changes to `_MIN_CFG` or any other test.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests present | `grep -n "test_config_with_github_server_url" tests/test_config_builders.py` | 2 matches |
| Test run | `uv run pytest tests/test_config_builders.py -k github_server_url -v` | both pass |
| Full file regression | `uv run pytest tests/test_config_builders.py -v` | all pass |
