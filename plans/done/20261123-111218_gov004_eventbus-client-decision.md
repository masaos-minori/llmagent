## Goal
- Retire the two unused agent-side EventBus client modules as the maintainer decided (2026-11-23: UNK-01 = retire), remove them from the tests, manifest, generated reference, and the documents that present them, and close AGENT-001 in the governance inventory. The EventBus producer/consumer model (NC-003) is left open as the maintainer decided (UNK-02 = leave open).

## Priority
Medium

## Scope
- **In-Scope**: removing `scripts/agent/eventbus_subscriber.py`, `scripts/agent/eventbus_topic_admin_client.py`, and their two test files; the matching documentation (`agent_02`, `governance_05`), generated-reference, manifest, and inventory (AGENT-001) updates.
- **Out-of-Scope**: implementing the EventBus integration; any change to the EventBus service itself; the producer/consumer decision (NC-003 and ADR-006 item 14 stay as they are, by the maintainer's decision UNK-02 = leave open); ADR-013 (its Review Trigger 1 stays the trigger to revisit the model); writing an approver, a date, or an approval sentence; the ledger entries AAL-006 to AAL-010 and AAL-029 (gov005).
- **Dependencies**: None open. Both maintainer decisions are stated (see Background); the retirement needs an Agent restart after deploy (a user decision).

## Background
Source Issue: `gov004`, from governance Known Issue AGENT-001 (Low) and Needs Confirmation NC-003 (Medium). Verified in Step 2:
- A scan of the whole repository (excluding archived work) finds the two modules referenced only by their own two test files, `docs/23_agent/agent_02_runtime-architecture.md` (section `EventBus Client Modules`), the generated `docs/23_agent/agent_13_reference-api-generated.md`, `registry/manifests/agent_api.yaml`, and the governance inventory; no runtime component imports them. Both modules are small (170 and 101 lines).
- Context the Issue did not state: ADR-006 Decision item 14 records a repository owner instruction of 2026-11-09 that the EventBus service is kept for a planned future integration, that it currently has no defined producers or consumers, and that this absence is intentional; ADR-013 `### Caller model status` repeats it. So the keep decision exists for the service, while the status of the client modules as retained-for-that-integration versus retire-candidates is not recorded (AGENT-001), and the producer/consumer model is open (NC-003).
- **Maintainer decisions (stated 2026-11-23, recorded here as given, not as an approval record)**: UNK-01 = retire the two modules; UNK-02 = leave NC-003 open (the model stays undefined until the integration is planned; ADR-013 Review Trigger 1 stays the trigger). Precedent: the sibling unused publish client `eventbus_client.py` was removed on 2026-11-10 (`add36ad68`) the day after the owner instruction to keep the EventBus service. The removed code stays recoverable from history (`60aad9290`, `0effc5b08`).
- Re-verified in the 2026-11-23 follow-up pass: `agent_02` (lines 155-157) already states that no runtime component of the Agent process imports the modules and only their unit tests do, so the earlier claim that it omits this was wrong. `AGENT-001` and `NC-003` already record the keep-or-retire and producer/consumer questions as pending maintainer decisions, and `NC-003` and ADR-006 item 14 say the implementer does not write the answer. No document edit is therefore available that does not depend on a maintainer statement, and the Plan stays Draft with both Unknowns blocking.

## Problem
Two modules read as a supported API while nothing in the runtime uses them, with no recorded decision, and the model they would serve is undefined.

## Reason for Change
Unused code presented as current API misleads readers and inflates the manifest; the decision is the maintainer's.

## Implementation Intent
Apply whichever of the two outcomes the maintainer chooses: retention (documents say the modules are retained for the planned integration and have no runtime caller) or retirement (modules, tests, manifest and generated entries removed through this Plan's steps), plus the producer/consumer decision, then close the inventory entries.

## Requirements
- `REQ-001`: The maintainer's decision to retire the two modules (UNK-01) is applied and the documents that present them (`agent_02`, `governance_05`) match it.
- `REQ-002`: The two modules, their two test files, and their manifest and generated reference entries are removed, and no importer remains.
- `REQ-003`: Not applicable by the maintainer's decision UNK-02 (leave open): ADR-006 item 14 and NC-003 are unchanged.
- `REQ-004`: AGENT-001 is removed from the inventory with the retirement as evidence; NC-003 stays; no approval text is written.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/agent/test_eventbus_subscriber.py | delete: remove the test file | Its subject is retired; it must go before the module so no import breaks | REQ-002; AC-2 | the only importer of the module (re-checked in this cycle: `rg` over `scripts/ tools/ deploy/ config/ .github/ tests/`) | itself | Verified |
| tests/agent/test_eventbus_topic_admin_client.py | delete: remove the test file | Its subject is retired; it must go before the module | REQ-002; AC-2 | the only importer of the module (re-checked in this cycle) | itself | Verified |
| scripts/agent/eventbus_subscriber.py | delete: remove the module | No runtime importer; retired by the maintainer's decision UNK-01 | REQ-001, REQ-002; AC-2 | `rg` import scan finds only its own test file and generated docs (re-checked in this cycle) | `tests/agent/test_eventbus_subscriber.py` | Verified |
| scripts/agent/eventbus_topic_admin_client.py | delete: remove the module | No runtime importer; retired by the maintainer's decision UNK-01 | REQ-001, REQ-002; AC-2 | `rg` import scan finds only its own test file and generated docs (re-checked in this cycle) | `tests/agent/test_eventbus_topic_admin_client.py` | Verified |
| registry/manifests/agent_api.yaml | modify: regenerate the manifest | Lists the two modules' public classes | REQ-002; AC-3 | `agent_api.yaml:343-369` entries for both modules (re-checked) | N/A: generated, `generate_reference_table.py --check` | Verified |
| docs/23_agent/agent_13_reference-api-generated.md | modify: regenerate the generated reference | Lists the two modules' classes (lines 69-76) | REQ-002; AC-3 | generated block (re-checked) | N/A: generated, `generate_reference_table.py --check` | Verified |
| docs/23_agent/agent_02_runtime-architecture.md | modify: remove the `EventBus Client Modules` section | The section presents the retired modules | REQ-001; AC-1 | `agent_02...md:155-157` (re-checked) | N/A: documentation | Verified |
| docs/00_governance/governance_05_change-impact-and-dependency-graphs.md | modify: drop the sentence naming the retired client modules in the `Not represented as an edge` list | The sentence describes modules that no longer exist | REQ-001; AC-1 | `governance_05...md:140-144` (found in this cycle; the Plan's first scan missed it) | N/A: documentation | Verified |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | modify: remove AGENT-001 | Closed by the retirement | REQ-004; AC-4 | `governance_03...md` entry AGENT-001 (`#### AGENT-001`); the size ceiling in `tools/check_docs_structure.py` only needs to stay an upper bound | N/A: documentation (`check_issue_inventory_conformance.py`) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | `### Caller model status` repeats the unresolved model | REQ-003 |
| tools/check_issue_inventory_conformance.py | Inventory entry shape after removal | REQ-004 |
| tools/generate_reference_table.py | Regenerates the manifest and generated reference | REQ-002 |
| tools/check_needs_confirmation_inventory.py | Needs Confirmation marker and inventory sync for NC-003 | REQ-003, REQ-004 |

## Acceptance Criteria
- `AC-1` (REQ-001): No document presents the two modules as existing code (`agent_02`, `governance_05`, generated reference).
- `AC-2` (REQ-002): No file in `scripts/`, `tests/`, or `tools/` references either module and the full test suite passes.
- `AC-3` (REQ-002): `generate_reference_table.py --check` exits 0 with the manifest and generated reference regenerated.
- `AC-4` (REQ-004): AGENT-001 is removed, NC-003 and ADR-006 item 14 are unchanged, and the conformance and Needs Confirmation checkers pass.

## Tests
- `rg "eventbus_subscriber|eventbus_topic_admin_client" scripts tests tools` lists nothing; the full suite (`uv run pytest tests/ -n logical ...`) passes (REQ-002).
- `generate_reference_table.py --check`, `check_issue_inventory_conformance.py`, `check_needs_confirmation_inventory.py`, `check_adr_structure.py`, `check_docs_structure.py`, and `tools/run_validation_gates.py` (REQ-001, REQ-002, REQ-004).

## Documentation Impact
Yes: `agent_02`, `governance_05`, the governance inventory, and the generated reference and manifest.

## Assumptions
- Retirement of code is the maintainer's decision, stated 2026-11-23 (UNK-01 = retire); this Plan executes it. NC-003 stays open by the maintainer's decision (UNK-02).
- The EventBus service itself stays (ADR-006 item 14 owner instruction of 2026-11-09).
- Path B because the retire path changes more than 3 files and removes public classes from the API manifest; there is no schema or persisted-state change, so the persisted-schema check does not apply.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Are the two client modules retained for the planned EventBus integration or retired? | Resolved: the maintainer decided to retire them (2026-11-23) | Applied in this Plan's rows | False |
| UNK-02 | Which component defines EventBus producers and consumers, and when is the integration planned? | Resolved as a scope decision: the maintainer decided to leave NC-003 open (2026-11-23); the model stays undefined until the integration is planned | No change to ADR-006 item 14 or NC-003 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/agent/test_eventbus_subscriber.py | Delete | Low | 1 | N/A | none (tests) |
| tests/agent/test_eventbus_topic_admin_client.py | Delete | Low | 1 | N/A | none (tests) |
| scripts/agent/eventbus_subscriber.py | Delete | Low | 1 | N/A | requires service restart (agent code removed) |
| scripts/agent/eventbus_topic_admin_client.py | Delete | Low | 1 | N/A | requires service restart (agent code removed) |
| registry/manifests/agent_api.yaml | Modify | Low | 25 | N/A | none (generated) |
| docs/23_agent/agent_13_reference-api-generated.md | Modify | Low | 24 | N/A | none (generated) |
| docs/23_agent/agent_02_runtime-architecture.md | Modify | Low | 6 | N/A | none (documentation) |
| docs/00_governance/governance_05_change-impact-and-dependency-graphs.md | Modify | Low | N/A | N/A | none (documentation) |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Modify | Medium | 19 | N/A | none (documentation) |

## Design
- Retirement (maintainer decision UNK-01): delete the two tests first, then the two modules, in one change (a module removed while its test remains breaks collection); regenerate the manifest and generated reference (`generate_reference_table.py --manifests --type agent` and `--type agent`); the scan after deletion proves no importer remains.
- Documents: remove the `EventBus Client Modules` section of `agent_02` and the sentence of `governance_05` that names the modules (keep the statement that no runtime component calls the Event Bus, which stays true); AGENT-001 is removed from the inventory; NC-003 and ADR-006 item 14 stay unchanged (maintainer decision UNK-02).
- Alternatives: retaining the modules with an `agent_02` sentence (rejected by the maintainer's decision); recording a deferral text in ADR-006 (not chosen; leaving NC-003 open is the decision).
- Consumer scan (Step 3): the scan targets the class and module names over `scripts/ tests/ tools/ deploy/ config/ .github/ docs/ registry/`; it finds only the files in the table (the first scan missed `governance_05`, added here). Predictable fallout: the manifest and generated reference are rows; module size and tool inventory do not apply; `tools/check_docs_structure.py` keeps a size ceiling for `governance_03` that stays an upper bound after the entry is removed; the citation-count pin in `tests/test_run_cited_adr_tests.py` counts the ADR index matrix, not agent API symbols.

## Implementation steps
1. **Phase 1: Retirement**
   - [ ] Remove the two tests first, then the two modules (REQ-001, REQ-002; tests/agent/test_eventbus_subscriber.py, tests/agent/test_eventbus_topic_admin_client.py, scripts/agent/eventbus_subscriber.py, scripts/agent/eventbus_topic_admin_client.py)
   - [ ] Regenerate the manifest and generated reference (REQ-002; registry/manifests/agent_api.yaml, docs/23_agent/agent_13_reference-api-generated.md)
2. **Phase 2: Documents**
   - [ ] Remove the retired modules from `agent_02` and `governance_05` (REQ-001; docs/23_agent/agent_02_runtime-architecture.md, docs/00_governance/governance_05_change-impact-and-dependency-graphs.md)
3. **Phase 3: Inventory and verification**
   - [ ] Remove AGENT-001 (REQ-004; docs/00_governance/governance_03_issue-and-uncertainty-management.md)
   - [ ] Run the checkers, the full suite, and the gates; hand off to `skills/deploy/SKILL.md` after commit and push (agent code removed): a user decision.

### Release units
**Unit**: eventbus-client-retirement | **Phases**: 1 | **Reason**: removing a module while its test or the manifest still names it breaks the suite and the drift check until all removals land together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/ and tests/ | Import scan and full suite | `rg "eventbus_subscriber|eventbus_topic_admin_client" scripts tests tools`; `uv run python tools/run_validation_gates.py --full` | No match; suite passes |
| Generated reference and manifest | Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Documents and inventory | Checkers | `check_issue_inventory_conformance.py`, `check_needs_confirmation_inventory.py`, `check_docs_structure.py`, `tools/run_validation_gates.py` | No findings |

## Risks
- **Risk**: Retiring the modules removes code intended for the future integration → **Mitigation**: the maintainer decided it; the code stays recoverable from history (`60aad9290`, `0effc5b08`).
- **Risk**: Removing public classes breaks the manifest contract check → **Mitigation**: regenerate in the same step and run `--check`.
- **Risk**: Agent code is removed, so the deployed Agent keeps the old modules until the next deploy → **Mitigation**: the modules have no runtime caller, so a late deploy changes nothing at runtime; the deploy hand-off is the user's decision.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Retirement | In Progress | — | — |  |
| 2 | Phase 2: Documents | In Progress | — | — |  |
| 3 | Phase 3: Inventory and verification | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261123-153647_03_scripts_agent_eventbus_subscriber.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-153647_04_scripts_agent_eventbus_topic_admin_client.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-153647_05_registry_manifests_agent_api.yaml.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-153647_06_docs_23_agent_agent_13_reference-api-generated.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261123-153647_07_docs_23_agent_agent_02_runtime-architecture.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-153647_08_docs_00_governance_governance_05_change-impact-and-dependency-graphs.md.md | 2 | Procedure | Pending | — | — |
| implementations/20261123-153647_09_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261123-104603_gov004_eventbus-client-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-111218
- **Related target files**: tests/agent/test_eventbus_subscriber.py, tests/agent/test_eventbus_topic_admin_client.py, scripts/agent/eventbus_subscriber.py, scripts/agent/eventbus_topic_admin_client.py, registry/manifests/agent_api.yaml, docs/23_agent/agent_13_reference-api-generated.md, docs/23_agent/agent_02_runtime-architecture.md, docs/00_governance/governance_05_change-impact-and-dependency-graphs.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-002 | Issue Required Changes (retire); import scan | tests/agent/test_eventbus_subscriber.py | Phase 1 | AC-2 | full suite | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (retire); import scan | tests/agent/test_eventbus_topic_admin_client.py | Phase 1 | AC-2 | full suite | Confirmed by repository evidence |
| REQ-001 | Maintainer decision UNK-01; import scan | scripts/agent/eventbus_subscriber.py | Phase 1 | AC-2 | `rg` import scan, full suite | Confirmed by repository evidence |
| REQ-002 | Import scan | scripts/agent/eventbus_subscriber.py | Phase 1 | AC-2 | `rg` import scan, full suite | Confirmed by repository evidence |
| REQ-001 | Maintainer decision UNK-01; import scan | scripts/agent/eventbus_topic_admin_client.py | Phase 1 | AC-2 | `rg` import scan, full suite | Confirmed by repository evidence |
| REQ-002 | Import scan | scripts/agent/eventbus_topic_admin_client.py | Phase 1 | AC-2 | `rg` import scan, full suite | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (manifest and generated entries) | registry/manifests/agent_api.yaml | Phase 1 | AC-3 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-002 | Issue Required Changes (manifest and generated entries) | docs/23_agent/agent_13_reference-api-generated.md | Phase 1 | AC-3 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-001 | `agent_02` section | docs/23_agent/agent_02_runtime-architecture.md | Phase 2 | AC-1 | gates | Confirmed by repository evidence |
| REQ-001 | `governance_05` dependency graph sentence | docs/00_governance/governance_05_change-impact-and-dependency-graphs.md | Phase 2 | AC-1 | gates | Confirmed by repository evidence |
| REQ-004 | Issue Acceptance Criteria (AGENT-001 removed) | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 3 | AC-4 | `check_issue_inventory_conformance.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-153647 -->