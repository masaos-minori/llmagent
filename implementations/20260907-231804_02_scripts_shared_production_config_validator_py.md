## Goal

Add unknown-top-level-key rejection in `ProductionConfigValidator.validate()` — reject configuration keys that are not present among the valid top-level keys derived from `config_dataclasses.py` via introspection (REQ-004).

## Scope

Modify exactly one file: `scripts/shared/production_config_validator.py`. Add a new method `_check_unknown_top_level_keys()` and call it from `validate()`.

## Assumptions

- Valid top-level config keys can be derived by iterating over all dataclass fields across all 9 sub-configs (`LLMConfig`, `RAGConfig`, `ToolConfig`, `MemoryConfig`, `MCPConfig`, `ApprovalConfig`, `ObservabilityConfig`, `DiagnosticsConfig`, `MessageRoleConfig`) in `scripts/agent/config_dataclasses.py` using `dataclasses.fields()`.
- The TOML config uses flat keys (e.g., `llm_url`, `embed_url`) while AgentConfig represents nested sub-configs. The mapping between raw TOML keys and dataclass field names needs to be worked out during implementation — some values are read via `cfg.get("some_key")` inside `_build_*` helper functions under different names or nested paths.
- Only production environments need this check (consistent with `ProductionConfigValidator`'s existing `is_production` gating).

## Design decisions

- Derive valid top-level keys by collecting `field.name` from all 9 sub-config dataclasses via `dataclasses.fields()`, then flattening into a single set. This approach follows the same pattern as the existing `_check_unknown_tool_safety_tiers` / `_check_missing_tool_safety_tiers` bidirectional checks but generalized from one nested mapping to the config's top-level key set.
- Add the check only in the `is_production` branch of `validate()` to avoid breaking development/local workflows where unknown keys may be intentional.
- Report unknown keys as errors (not warnings), consistent with how `_check_unknown_tool_safety_tiers` treats its findings.

## Alternatives considered

- Hand-maintaining a static allowlist of valid top-level keys: rejected because it could drift out of sync with `config_dataclasses.py` dataclass definitions.
- Using pydantic `extra="forbid"`: rejected because `config_dataclasses.py` uses plain `@dataclass` definitions, not pydantic models.
- Adding the check to `ConfigLoader.load_all()` instead of `ProductionConfigValidator`: rejected because `ConfigLoader` is used in non-production contexts (RAG pipeline, CLI commands) where strict validation is not required.

## Implementation
### Target file
`scripts/shared/production_config_validator.py`

### Procedure
Add a new method `_check_unknown_top_level_keys()` and call it from `validate()`.

### Method
1. In `scripts/shared/production_config_validator.py`, add a new private method `_check_unknown_top_level_keys(config: Mapping[str, object]) -> list[str]`:
   - Import `dataclasses` module.
   - Iterate over all 9 sub-config dataclasses from `agent.config_dataclasses` (LLMConfig, RAGConfig, ToolConfig, MemoryConfig, MCPConfig, ApprovalConfig, ObservabilityConfig, DiagnosticsConfig, MessageRoleConfig).
   - For each dataclass, collect `field.name` from `dataclasses.fields()` into a set.
   - Compare against `config.keys()` and return any keys not found in the collected set.
2. Call this method from `validate()` alongside existing checks, within the `is_production` branch.

### Details
1. Open `scripts/shared/production_config_validator.py`.
2. At the top of the file, ensure `import dataclasses` is present.
3. Add the new method before the `validate()` method:
```python
    def _check_unknown_top_level_keys(
        self, config: Mapping[str, object]
    ) -> list[str]:
        """Check for unknown top-level config keys not in dataclass fields."""
        from agent.config_dataclasses import (
            LLMConfig, RAGConfig, ToolConfig, MemoryConfig,
            MCPConfig, ApprovalConfig, ObservabilityConfig,
            DiagnosticsConfig, MessageRoleConfig,
        )
        known_fields: set[str] = set()
        for dc in (LLMConfig, RAGConfig, ToolConfig, MemoryConfig,
                   MCPConfig, ApprovalConfig, ObservabilityConfig,
                   DiagnosticsConfig, MessageRoleConfig):
            known_fields.update(f.name for f in dataclasses.fields(dc))
        unknown = [k for k in config if k not in known_fields]
        return unknown
```
4. In `validate()`, after the existing `tool_safety_tiers` check (around line 155), add:
```python
        # Unknown top-level key check (production only)
        if self.is_production:
            unknown_keys = self._check_unknown_top_level_keys(config)
            if unknown_keys:
                key_msg = "; ".join(repr(k) for k in unknown_keys)
                self._record(errors, warnings, f"Unknown top-level keys: {key_msg}")
```

## Compatibility considerations

- Development/local environments are unaffected (check is gated behind `is_production`).
- Existing production configs must contain only keys derived from the 9 sub-config dataclasses; any unknown keys will now cause a validation error.
- If the TOML key → dataclass field mapping is ambiguous for a given key during implementation, stop and report rather than guessing.

## Security considerations

This change closes a security-relevant gap: a typo'd or mistyped top-level config key was previously silently absorbed into the merged dict with no warning at any layer. Rejecting unknown keys prevents misconfiguration from reaching production undetected.

## Rollback considerations

Reverting this change means removing the `_check_unknown_top_level_keys()` method and its call site. If the change causes unexpected failures in deployment, the rollback is straightforward. However, reverting re-introduces the silent-absorption vulnerability for unknown keys.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/production_config_validator.py` | Unit: verify unknown key rejection in production | `pytest -xvs` on new test | Validation error returned |
| `scripts/shared/production_config_validator.py` | Unit: verify known keys pass validation | `pytest -xvs` on new test | No errors |
| `scripts/shared/production_config_validator.py` | Unit: verify dev environment allows unknown keys | `pytest -xvs` on new test | No errors in dev mode |

## Completion criteria

- [ ] `ProductionConfigValidator.validate()` rejects unknown top-level config keys in production
- [ ] Known top-level keys derived from `config_dataclasses.py` dataclass fields pass validation
- [ ] Non-production environments do not enforce unknown-key rejection
- [ ] New unit test exists asserting unknown-key rejection behavior
- [ ] Existing tests pass without modification

## Out of scope

- Modifying `config_dataclasses.py` to add validators or fix field naming gaps.
- Adding the unknown-key check to `ConfigLoader.load()` or `load_all()`.
- Handling nested key validation beyond top-level keys (requires separate investigation per UNK-02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement _check_unknown_top_level_keys() method | Pending | — | — | |
| 2 | Call _check_unknown_top_level_keys() from validate() | Pending | — | — | |
| 3 | Add unit tests for unknown-key rejection | Pending | — | — | |
| 4 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-203653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-07T23:18:04Z
- **Related target files**: scripts/shared/production_config_validator.py
