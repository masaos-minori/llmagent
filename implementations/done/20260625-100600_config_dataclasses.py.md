# config_dataclasses.py — update workflow_mode docstring with production note

**Plan:** `plans/20260625-093349_plan.md` (req #61)
**Target:** `scripts/agent/config_dataclasses.py`

## What to change

Update the `AgentConfig` class docstring (line 508-514) to add a note that the dataclass
default `"auto"` is only used when no config file sets `workflow_mode`, and that the
production default is set via `config/common.toml`.

**Before (line 512):**
```python
    workflow_mode: "auto" (fallback with warning), "required" (hard error), "disabled" (always direct).
```

**After:**
```python
    workflow_mode: "auto" (fallback with warning), "required" (hard error), "disabled" (always direct).
        Production default is set via config/common.toml (workflow_mode = "required").
        Dataclass default "auto" is used only when no config file sets workflow_mode.
```

The docstring is on line 512, inside the `AgentConfig` class docstring block. The additional
two lines should be indented at 4 spaces (same as the rest of the docstring body) plus 4 more
for the continuation of the same bullet point — use 8-space indent to align under the first `w`
of `workflow_mode:`.

Alternatively, add as a separate bullet on the same indentation level:
```python
    """Mutable runtime configuration shared by all agent components.

    Composes 7 domain-specific sub-configs.
    Access fields via nested paths: cfg.llm.llm_url, cfg.rag.top_k_search, etc.
    workflow_mode: "auto" (fallback with warning), "required" (hard error), "disabled" (always direct).
        Production default: config/common.toml sets workflow_mode = "required".
        Dataclass default "auto" applies only when no config file is present (local/test).
    security_lockdown_enabled: suppress DENY-ALL warnings for intentional lockdowns.
    """
```

## Validation

Docstring-only change — visual inspection. No behavior change.
