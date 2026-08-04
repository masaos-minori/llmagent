## 1. Goal
- Propagate the fact that `config/agent.toml`'s `tool_names` field is not used for routing or circuit-breaker state, but only for drift validation/observation, to ensure consistency across documentation files.

## 2. Scope
- **In-Scope**:
  - Update `docs/04_mcp_01_system_overview.md` with a clarifying note regarding `tool_names`.
  - Update `docs/04_mcp_06_09_mcp-failure-diagnosis.md` with a clarifying note regarding `tool_names`.
- **Out-of-Scope**:
  - Modifying source code.
  - Modifying `docs/04_mcp_03_01_dispatch-and-routing.md`.
  - Modifying other documentation files.

## 3. Assumptions
- The current wording in `docs/04_mcp_03_01_dispatch-and-routing.md` is correct and serves as the authoritative phrasing.
- Adding these notes will resolve potential reader confusion without requiring restructuring of existing sections.

## 4. Unknowns & Gaps
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Preferred exact placement in `docs/04_mcp_01_system_overview.md` beyond "near the table" | N/A | Follow implementation intent in requirement | False |

## 5. Affected Areas & Tool Evidence
- **Affected Files**:
  - `docs/04_mcp_01_system_overview.md`
  - `docs/04_mcp_06_09_mcp-failure-diagnosis.md`
- **Blast Radius**: Minimal (documentation only).
- **Risk Metrics**: Low risk.
- **Deploy Impact**: None.

## 6. Implementation Steps
1. **Phase 1: Preparation**
   - [ ] Verify exact wording in `docs/04_mcp_03_01_dispatch-and-routing.md` (already done during analysis).
2. **Phase 2: Core Logic Implementation (Documentation Updates)**
   - [ ] Edit `docs/04_mcp_01_system_overview.md` to add the note following the Major Components table.
   - [ ] Edit `docs/04_mcp_06_09_mcp-failure-diagnosis.md` to add the note at the end of the `McpServerHealthRegistry` section.
3. **Phase 3: Deployment & Verification**
   - [ ] Manually verify both files contain the correct text and formatting.

## 7. Validation Plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_01_system_overview.md` | Manual Inspection | `grep` or `Read` | Contains clarification about `tool_names` and its relation to `RuntimeToolRegistry`. |
| `docs/04_mcp_06_09_mcp-failure-diagnosis.md` | Manual Inspection | `grep` or `Read` | Contains clarification about `tool_names` and its relation to circuit breakers. |

## 8. Risks & Mitigations
- **Risk**: Inconsistent wording between the two new additions. → **Mitigation**: Strictly follow the wording from `docs/04_mcp_03_01_dispatch-and-routing.md`.
