## Goal
- Make the component-mandatoriness registry and the governance documents consistent about why all 10 MCP servers are `required` and which source is canonical for that classification, by closing the two inventory items MCP-003 and MCP-004 once the maintainer has decided the questions that only the maintainer can answer.

## Priority
Medium

## Scope
- **In-Scope**: the registry rationale (and, if decided, `failure_category`) of the 10 entries; the regenerated manifest and generated table that mirror the registry; the governance_01 or canonical-source-registry text that places the registry under a claim type; removing or updating MCP-003 and MCP-004 in the governance inventory.
- **Out-of-Scope**: changing any classification away from `required` or any `startup_consequence`; the ADR-004 Group 2 item 7 justification itself (Needs Confirmation NC-002, carried in mcpai012); ADR-004 text changes; code under `scripts/`; writing an approver, a date, or an approval sentence.
- **Dependencies**: None open. The maintainer decisions UNK-01 and UNK-02 gate this Plan.

## Background
Source Issue: `gov003`, from governance Known Issues MCP-003 (Medium) and MCP-004 (Low). Verified in Step 2 (adversarial verification against the registry, ADR-004, governance_01, and the canonical-source registry):
- The registry holds 10 entries, each `classification: required`, `startup_consequence: abort_startup`, `failure_category: safety-integrity`, with the rationale `Not assessed as satisfying Decision Group 3 item 10; status quo default`; the `agent_08_04` table is generated from it and shows the same rationale.
- The Issue's premise for MCP-003 (an approved per-server item-10 assessment is missing) is contestable. ADR-004 `### Group 7` records a repository owner instruction of 2026-11-10 (option B): every component in the registry is classified `required`. Decision Group 3 item 10 lists the criteria a component must meet to be non-mandatory, and item 12 says an undetermined classification is not assumed non-mandatory. For a `required` classification the item-10 criteria are not what decides it. What is verifiably missing is that the registry rationale does not cite the owner instruction.
- `failure_category` is `safety-integrity` for all 10 entries, while ADR-004 Decision Group 2 item 7 lists the unavailability of an MCP server among availability failures. Whether the field should follow item 7 is a maintainer question (for a `required` component the startup outcome is abort either way, item 8).
- MCP-004's premise differs from the files: the governance_01 `### Resolution Matrix` is a table by claim type (13 rows) with no per-decision-target row and no owner column, so there is no `mcp.component-mandatoriness` row whose owner list could be approved. The actual mismatch: `config/documentation_canonical_sources.toml` registers `registry/component_mandatoriness.yaml` for the decision target `mcp.component-mandatoriness` under claim type `security-policy`, while the governance_01 `security-policy` row names only Accepted security ADRs (ADR-007, ADR-012, ADR-013) as canonical source kind. `check_canonical_source_registry.py` passes, so the registry is accepted by the tool.
- The Issue cites `check_canonical_sources.py`, which does not exist; the checker is `tools/check_canonical_source_registry.py`.

## Problem
The registry says `Not assessed` for a classification that an owner instruction already fixed, and the policy document and the canonical-source registry describe the registry's authority differently, so the inventory items stay open without a clear closing action.

## Reason for Change
Readers cannot tell whether the all-required classification is approved, and the registry's claim type has no matching canonical-source description.

## Implementation Intent
After the maintainer states (a) whether the Option B owner instruction satisfies ADR-004 item 13 and what `failure_category` should be, and (b) where the registry's authority is documented, apply the matching wording changes mechanically, regenerate the mirrors, and close MCP-003 and MCP-004.

## Requirements
- `REQ-001`: Each of the 10 registry rationales cites the owner instruction recorded in ADR-004 Group 7 (option B, 2026-11-10) instead of `Not assessed`, with no classification change (applies only if UNK-01 is answered that the instruction suffices).
- `REQ-002`: `failure_category` is changed, or confirmed as `safety-integrity`, per the maintainer's answer (UNK-01); the change would be limited to the field's values.
- `REQ-003`: The registry's claim type and its governance description agree: either the governance_01 `security-policy` canonical-source-kind text names the registry (and ADR-004 item 13), or the canonical-source registry entry changes its claim type, per the maintainer's answer (UNK-02).
- `REQ-004`: The generated mirrors (`registry/manifests/component_mandatoriness.yaml` and the `agent_08_04` table) are regenerated, not hand-edited.
- `REQ-005`: MCP-003 and MCP-004 are removed from the inventory with validation evidence, or updated to the remaining open question, per the maintainer's answers; no approval text is written.

## Implementation Target Files
**Freeze status**: Draft

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| registry/component_mandatoriness.yaml | modify: rationale of the 10 entries (and `failure_category` if decided) | The rationale says `Not assessed` although an owner instruction exists | REQ-001, REQ-002; AC-1 | `component_mandatoriness.yaml:1-30` (10 entries, rationale lines); `adr_02_01_004...md:98` (checked in Step 2) | `tests/tools/test_check_component_mandatoriness.py` | Needs confirmation |
| registry/manifests/component_mandatoriness.yaml | modify: regenerate the manifest mirror | The manifest copies the rationale text | REQ-004; AC-3 | `manifests/component_mandatoriness.yaml` carries 10 `rationale` lines (checked in Step 3) | N/A: generated, `generate_reference_table.py --check` | Verified |
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | modify: regenerate the generated mandatoriness table | The generated table shows the rationale column | REQ-004; AC-3 | `agent_08_04...md` AUTO-GENERATED `component-mandatoriness-reference` block (checked in Step 3) | N/A: generated, `generate_reference_table.py --check` | Verified |
| docs/00_governance/governance_01_documentation-policy.md | modify: name the registry in the `security-policy` canonical-source kind (only if UNK-02 chooses this option) | The row names only ADRs while the registry is registered under `security-policy` | REQ-003; AC-2 | `governance_01...md:120-135` (Resolution Matrix has no owner column or per-target rows; checked in Step 2) | N/A: documentation | Needs confirmation |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | modify: remove or update MCP-003 and MCP-004 | The entries rest on premises Step 2 found contestable | REQ-005; AC-4 | `governance_03...md:154-192` (checked in Step 2) | N/A: documentation (`check_issue_inventory_conformance.py`) | Needs confirmation |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | Group 3 items 10, 12, 13, Group 2 item 7, and the Group 7 owner instruction | REQ-001, REQ-002 |
| config/documentation_canonical_sources.toml | Registers the registry under `security-policy` (lines 66-71) | REQ-003 |
| tools/check_canonical_source_registry.py | Validates the canonical-source registry (the Issue named a nonexistent `check_canonical_sources.py`) | REQ-003 |
| tools/check_component_mandatoriness.py | Registry versus `config/agent.toml` consistency | REQ-001 |
| scripts/shared/component_mandatoriness.py | Registry schema and loader (fields and coercions) | REQ-001, REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): No registry rationale says `Not assessed`; each cites the Group 7 owner instruction or the maintainer's recorded decision; no classification or `startup_consequence` value changed; `failure_category` is as decided.
- `AC-2` (REQ-003): One description of the registry's claim type and canonical source exists across `governance_01` and `config/documentation_canonical_sources.toml`, and `check_canonical_source_registry.py` passes.
- `AC-3` (REQ-004): `generate_reference_table.py --check` exits 0 with the manifest and generated table regenerated.
- `AC-4` (REQ-005): MCP-003 and MCP-004 are removed or updated to the remaining question with evidence, and the conformance checkers pass.

## Tests
- `uv run pytest tests/tools/test_check_component_mandatoriness.py tests/shared/test_component_mandatoriness.py tests/tools/test_check_canonical_source_registry.py -q` (REQ-001 to REQ-003).
- `uv run python tools/check_component_mandatoriness.py`, `check_canonical_source_registry.py`, `generate_reference_table.py --check`, `check_issue_inventory_conformance.py`, and `tools/run_validation_gates.py` (REQ-001 to REQ-005).

## Documentation Impact
Yes: the registry mirrors, `agent_08_04` (generated), the governance policy or canonical-source registry text, and the governance inventory.

## Assumptions
- Rewording a rationale to cite an owner instruction that ADR-004 already records is a factual documentation change, not a classification change; if the maintainer disagrees, UNK-01 is answered differently and this Plan is revised.
- The `required` classification of all 10 servers and their `abort_startup` consequence are unchanged by this Plan.
- Path B because the change spans 5 files including a contract registry and its generated mirrors; no Python or schema change, so the baseline is `N/A: no Python target` and the persisted-schema check does not apply.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Does the repository owner instruction of 2026-11-10 (ADR-004 Group 7, option B) satisfy ADR-004 Decision Group 3 item 13's approved classification for all 10 servers, and should `failure_category` stay `safety-integrity` or follow Group 2 item 7? | No maintainer statement; decides whether the registry rationale text, the `failure_category` values, or neither change, and thus what rows 1 to 3 contain | The maintainer answers; the Plan is then frozen | True |
| UNK-02 | Where is the registry's authority documented: amend the governance_01 `security-policy` canonical-source kind to name the registry, or change the registry's claim type in `config/documentation_canonical_sources.toml`? | No maintainer statement; decides whether `governance_01` or the canonical-source registry is the file that changes | The maintainer answers; the Plan is then frozen | True |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| registry/component_mandatoriness.yaml | Modify | Medium | 2 | N/A | none (contract data read by startup validation; no new file) |
| registry/manifests/component_mandatoriness.yaml | Modify | Low | 3 | N/A | none (generated) |
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | Modify | Low | 8 | N/A | none (generated block) |
| docs/00_governance/governance_01_documentation-policy.md | Modify | Medium | 4 | N/A | none (documentation) |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Modify | Medium | 19 | N/A | none (documentation) |

## Design
- Rationale text (if UNK-01 is answered yes): `Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification` for every entry; generated mirrors are regenerated with `generate_reference_table.py --manifests` and `--type mandatoriness`.
- Authority text (UNK-02): option 1 edits the `security-policy` row of the governance_01 matrix (canonical source kind: add the registry entry and ADR-004 item 13); option 2 changes the registry's `claim_type` in `config/documentation_canonical_sources.toml`. Recommendation: option 1, since the registry already is the machine-readable source of ADR-004 item 13's classification and the matrix row is the narrower statement.
- Alternatives: a full per-server item-10 assessment (rejected as the default: it would assess non-mandatory criteria for components that are all required); hand-editing the generated table (rejected: the generator owns it).
- Predictable fallout: the manifest and generated table are rows; the pinned manifest tests are `not affected` by a text-only change; module size and tool inventory do not apply.
- Consumer scan and persisted-schema check: not applicable (no symbol, constant, or schema change).

## Implementation steps
1. **Phase 1: Registry wording**
   - [ ] Apply the maintainer's UNK-01 answer to the 10 rationales and `failure_category` (REQ-001, REQ-002; registry/component_mandatoriness.yaml)
   - [ ] Regenerate the manifest and the generated table (REQ-004; registry/manifests/component_mandatoriness.yaml, docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md)
2. **Phase 2: Authority wording**
   - [ ] Apply the maintainer's UNK-02 answer (REQ-003; docs/00_governance/governance_01_documentation-policy.md)
3. **Phase 3: Inventory and verification**
   - [ ] Remove or update MCP-003 and MCP-004 (REQ-005; docs/00_governance/governance_03_issue-and-uncertainty-management.md)
   - [ ] Run the tests, checkers, and gates in Validation plan (REQ-001 to REQ-005). No deploy step: no `scripts/` or `config/` change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| registry/component_mandatoriness.yaml | Unit and consistency | `uv run pytest tests/tools/test_check_component_mandatoriness.py tests/shared/test_component_mandatoriness.py -q`; `uv run python tools/check_component_mandatoriness.py` | Pass; no classification change |
| Generated mirrors | Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Authority wording | Registry check | `uv run python tools/check_canonical_source_registry.py`; `uv run pytest tests/tools/test_check_canonical_source_registry.py -q` | Pass |
| Inventory | Conformance | `uv run python tools/check_issue_inventory_conformance.py`; `uv run python tools/run_validation_gates.py` | Pass |

## Risks
- **Risk**: The maintainer decides the owner instruction does not satisfy item 13 and wants a real per-server assessment → **Mitigation**: UNK-01 is blocking, so no registry text is written before the answer.
- **Risk**: A reworded rationale reads as an approval → **Mitigation**: the text only cites the existing ADR-004 owner instruction; no approver or date is written.
- **Risk**: The registry is a contract file read by startup validation → **Mitigation**: only string fields change, and the checker and loader tests run.
- **Risk**: Generated mirrors drift if the wording is edited without regeneration → **Mitigation**: regenerate and run `--check` in the same step.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Registry wording | Pending | — | — | |
| 2 | Authority wording | Pending | — | — | |
| 3 | Inventory and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01 (maintainer answer on item 13 and `failure_category`) is unresolved | — | — |
| 2 | UNK-02 (maintainer answer on where the registry's authority is documented) is unresolved | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261123-104602_gov003_mandatoriness-assessment-registry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-111105
- **Related target files**: registry/component_mandatoriness.yaml, registry/manifests/component_mandatoriness.yaml, docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md, docs/00_governance/governance_01_documentation-policy.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (record the result in the registry); ADR-004 Group 7 owner instruction | registry/component_mandatoriness.yaml | Phase 1 | AC-1 | `test_check_component_mandatoriness.py` | Needs confirmation |
| REQ-002 | Issue Required Changes (`failure_category` question); ADR-004 Group 2 item 7 | registry/component_mandatoriness.yaml | Phase 1 | AC-1 | `check_component_mandatoriness.py` | Needs confirmation |
| REQ-003 | Issue Required Changes (owner list); governance_01 Resolution Matrix, canonical-source registry | docs/00_governance/governance_01_documentation-policy.md | Phase 2 | AC-2 | `check_canonical_source_registry.py` | Needs confirmation |
| REQ-004 | Step 3 evidence: generated table and manifest | registry/manifests/component_mandatoriness.yaml | Phase 1 | AC-3 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-004 | Step 3 evidence: generated table and manifest | docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | Phase 1 | AC-3 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-005 | Issue Acceptance Criteria (MCP-003 and MCP-004 removed) | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 3 | AC-4 | `check_issue_inventory_conformance.py` | Needs confirmation |
