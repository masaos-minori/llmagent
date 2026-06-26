## Goal

Make the quality impact of `use_rrf=False` more visible in diagnostics, debug output, and configuration docs so operators understand this is a significant degradation, not a harmless fallback mode.

## Scope

**In-Scope**:
- Ensure diagnostics include `fusion_mode="dedup_only"` when `use_rrf=False` (already implemented)
- Add debug output that explicitly says rank signal is disabled
- Add configuration documentation warning about retrieval quality degradation (already partially documented)
- Optionally emit startup/config warning when `use_rrf=False` (already exists in config_validator.py)

**Out-of-Scope**:
- Removing `use_rrf=False`
- Changing RRF scoring formula

## Assumptions

1. Diagnostics already include `fusion_mode` — confirmed by pipeline.py:554
2. Startup warning already exists — confirmed by config_validator.py:33
3. Debug output improvement needed — output_port.py:75 shows `use_rrf={value}` but doesn't explicitly state quality impact

## Implementation

### Target file: scripts/rag/stages/fusion.py

**Procedure**: Upgrade FusionStage log level, add quality impact description.

**Method**: Modify log message in fusion.py.

**Details**:
1. Change INFO-level message in fusion.py:22 to WARNING or add a separate WARNING-level message
2. Include quality impact description: "FusionStage: dedup-only mode (use_rrf=False) — rank signal disabled, MQE provides no ranking benefit"

### Target file: scripts/agent/commands/output_port.py

**Procedure**: Enhance debug output in --debug mode.

**Method**: Modify debug output formatting in output_port.py.

**Details**:
1. Update output_port.py:75 to explicitly state "rank signal disabled" when `use_rrf=False`
2. Example: `[debug] fusion: use_rrf=False (rank signal disabled) rrf_k=60`

### Target file: docs/03_rag_03_query_pipeline.md

**Procedure**: Strengthen configuration documentation.

**Method**: Add prominent warning in documentation near `use_rrf` definition.

**Details**:
1. Add prominent warning in 03_rag_03_query_pipeline.md near the `use_rrf` definition
2. Make the quality tradeoff table more visible (add callout/warning box)

### Target file: docs/03_rag_05_configuration_and_operations.md

**Procedure**: Verify startup warning is displayed.

**Method**: Confirm config_validator.py warning is surfaced to operators during startup.

**Details**:
1. Confirm config_validator.py warning is displayed to operators during startup
2. Add documentation about where the warning appears

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| output_port.py | Verify debug output explicitly states rank signal disabled | Check debug output formatting | `[debug] fusion: use_rrf=False (rank signal disabled)` present |
| fusion.py | Verify WARNING-level message when use_rrf=False | Review log level change | WARNING or prominent INFO message with quality impact |
| docs/03_rag_03_query_pipeline.md | Verify warning is prominent | Check documentation formatting | Quality tradeoff table visible near use_rrf definition |

## Risks

- **Risk**: Upgrading log level to WARNING may cause excessive log noise in production environments where use_rrf=False is intentionally used | **Likelihood**: Medium | **Mitigation**: Keep INFO level but make the message more prominent (add `[WARNING]` prefix in message text); or add separate WARNING-level message only when dedup-only mode is first activated | False
