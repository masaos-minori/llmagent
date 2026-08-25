# `memory_embed_enabled` is not detected as a startup-only field on reload

## Priority
Medium

## Summary
`_detect_startup_only()` in `config_reload.py` only checks `use_memory_layer` and `routing_drift_strict`. `memory_embed_enabled` (`MemoryConfig`) is also effectively startup-only — `AgentConfig.__post_init__` enforces `memory_embed_enabled and not rag.embed_url` as an invariant, and nothing re-evaluates that dependency on reload — but it is not detected, so a user who changes it via `/reload` gets no "startup-only / restart required" signal and the change is silently ignored.

## Background
N/A: covered by Summary.

## Problem
Verified:
- `scripts/agent/services/config_reload.py:_detect_startup_only()` (lines 431-444) checks exactly two fields: `use_memory_layer` and `routing_drift_strict`.
- `scripts/agent/config_dataclasses.py:250` defines `memory_embed_enabled: bool = True` on `MemoryConfig`.
- `scripts/agent/config_dataclasses.py:481-483` (`AgentConfig.__post_init__` or equivalent) enforces: `if self.memory.memory_embed_enabled and not self.rag.embed_url: raise ...` — confirming this field participates in a startup-time-only invariant check, consistent with it being startup-only.
- No code path was found in `config_reload.py` that updates `memory_embed_enabled` on `/reload`, so today it is neither reloadable nor reported as startup-only — a silently-ignored reload request.

## Reason for Change
Without detection, an operator who requests this change via `/reload` receives no feedback that the request had no effect, and may incorrectly believe the new value is active.

## Implementation Intent
Add `memory_embed_enabled` to `_detect_startup_only()` following the exact pattern already used for `use_memory_layer` and `routing_drift_strict`.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`

## Required Changes
- In `_detect_startup_only()`, add:
  ```
  v = _get_bool(new_cfg, "memory_embed_enabled")
  if v is not None and v != ctx.cfg.memory.memory_embed_enabled:
      changed.append("memory_embed_enabled")
  ```

## Constraints
- This only adds *detection and reporting*; it does not make `memory_embed_enabled` actually hot-reloadable (see Out of Scope).

## Acceptance Criteria
- [ ] Changing `memory_embed_enabled` via `/reload` is reported under `startup_only` in the reload outcome.
- [ ] Existing `use_memory_layer` / `routing_drift_strict` startup-only detections remain intact.

## Testing Expectations
- Unit test: reloading with a different `memory_embed_enabled` value adds `"memory_embed_enabled"` to `ConfigReloadOutcome.startup_only`.
- Regression: existing `_detect_startup_only()` tests for the other two fields continue to pass.

## Documentation Impact
If `docs/05_agent_07_06_cli-and-commands-hot-reload.md` (or the equivalent hot-reload scope doc) lists which fields are startup-only, add `memory_embed_enabled` to that list.

## Out of Scope
- Making `memory_embed_enabled` actually hot-reloadable.
- Any other `MemoryConfig` field not already covered.

## Dependencies
- N/A: none.

## Unresolved Questions
- N/A: none.

## AI Implementation Instruction
This is a small, well-scoped addition mirroring an existing pattern — do not attempt to make the field hot-reloadable as part of this issue; that would require re-validating the `memory_embed_enabled` + `rag.embed_url` invariant on reload, which is out of scope here.
