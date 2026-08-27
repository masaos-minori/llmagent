## Goal

Add `memory_embed_enabled` detection to `_detect_startup_only()` so operators reloading this field receive feedback that a restart is required.

## Scope

**In-Scope**:
- `scripts/agent/services/config_reload.py`: add `memory_embed_enabled` diff-detection to `_detect_startup_only()`.
- Add a test case verifying the detection behavior.

**Out-of-Scope**:
- Making `memory_embed_enabled` hot-reloadable (would require re-validating `memory_embed_enabled + rag.embed_url` invariant on reload).
- Other `MemoryConfig` fields.

## Assumptions

- The existing pattern (`_get_bool` → diff comparison → `changed.append()`) is correct and should be followed exactly.
- No changes to `use_memory_layer` or `routing_drift_strict` detection logic.

## Design decisions

- Follow the exact same shape as existing startup-only detections: `_get_bool()` → diff comparison → `changed.append()`.
- No signature changes to any method.

## Alternatives considered

- Make `memory_embed_enabled` hot-reloadable: rejected because it would require revalidating the invariant `memory_embed_enabled=True => embed_url must be non-empty` on each reload, which is tracked separately.
- Inline the invariant check inside `_detect_startup_only`: rejected because it would duplicate logic already present in `AgentConfig.__post_init__`.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. In `_detect_startup_only()` (line ~431), after the `routing_drift_strict` block (line 444), add the `memory_embed_enabled` detection.
2. Add a test case verifying `"memory_embed_enabled"` appears in `ConfigReloadOutcome.startup_only` when the field value differs.

### Method

```python
# --- Phase 2: Core Logic Implementation ---

# REQ-001: Add memory_embed_enabled to _detect_startup_only()
# After line 444 (routing_drift_strict block), before "return changed":

        v = _get_bool(new_cfg, "memory_embed_enabled")
        if v is not None and v != ctx.cfg.memory.memory_embed_enabled:
            changed.append("memory_embed_enabled")

# --- Phase 3: Deployment & Verification ---

# New test case (REQ-001):
# In tests/agent/services/test_config_reload*.py, add:
#
# def test_detect_startup_only_memory_embed_enabled():
#     """Verify memory_embed_enabled differences are reported as startup-only."""
#     ctx = make_context(memory_embed_enabled=True)  # or use existing fixture
#     outcome = ctx.services.config_reload.apply_config_dict({
#         "memory_embed_enabled": False,
#     })
#     assert "memory_embed_enabled" in outcome.startup_only
```

### Details

- **Line placement**: Insert after line 444 (`routing_drift_strict` block), before `return changed` (line 445).
- **Pattern match**: Uses `_get_bool` exactly like other startup-only detections in this function.
- **Assignment target**: `ctx.cfg.memory.memory_embed_enabled` where `ctx = self._ctx` (bound at line 437).
- **Test**: New test case only — no modifications to existing `use_memory_layer` / `routing_drift_strict` tests. Test verifies both the state change (`outcome.startup_only` contains `"memory_embed_enabled"`) and that existing detections remain unchanged.

## Compatibility considerations

- Public API unchanged (`ConfigReloadRequest`, `ConfigReloadOutcome`).
- Existing 2 startup-only fields unaffected.
- No config schema changes required — `memory_embed_enabled` already exists in `MemoryConfig`.

## Security considerations

- No new secrets or credentials introduced.
- This is purely an informational change — operators will now get proper feedback about startup-only fields.

## Rollback considerations

- Revert: remove the single added block from `_detect_startup_only()`.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/services/config_reload.py`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload*.py -v` | New test green, existing 2-field detections pass |

## Completion criteria

- [ ] `memory_embed_enabled` diff-detection block exists in `_detect_startup_only()` after `routing_drift_strict` handler.
- [ ] New test case verifies `"memory_embed_enabled"` appears in `outcome.startup_only` when value differs.
- [ ] Existing `use_memory_layer` / `routing_drift_strict` tests still pass.
- [ ] `mypy scripts/` reports no new type errors.

## Out of scope

- Making `memory_embed_enabled` hot-reloadable.
- Changes to the `memory_embed_enabled + rag.embed_url` invariant validation.
- Modifying field update logic semantics for other fields.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation / Refactoring | Pending | — | — | Awaiting implementation |
| 2 | Core Logic Implementation | Pending | — | — | Awaiting implementation |
| 3 | Deployment & Verification | Pending | — | — | Awaiting implementation |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260825_cfgreload_memory_embed_enabled_startup_only_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-142047_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_reload.py
