## Goal
- Resolve the unrecorded keep-or-retire status of the two unused agent-side EventBus client modules, and the undefined EventBus producer/consumer model, by applying the maintainer's decisions to the documents (and, if the modules are retired, to the code, tests, manifest, and generated docs), then closing AGENT-001 and NC-003 in the governance inventory.

## Priority
Medium

## Scope
- **In-Scope**: applying the maintainer's keep-or-retire decision for `scripts/agent/eventbus_subscriber.py` and `scripts/agent/eventbus_topic_admin_client.py`; recording the maintainer's producer/consumer decision in ADR-006 item 14; the matching documentation, generated-reference, manifest, and inventory updates.
- **Out-of-Scope**: implementing the EventBus integration; any change to the EventBus service itself; writing an approver, a date, or an approval sentence; changes to ADR-013 beyond a decision the maintainer states; the ledger entries AAL-006 to AAL-010 and AAL-029 (the ADR Approval Ledger issue, gov005).
- **Dependencies**: None open. The maintainer decisions UNK-01 and UNK-02 gate this Plan.

## Background
Source Issue: `gov004`, from governance Known Issue AGENT-001 (Low) and Needs Confirmation NC-003 (Medium). Verified in Step 2:
- A scan of the whole repository (excluding archived work) finds the two modules referenced only by their own two test files, `docs/23_agent/agent_02_runtime-architecture.md` (section `EventBus Client Modules`), the generated `docs/23_agent/agent_13_reference-api-generated.md`, `registry/manifests/agent_api.yaml`, and the governance inventory; no runtime component imports them. Both modules are small (170 and 101 lines).
- Context the Issue did not state: ADR-006 Decision item 14 records a repository owner instruction of 2026-11-09 that the EventBus service is kept for a planned future integration, that it currently has no defined producers or consumers, and that this absence is intentional; ADR-013 `### Caller model status` repeats it. So the keep decision exists for the service, while the status of the client modules as retained-for-that-integration versus retire-candidates is not recorded (AGENT-001), and the producer/consumer model is open (NC-003).
- `agent_02` describes the modules as client-side libraries for the Event Bus HTTP API without saying they have no runtime caller.

## Problem
Two modules read as a supported API while nothing in the runtime uses them, with no recorded decision, and the model they would serve is undefined.

## Reason for Change
Unused code presented as current API misleads readers and inflates the manifest; the decision is the maintainer's.

## Implementation Intent
Apply whichever of the two outcomes the maintainer chooses: retention (documents say the modules are retained for the planned integration and have no runtime caller) or retirement (modules, tests, manifest and generated entries removed through this Plan's steps), plus the producer/consumer decision, then close the inventory entries.

## Requirements
- `REQ-001`: The maintainer's keep-or-retire decision for the two modules is recorded (UNK-01) and the documents match it.
- `REQ-002`: If retired, the two modules, their two test files, and their manifest and generated reference entries are removed, and no importer remains.
- `REQ-003`: The maintainer's producer/consumer decision (defining component and timing) is recorded in ADR-006 item 14 (UNK-02), without the implementer writing it.
- `REQ-004`: AGENT-001 and NC-003 are removed from the inventory with evidence once their decisions are recorded; no approval text is written.

## Implementation Target Files
**Freeze status**: Draft

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| docs/23_agent/agent_02_runtime-architecture.md | modify: state the retained or retired status of the client modules | The section presents them as current client libraries with no runtime caller note | REQ-001; AC-1 | `agent_02...md:155-157` (checked in Step 2) | N/A: documentation | Needs confirmation |
| scripts/agent/eventbus_subscriber.py | delete: remove the module (retire path only) | No runtime importer | REQ-002; AC-2 | `rg` import scan (checked in Step 2) | `tests/agent/test_eventbus_subscriber.py` | Needs confirmation |
| scripts/agent/eventbus_topic_admin_client.py | delete: remove the module (retire path only) | No runtime importer | REQ-002; AC-2 | `rg` import scan (checked in Step 2) | `tests/agent/test_eventbus_topic_admin_client.py` | Needs confirmation |
| tests/agent/test_eventbus_subscriber.py | delete: remove the test file (retire path only) | Its subject is removed | REQ-002; AC-2 | the only importer of the module (checked in Step 2) | itself | Needs confirmation |
| tests/agent/test_eventbus_topic_admin_client.py | delete: remove the test file (retire path only) | Its subject is removed | REQ-002; AC-2 | the only importer of the module (checked in Step 2) | itself | Needs confirmation |
| registry/manifests/agent_api.yaml | modify: regenerate the manifest (retire path only) | Lists the two modules' public classes | REQ-002; AC-3 | `agent_api.yaml:343-369` (checked in Step 2) | N/A: generated, `generate_reference_table.py --check` | Needs confirmation |
| docs/23_agent/agent_13_reference-api-generated.md | modify: regenerate the generated reference (retire path only) | Lists the modules | REQ-002; AC-3 | generated block (checked in Step 2) | N/A: generated, `generate_reference_table.py --check` | Needs confirmation |
| docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | modify: record the maintainer's producer/consumer decision in item 14 | NC-003 marks the model as not yet defined | REQ-003; AC-4 | `adr_02_04_006...md:86` (checked in Step 2) | N/A: documentation | Needs confirmation |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | modify: remove AGENT-001 and NC-003 | Closed by the recorded decisions | REQ-004; AC-5 | `governance_03...md` entries AGENT-001 and NC-003 (checked in Step 2) | N/A: documentation | Needs confirmation |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md | `### Caller model status` repeats the unresolved model | REQ-003 |
| tools/check_issue_inventory_conformance.py | Inventory entry shape after removal | REQ-004 |
| tools/generate_reference_table.py | Regenerates the manifest and generated reference | REQ-002 |
| tools/check_needs_confirmation_inventory.py | Needs Confirmation marker and inventory sync for NC-003 | REQ-003, REQ-004 |

## Acceptance Criteria
- `AC-1` (REQ-001): The documents state the modules' decided status accurately.
- `AC-2` (REQ-002): On the retire path, no file in `scripts/` or `tests/` references either module and the full test suite passes.
- `AC-3` (REQ-002): On the retire path, `generate_reference_table.py --check` exits 0 with the manifest and generated reference regenerated.
- `AC-4` (REQ-003): ADR-006 item 14 records the maintainer's decision and the inline NC-003 marker is gone.
- `AC-5` (REQ-004): AGENT-001 and NC-003 are removed and the conformance and Needs Confirmation checkers pass.

## Tests
- Retire path: `rg "eventbus_subscriber|eventbus_topic_admin_client" scripts tests tools` lists nothing; the full suite (`uv run pytest tests/ -n logical ...`) passes (REQ-002).
- All paths: `generate_reference_table.py --check`, `check_issue_inventory_conformance.py`, `check_needs_confirmation_inventory.py`, `check_adr_structure.py`, and `tools/run_validation_gates.py` (REQ-001 to REQ-004).

## Documentation Impact
Yes: `agent_02`, ADR-006, and the governance inventory; the generated reference and manifest on the retire path.

## Assumptions
- Retirement of code is a maintainer decision that this Plan only executes after it is stated; the default for an unanswered question is no code change.
- The EventBus service itself stays (ADR-006 item 14 owner instruction of 2026-11-09).
- Path B because the retire path changes more than 3 files and removes public classes from the API manifest; there is no schema or persisted-state change, so the persisted-schema check does not apply.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Are the two client modules retained for the planned EventBus integration or retired? | No maintainer statement; decides whether the rows for the modules, tests, manifest, and generated reference are changed or only the documents | The maintainer answers; the Plan is then frozen with the matching rows | True |
| UNK-02 | Which component defines EventBus producers and consumers, and when is the integration planned? | No maintainer statement; decides the text of ADR-006 item 14 | The maintainer states it; the implementer does not write either | True |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| docs/23_agent/agent_02_runtime-architecture.md | Modify | Low | 6 | N/A | none (documentation) |
| scripts/agent/eventbus_subscriber.py | Delete | Low | 1 | N/A | requires service restart (agent code, retire path only) |
| scripts/agent/eventbus_topic_admin_client.py | Delete | Low | 1 | N/A | requires service restart (agent code, retire path only) |
| tests/agent/test_eventbus_subscriber.py | Delete | Low | 1 | N/A | none (tests) |
| tests/agent/test_eventbus_topic_admin_client.py | Delete | Low | 1 | N/A | none (tests) |
| registry/manifests/agent_api.yaml | Modify | Low | 25 | N/A | none (generated) |
| docs/23_agent/agent_13_reference-api-generated.md | Modify | Low | 24 | N/A | none (generated) |
| docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | Modify | Medium | 17 | N/A | none (documentation) |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Modify | Medium | 19 | N/A | none (documentation) |

## Design
- Retain path: `agent_02` gains one factual sentence that the modules have no runtime caller and are kept for the planned integration; no code change; the inventory entry closes with the maintainer's decision.
- Retire path: delete the two modules and their tests in one change, regenerate the manifest and generated reference (`generate_reference_table.py --manifests` and `--type agent`), and remove the `agent_02` section; the scan after deletion proves no importer remains.
- ADR-006 item 14: the implementer inserts only the maintainer's stated text; nothing is drafted as a decision.
- Alternatives: retiring by default (rejected: loses the client libraries the owner instruction of 2026-11-09 may intend to use); documenting only (the default if the maintainer retains).
- Consumer scan (Step 3): the retire path removes public classes, so the scan targets the class and module names; the repository scan found only the files above. Predictable fallout: the manifest and generated reference are rows; module size, pinned counts, and tool inventory do not apply (the citation-count pin in `tests/test_run_cited_adr_tests.py` counts the ADR index matrix, not agent API symbols).

## Implementation steps
1. **Phase 1: Documents (both paths)**
   - [ ] Apply the maintainer's UNK-01 answer to `agent_02` (REQ-001; docs/23_agent/agent_02_runtime-architecture.md)
   - [ ] Record the maintainer's UNK-02 text (REQ-003; docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md)
2. **Phase 2: Retirement (only if UNK-01 says retire)**
   - [ ] Remove the two tests first, then the two modules (REQ-002; tests/agent/test_eventbus_subscriber.py, tests/agent/test_eventbus_topic_admin_client.py, scripts/agent/eventbus_subscriber.py, scripts/agent/eventbus_topic_admin_client.py)
   - [ ] Regenerate the manifest and generated reference (REQ-002; registry/manifests/agent_api.yaml, docs/23_agent/agent_13_reference-api-generated.md)
3. **Phase 3: Inventory and verification**
   - [ ] Remove AGENT-001 and NC-003 (REQ-004; docs/00_governance/governance_03_issue-and-uncertainty-management.md)
   - [ ] Run the checkers, the full suite on the retire path, and the gates. Retire path: deploy hand-off to `skills/deploy/SKILL.md` after commit and push, a user decision (agent code removed).

### Release units
**Unit**: eventbus-client-retirement | **Phases**: 2 | **Reason**: removing a module while its test or the manifest still names it breaks the suite and the drift check until all removals land together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/ and tests/ (retire path) | Import scan and full suite | `rg "eventbus_subscriber|eventbus_topic_admin_client" scripts tests tools`; `uv run python tools/run_validation_gates.py --full` | No match; suite passes |
| Generated reference and manifest (retire path) | Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Documents and inventory (all paths) | Checkers | `check_adr_structure.py`, `check_issue_inventory_conformance.py`, `check_needs_confirmation_inventory.py`, `tools/run_validation_gates.py` | No findings |

## Risks
- **Risk**: Retiring the modules removes code the owner instruction of 2026-11-09 intended for the integration → **Mitigation**: UNK-01 is blocking; no code is removed before the maintainer answers.
- **Risk**: Removing public classes breaks the manifest contract check → **Mitigation**: regenerate in the same step and run `--check`.
- **Risk**: The ADR-006 text is written by the implementer → **Mitigation**: only the maintainer's stated text is inserted (UNK-02 is blocking).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Documents (both paths) | Pending | — | — | |
| 2 | Retirement (only if retire) | Pending | — | — | |
| 3 | Inventory and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01 (keep or retire the client modules) is unresolved | — | — |
| 1 | UNK-02 (producer/consumer model decision) is unresolved | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261123-104603_gov004_eventbus-client-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-111218
- **Related target files**: docs/23_agent/agent_02_runtime-architecture.md, scripts/agent/eventbus_subscriber.py, scripts/agent/eventbus_topic_admin_client.py, tests/agent/test_eventbus_subscriber.py, tests/agent/test_eventbus_topic_admin_client.py, registry/manifests/agent_api.yaml, docs/23_agent/agent_13_reference-api-generated.md, docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (record the decision); `agent_02` section | docs/23_agent/agent_02_runtime-architecture.md | Phase 1 | AC-1 | `check_adr_structure.py`, gates | Needs confirmation |
| REQ-002 | Issue Required Changes (if retired); import scan | scripts/agent/eventbus_subscriber.py | Phase 2 | AC-2 | `rg` import scan, full suite | Needs confirmation |
| REQ-002 | Issue Required Changes (if retired); import scan | scripts/agent/eventbus_topic_admin_client.py | Phase 2 | AC-2 | `rg` import scan, full suite | Needs confirmation |
| REQ-002 | Issue Required Changes (if retired); import scan | tests/agent/test_eventbus_subscriber.py | Phase 2 | AC-2 | full suite | Needs confirmation |
| REQ-002 | Issue Required Changes (if retired); import scan | tests/agent/test_eventbus_topic_admin_client.py | Phase 2 | AC-2 | full suite | Needs confirmation |
| REQ-002 | Issue Required Changes (manifest and generated entries) | registry/manifests/agent_api.yaml | Phase 2 | AC-3 | `generate_reference_table.py --check` | Needs confirmation |
| REQ-002 | Issue Required Changes (manifest and generated entries) | docs/23_agent/agent_13_reference-api-generated.md | Phase 2 | AC-3 | `generate_reference_table.py --check` | Needs confirmation |
| REQ-003 | Issue Required Changes (producer/consumer decision); ADR-006 item 14 | docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md | Phase 1 | AC-4 | `check_needs_confirmation_inventory.py` | Needs confirmation |
| REQ-004 | Issue Acceptance Criteria (AGENT-001 and NC-003 removed) | docs/00_governance/governance_03_issue-and-uncertainty-management.md | Phase 3 | AC-5 | `check_issue_inventory_conformance.py` | Needs confirmation |
