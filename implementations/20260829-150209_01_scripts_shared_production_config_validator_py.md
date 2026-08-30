# Implementation Procedure: Config Floor Check for Git Tools (REQ-001)

## Goal

Prevent effective risk below HIGH for git_checkout/git_pull/git_push via a config floor check in ProductionConfigValidator.validate().

## Scope

Add `_check_approval_risk_floor()` helper to `scripts/shared/production_config_validator.py` that resolves effective risk per classify_risk()'s priority chain and returns tool names whose resolved risk is below HIGH. Call it from validate() using the existing self._record(errors, warnings, msg, is_production) pattern. In production mode this is an error (reject); in local-dev, a warning (allow with loud message).

## Assumptions

- The existing _TIER_TO_RISK mapping in scripts/agent/tool_policy.py correctly maps WRITE_DANGEROUS → RiskLevel.MEDIUM.
- The ProductionConfigValidator._record() method signature and error/warning separation pattern established by _check_missing_tool_safety_tiers() and _check_unknown_tool_safety_tiers() is stable and can be reused without modification.
- ADR-004 Environment Profile fail-fast/fail-open policy applies: production = error (reject), local-dev = warning (allow with loud message).

## Design decisions

- Follow the existing helper pattern already used in ProductionConfigValidator: standalone function + call from validate() via self._record(). Do not invent a new validation mechanism.
- The floor check resolves effective risk per classify_risk()'s priority chain: approval_risk_rules override → tool_safety_tiers → _TIER_TO_RISK fallback. An absent override falling back to WRITE_DANGEROUS tier's MEDIUM default must be caught too, not just an explicit "medium"/"low" override.
- The helper returns a list of tool names whose effective risk is below HIGH; validate() feeds results into self._record() following the existing pattern.

## Alternatives considered

- Inline the floor check directly in validate() rather than extracting a helper. Rejected: violates the existing pattern where each validation concern has its own helper (_check_missing_tool_safety_tiers, _check_unknown_tool_safety_tiers).
- Add the floor check to tool_policy.py alongside classify_risk(). Rejected: this belongs in the config validator, not the runtime classifier; the validator is the right place for startup-time config integrity checks.

## Implementation

### Target file

`scripts/shared/production_config_validator.py`

### Procedure

Add `_check_approval_risk_floor()` helper function and call it from `validate()`.

### Method

1. Define `_check_approval_risk_floor(approval_risk_rules, tool_safety_tiers, known_tools=None)` at module level, following the signature pattern of `_check_missing_tool_safety_tiers` and `_check_unknown_tool_safety_tiers`.
2. Resolve effective risk per classify_risk()'s priority chain for each git write tool:
   - Priority 1: approval_risk_rules override (if present, use its value mapped via RiskLevel enum)
   - Priority 2: tool_safety_tiers tier → _TIER_TO_RISK fallback
   - Return tool name if resolved risk < HIGH
3. Call from validate() after the existing tool_safety_tiers checks, before allowed_tools visibility check:
   ```python
   approval_risk_rules = config.get("approval_risk_rules")
   if isinstance(approval_risk_rules, Mapping):
       low_risk_tools = _check_approval_risk_floor(
           approval_risk_rules, tool_safety_tiers, known_tools=known_tools
       )
       if low_risk_tools:
           tool_list = "; ".join(low_risk_tools)
           msg = f"Effective risk below HIGH for git tools: {tool_list}"
           self._record(errors, warnings, msg, is_production)
   ```
4. Handle the case where approval_risk_rules is absent or not a Mapping: resolve effective risk using only tool_safety_tiers → _TIER_TO_RISK fallback for git tools.

### Details

```python
def _check_approval_risk_floor(
    approval_risk_rules: Mapping[str, object],
    tool_safety_tiers: Mapping[str, object],
    known_tools: set[str] | None = None,
) -> list[str]:
    """Return tool names whose resolved effective risk is below HIGH."""
    from agent.tool_policy import _TIER_TO_RISK, RiskLevel

    GIT_WRITE_TOOLS = frozenset(("git_checkout", "git_pull", "git_push"))
    resolved_tools = _resolve_known_tools(known_tools)
    if resolved_tools is None:
        return []
    # Only check git write tools that are actually registered
    targets = GIT_WRITE_TOOLS & resolved_tools
    below_high: list[str] = []
    for tool_name in sorted(targets):
        # Priority 1: approval_risk_rules override
        raw_rule = approval_risk_rules.get(tool_name)
        if raw_rule is not None:
            try:
                base = RiskLevel(raw_rule)
            except ValueError:
                continue  # invalid rule value, skip this tool
        # Priority 2: tool_safety_tiers → _TIER_TO_RISK fallback
        elif tool_name in tool_safety_tiers:
            tier = tool_safety_tiers[tool_name]
            base = _TIER_TO_RISK.get(tier, RiskLevel.MEDIUM)
        else:
            # No override and no tier entry: falls through to UNKNOWN path
            # which classify_risk treats as HIGH — so no flag needed
            continue
        if base != RiskLevel.HIGH:
            below_high.append(f"'{tool_name}' effective risk={base}")
    return below_high
```

## Compatibility considerations

- This change adds a new validation check that may cause production deployments to reject configs that previously passed validation. Existing configs with git_checkout/git_pull/git_push = "high" will pass; configs missing these overrides or set to lower values will be rejected.
- The helper imports from agent.tool_policy at runtime inside the function body to avoid circular import issues during module initialization.

## Security considerations

- This is a security enhancement: preventing accidental config downgrade of git write tools below HIGH tier.
- The floor check catches both explicit downgrades (e.g., "medium") and implicit downgrades (absent override reverting to WRITE_DANGEROUS tier's MEDIUM default).

## Rollback considerations

- If the floor check causes false positives in production, revert by removing the call from validate() and the helper function. The underlying risk classification logic remains unchanged.

## Validation plan

- Unit test for config floor check: accepts "high", rejects/warns on "medium"/"low"/absent-override-with-low-tier.
- Test cases:
  1. All three git tools set to "high" → empty result (no violations)
  2. One or more git tools set to "medium" → non-empty result listing violated tools
  3. One or more git tools set to "low" → non-empty result listing violated tools
  4. Git tools absent from approval_risk_rules but present in tool_safety_tiers with WRITE_DANGEROUS tier → non-empty result (implicit MEDIUM)
  5. Git tools absent from both approval_risk_rules and tool_safety_tiers → empty result (classify_risk would treat as HIGH)

## Completion criteria

- `_check_approval_risk_floor()` helper exists and resolves effective risk per classify_risk()'s priority chain.
- validate() calls the helper and feeds results into self._record(errors, warnings, msg, is_production).
- In production mode, violations are errors (rejected); in local-dev, warnings (allowed with loud message).
- Unit test covers all five scenarios above.

## Out of scope

- Adding floor checks for non-git tools.
- Modifying classify_risk() itself.
- Changing the _prompt_user_approval() behavior.
- Updating audit_approval() recording.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement _check_approval_risk_floor() helper in scripts/shared/production_config_validator.py | Pending | — | — | |
| 2 | Call the helper from validate() via self._record() | Pending | — | — | |
| 3 | Write unit test for config floor check | Pending | — | — | |

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
- **Source issue**: issues/20260828-163234_mcp004_approval_risk_hierarchy_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-150209_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-205709
- **Related target files**: scripts/shared/production_config_validator.py
