## Goal
- Make the component-mandatoriness registry rationale and the two governance inventory entries MCP-003 and MCP-004 state what the repository verifiably records: all 10 MCP servers are `required` by the repository owner instruction of 2026-11-10 (ADR-004 Group 7, option B). Two questions that only the maintainer can answer stay open and are recorded as such, not decided here.

## Priority
Medium

## Scope
- **In-Scope**: the registry rationale text of the 10 entries and the stale header comment of the registry file; the regenerated manifest and generated table that mirror the registry; narrowing MCP-003 to its remaining open question and correcting the premise of MCP-004 in the governance inventory.
- **Out-of-Scope**: changing any classification away from `required`, any `startup_consequence`, or any `failure_category`; deciding whether `failure_category` should follow ADR-004 Group 2 item 7 (remaining maintainer question); deciding where the registry's authority is documented (`governance_01` matrix versus the claim type in `config/documentation_canonical_sources.toml`, remaining maintainer question; so `governance_01` and the canonical-source registry are not modified); the ADR-004 item 7 justification itself (AAL-019); ADR-004 text changes; code under `scripts/`; writing an approver, a date, or an approval sentence.
- **Dependencies**: None open. The two maintainer questions no longer gate this Plan; they stay recorded in MCP-003 and MCP-004.

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
Replace the `Not assessed` rationale with a citation of the owner instruction ADR-004 already records, fix the stale registry header comment, regenerate the mirrors, and rewrite MCP-003 and MCP-004 to the questions that really remain. No decision belonging to the maintainer is made.

## Requirements
- `REQ-001`: Each of the 10 registry rationales cites the owner instruction recorded in ADR-004 Group 7 (option B, 2026-11-10) instead of `Not assessed`, with no classification change; the registry header comment no longer calls the assessments pending.
- `REQ-002`: `failure_category` stays `safety-integrity` for all 10 entries; whether it should follow ADR-004 Group 2 item 7 is recorded as MCP-003's remaining question (UNK-01, now non-blocking).
- `REQ-003`: MCP-004 states the verified mismatch (the registry is registered under claim type `security-policy` while the governance_01 `security-policy` row names only Accepted security ADRs; the matrix has no owner column) and leaves the choice of resolution to the maintainer (UNK-02, now non-blocking).
- `REQ-004`: The generated mirrors (`registry/manifests/component_mandatoriness.yaml` and the `agent_08_04` table) are regenerated, not hand-edited.
- `REQ-005`: MCP-003 is updated to its remaining open question and MCP-004 to the verified mismatch; both stay open and no approval text is written.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| registry/component_mandatoriness.yaml | modify: rationale of the 10 entries and the header comment that calls MCP-003 and MCP-004 pending assessments | The rationale says `Not assessed` although an owner instruction exists | REQ-001, REQ-002; AC-1 | `component_mandatoriness.yaml:1-8` (header comment) and the 10 `rationale:` lines; `adr_02_01_004...md:98` (Group 7 owner instruction; re-checked in this cycle) | `tests/tools/test_check_component_mandatoriness.py` | Verified |
| registry/manifests/component_mandatoriness.yaml | modify: regenerate the manifest mirror | The manifest copies the rationale text | REQ-004; AC-3 | `manifests/component_mandatoriness.yaml` carries 10 `rationale` lines (checked in Step 3) | N/A: generated, `generate_reference_table.py --check` | Verified |
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | modify: regenerate the generated mandatoriness table | The generated table shows the rationale column | REQ-004; AC-3 | `agent_08_04...md` AUTO-GENERATED `component-mandatoriness-reference` block (checked in Step 3) | N/A: generated, `generate_reference_table.py --check` | Verified |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | modify: rewrite MCP-003 to its remaining question and MCP-004 to the verified mismatch (both stay open) | The entries rest on premises that the files contradict | REQ-002, REQ-003, REQ-005; AC-2, AC-4 | `governance_03...md:154-190` (MCP-003, MCP-004 entries; re-checked in this cycle) | N/A: documentation (`check_issue_inventory_conformance.py`) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | Group 3 items 10, 12, 13, Group 2 item 7, and the Group 7 owner instruction | REQ-001, REQ-002 |
| config/documentation_canonical_sources.toml | Registers the registry under `security-policy` (lines 66-71) | REQ-003 |
| tools/check_canonical_source_registry.py | Validates the canonical-source registry (the Issue named a nonexistent `check_canonical_sources.py`) | REQ-003 |
| tools/check_component_mandatoriness.py | Registry versus `config/agent.toml` consistency | REQ-001 |
| scripts/shared/component_mandatoriness.py | Registry schema and loader (fields and coercions) | REQ-001, REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): No registry rationale says `Not assessed`; each cites the Group 7 owner instruction; no `classification`, `startup_consequence`, or `failure_category` value changed; the header comment states the open items accurately.
- `AC-2` (REQ-003): MCP-004 states the verified claim-type mismatch and names no decision; `config/documentation_canonical_sources.toml` and `governance_01` are unchanged and `check_canonical_source_registry.py` still passes.
- `AC-3` (REQ-004): `generate_reference_table.py --check` exits 0 with the manifest and generated table regenerated.
- `AC-4` (REQ-005): MCP-003 and MCP-004 are updated to the remaining questions with evidence and stay open, and the conformance checkers pass.

## Tests
- `uv run pytest tests/tools/test_check_component_mandatoriness.py tests/shared/test_component_mandatoriness.py tests/tools/test_check_canonical_source_registry.py -q` (REQ-001, REQ-002).
- `uv run python tools/check_component_mandatoriness.py`, `check_canonical_source_registry.py`, `generate_reference_table.py --check`, `check_issue_inventory_conformance.py`, and `tools/run_validation_gates.py` (REQ-001 to REQ-005).

## Documentation Impact
Yes: the registry mirrors, `agent_08_04` (generated), and the governance inventory.

## Assumptions
- Rewording a rationale to cite an owner instruction that ADR-004 already records (Group 7, 2026-11-10) is a factual documentation change, not a classification change and not an approval; if the maintainer disagrees, the Plan is revised.
- Scope narrowing made in this cycle: the parts of the original Plan that needed a maintainer decision (the `failure_category` choice and the placement of the registry's authority) were removed from the rows and moved into the inventory entries as open questions. They were not decided; the `governance_01` row was dropped for that reason.
- The `required` classification of all 10 servers and their `abort_startup` consequence are unchanged by this Plan.
- Path B because the change spans 5 files including a contract registry and its generated mirrors; no Python or schema change, so the baseline is `N/A: no Python target` and the persisted-schema check does not apply.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Should `failure_category` stay `safety-integrity` for the 10 entries or follow ADR-004 Group 2 item 7 (MCP server unavailability listed among availability failures; the item's own classification awaits approval as AAL-019)? | No maintainer statement; the startup outcome is abort either way (item 8) | Recorded as MCP-003's remaining open question; the values stay unchanged in this Plan | False |
| UNK-02 | Where is the registry's authority documented: amend the governance_01 `security-policy` canonical-source kind to name the registry, or change the registry's claim type in `config/documentation_canonical_sources.toml`? | No maintainer statement; `check_canonical_source_registry.py` accepts the current state | Recorded as MCP-004's remaining open question; neither file changes in this Plan | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| registry/component_mandatoriness.yaml | Modify | Medium | 2 | N/A | none (contract data read by startup validation; no new file) |
| registry/manifests/component_mandatoriness.yaml | Modify | Low | 3 | N/A | none (generated) |
| docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | Modify | Low | 8 | N/A | none (generated block) |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Modify | Medium | 19 | N/A | none (documentation) |

## Design
- Rationale text: `Classified required by repository owner instruction 2026-11-10 (ADR-004 Group 7 applicability note, option B); item 10 criteria apply only to a non-mandatory classification` for every entry; the registry header comment is reworded so it no longer calls the assessments pending and points at the two remaining open questions; generated mirrors are regenerated with `generate_reference_table.py --manifests` and `--type mandatoriness`.
- Authority text (UNK-02): not changed. The two possible resolutions (name the registry in the governance_01 `security-policy` row, or change the registry's `claim_type`) are described in MCP-004 for the maintainer; the earlier recommendation of the first option stays a recommendation there.
- Inventory entries: MCP-003 keeps its ID and open status; its title, summary, current description, observed implementation, impact, recommended action, and resolution target are rewritten to the `failure_category` question. MCP-004 keeps its ID and open status; its source and observed implementation are corrected (the matrix has no owner column; the actual mismatch is the claim type). Severity and owner are not changed. The registry header comment keeps citing both IDs.
- Alternatives: a full per-server item-10 assessment (rejected: it would assess non-mandatory criteria for components that are all required); removing MCP-003 and MCP-004 (rejected: the `failure_category` and authority questions are still open and removal would hide them); hand-editing the generated table (rejected: the generator owns it).
- Predictable fallout: the manifest and generated table are rows; the pinned manifest tests are `not affected` by a text-only change; module size and tool inventory do not apply.
- Consumer scan and persisted-schema check: not applicable (no symbol, constant, or schema change).

## Implementation steps
1. **Phase 1: Registry wording**
   - [ ] Reword the 10 rationales and the header comment, leaving every other field unchanged (REQ-001, REQ-002; registry/component_mandatoriness.yaml)
   - [ ] Regenerate the manifest and the generated table (REQ-004; registry/manifests/component_mandatoriness.yaml, docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md)
2. **Phase 2: Inventory and verification**
   - [ ] Rewrite MCP-003 and MCP-004 to the remaining questions (REQ-002, REQ-003, REQ-005; docs/00_governance/governance_03_issue-and-uncertainty-management.md)
   - [ ] Run the tests, checkers, and gates in Validation plan (REQ-001 to REQ-005). No deploy step: no `scripts/` or `config/` change.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| registry/component_mandatoriness.yaml | Unit and consistency | `uv run pytest tests/tools/test_check_component_mandatoriness.py tests/shared/test_component_mandatoriness.py -q`; `uv run python tools/check_component_mandatoriness.py` | Pass; no classification change |
| Generated mirrors | Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Authority wording unchanged | Registry check | `uv run python tools/check_canonical_source_registry.py`; `uv run pytest tests/tools/test_check_canonical_source_registry.py -q` | Pass |
| Inventory | Conformance | `uv run python tools/check_issue_inventory_conformance.py`; `uv run python tools/run_validation_gates.py` | Pass |

## Risks
- **Risk**: The maintainer decides the owner instruction does not satisfy item 13 and wants a real per-server assessment → **Mitigation**: the rewording only cites what ADR-004 records and is reversible text; MCP-003 keeps the open question.
- **Risk**: A reworded rationale reads as an approval → **Mitigation**: the text only cites the existing ADR-004 owner instruction; no approver or date is written.
- **Risk**: The registry is a contract file read by startup validation → **Mitigation**: only string fields change, and the checker and loader tests run.
- **Risk**: Generated mirrors drift if the wording is edited without regeneration → **Mitigation**: regenerate and run `--check` in the same step.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Registry wording | Completed | — | 20261123-134644 |  |
| 2 | Phase 2: Inventory and verification | Completed | — | 20261123-134644 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261123-133747_01_registry_component_mandatoriness.yaml.md | 1 | Procedure | Completed | — | — |
| implementations/20261123-133747_02_registry_manifests_component_mandatoriness.yaml.md | 1 | Procedure | Completed | — | — |
| implementations/20261123-133747_03_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261123-133747_04_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261123-104602_gov003_mandatoriness-assessment-registry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-111105
- **Related target files**: registry/component_mandatoriness.yaml, registry/manifests/component_mandatoriness.yaml, docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (record the result in the registry); ADR-004 Group 7 owner instruction | registry/component_mandatoriness.yaml | Phase 1 | AC-1 | `test_check_component_mandatoriness.py` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (`failure_category` question); ADR-004 Group 2 item 7 | registry/component_mandatoriness.yaml | Phase 1 | AC-1 | `check_component_mandatoriness.py` | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes (owner list); governance_01 Resolution Matrix, canonical-source registry | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 2 | AC-2 | `check_issue_inventory_conformance.py` | Confirmed by repository evidence |
| REQ-004 | Step 3 evidence: generated table and manifest | registry/manifests/component_mandatoriness.yaml | Phase 1 | AC-3 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-004 | Step 3 evidence: generated table and manifest | docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md | Phase 1 | AC-3 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-005 | Issue Acceptance Criteria (MCP-003 and MCP-004 updated) | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 2 | AC-4 | `check_issue_inventory_conformance.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-133747 -->