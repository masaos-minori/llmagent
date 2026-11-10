## Goal
- Record, in ADR-006, ADR-013, ADR-004, the ADR index, `security_01`, and `eventbus_01`, the two decisions the Issue gates the EventBus work on: the EventBus service is kept (planned future integration) with its producer/consumer model stated or explicitly marked not yet defined, and ADR-004 Decision Group 7 and INV-09 are declared inapplicable until a non-required MCP server exists.

## Priority
High

## Scope
- **In-Scope**: Documentation-only decision records and the `security_01` trust-boundary and threat-model addition for the EventBus; the follow-up issues the chosen options require (Phase 4, through `issue-creator`).
- **Out-of-Scope**: Implementing deletion, hardening, or partial-availability tests; changing EventBus runtime behavior; changing `registry/component_mandatoriness.yaml` or `config/agent.toml` (option B changes no classification); the Agent-side coupling removal (`plans/20261110-091327_adrrev002_agent-eventbus-coupling.md`).
- **Dependencies**: The Issue's external dependency (the Group 7 decision) is resolved: option B, stated by the repository owner on 2026-11-10. Blocks `issues/20261109-112952_adrrev010_eventbus-authz-harden.md` and `issues/20261109-113152_adrrev014_eventbus-spec-gaps.md`. Sequencing: the caller model written here must be consistent with plan 002's outcome (Agent-side clients removed); plan 002 rewrites the ADR-013 `Review Triggers` caller assumption and this Plan adds the keep decision and the producer/consumer statement in other ADR-013 text, see Assumptions.
  - **Depends on**: plans/20261110-091327_adrrev002_agent-eventbus-coupling.md | phase 5 | the documented caller model must match the outcome of the Agent-side coupling removal

## Background
- Source: `memo-issue.md` item H-08, re-verified on 2026-11-10.
- Decisions on record (stated by the repository owner, the authority the project's ADRs cite for approval): keep the EventBus service (2026-11-09, quoted in the Issue); Group 7 option B, declare Group 7 inapplicable until a non-required server exists (2026-11-10, in this session). Neither statement names an individual approver; the ADRs' existing convention records "task-level approval decision (repository owner instruction)" without reviewer names (`adr_02_04_013...md:287-290`, `adr_02_01_004...md:338-343`).
- `Confirmed by repository evidence`: `registry/component_mandatoriness.yaml` has 10 entries, every one `classification: required`, so Group 7 (`adr_02_01_004...md:93`, INV-09 at `:226`, matrix row at `:257`) applies to no component today. `agent_08_04` documents the table from the registry in an `AUTO-GENERATED` block.
- `Confirmed by repository evidence` (partly confirms the memo): `docs/91_security/security_01_architecture-and-trust-boundaries.md` mentions the EventBus (`Protected assets` line 61, a full `EventBus Authentication and Authorization` section at line 272, loopback binding at line 129), but the trust-boundary diagram (lines 40-51) and the threat vector list (lines 65-75) do not name it, and the per-API table (lines 77-90) lists MCP servers only.
- `Confirmed by repository evidence`: no ADR states the intended producers and consumers. ADR-006 describes Publisher and Subscriber generically (`adr_02_04_006...md:45-72`); ADR-013 `Review Triggers` line 272 was extended by plan 002's implementation (re-verified 2026-11-10, commit add36ad68: "A first publisher or consumer client of any kind is added to the EventBus"); the older item at line 273 names replacement of the single trusted Agent process as a trigger and remains as written; `eventbus_01` lines 25-28 and 52 state that the Agent neither publishes nor subscribes and that any HTTP client may publish. The Agent-side clients have been removed by plan 002's implementation (commit add36ad68, 2026-11-10; `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md`).
- `Needs confirmation`: the planned producers and consumers of the EventBus and the integration timing (UNK-01); no repository evidence defines them.

## Problem
- No ADR records that the EventBus is intentionally kept without a current user, so reviews cannot tell whether "unused" is intentional, and its producer/consumer model is undefined; Group 7 and INV-09 describe behavior no configuration triggers, so the specification could drift unverified; `security_01` omits the EventBus from the trust-boundary diagram and threat vectors.

## Reason for Change
- The EventBus authorization-hardening and specification-gap Issues are conditional on these decisions; recording them first avoids rework. This is a maintainer decision recorded as documentation, time-sensitive only because it gates that work.

## Implementation Intent
- Record explicit decisions in the ADRs: the EventBus is kept; its producers and consumers are not yet defined (until UNK-01 is answered) and the responsible component is named by the maintainer; Group 7 and INV-09 stay in force as written but are declared inapplicable until a component is classified non-required; no code or configuration changes. Follow the ADR amendment process and the authority model.

## Requirements
- `REQ-001`: Record the EventBus keep decision with its date and the repository-owner source in ADR-006 and ADR-013, state the producer/consumer model as "not yet defined" with the defining component left as a marked pending item, and make `eventbus_01` and the ADR index consistent.
- `REQ-002`: Record in ADR-004 that Group 7 and INV-09 are inapplicable until a non-required server exists (option B), with the approval record, and align `agent_08_04` prose and the ADR index.
- `REQ-003`: Add the EventBus to the `security_01` trust-boundary diagram and threat vectors (the authN/authZ section already exists).
- `REQ-004`: Create the follow-up issues the decisions require through `issue-creator`, and update or close the dependent Issues in this batch where the decisions change them.
- `REQ-005`: Verification: `check_adr_authority.py`, `check_adr_structure.py`, `check_docs_consistency.py --domain eventbus` pass; both decisions carry an approval record.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify: Record the keep decision and the producer/consumer model (or its explicit absence) in the ADR | Record the keep decision and the producer/consumer model (or its explicit absence) in the ADR | REQ-001 / AC-01 | ADR-006 (`Context`, `Decision`) describes Publisher and Subscriber roles generically (lines 45-72) and records no keep decision or defined producers/consumers (checked in Step 3) | `check_adr_structure.py`, `check_adr_authority.py`, `check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Modify: Record the keep decision and state that producers and consumers are not yet defined, naming the responsible component as pending | Record the keep decision and state that producers and consumers are not yet defined, naming the responsible component as pending | REQ-001 / AC-01 | ADR-013 `Review Triggers` (line 272) — extended by plan 002 (commit add36ad68), item 1 now reads "A first publisher or consumer client of any kind is added to the EventBus" (re-verified 2026-11-10) — states no producer/consumer model, and no ADR text states the intended producers and consumers | `check_adr_structure.py`, `check_adr_authority.py`, `check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify: Declare Decision Group 7 and INV-09 inapplicable until a non-required server exists, with the approval record | Declare Decision Group 7 and INV-09 inapplicable until a non-required server exists, with the approval record | REQ-002 / AC-02 | ADR-004 `### Group 7` (line 93), `INV-09` (line 226) and the verification-matrix row (line 257); `registry/component_mandatoriness.yaml` classifies all 10 servers `required` (checked in Step 3) | `check_adr_structure.py`, `check_adr_authority.py`, `check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify: Reflect the Group 7 outcome and the EventBus keep decision in the index | Reflect the Group 7 outcome and the EventBus keep decision in the index | REQ-001, REQ-002 / AC-01, AC-02 | ADR index rows for ADR-004, ADR-006, ADR-013 (lines 48, 50, 56) and the verification matrix (checked in Step 3) | `uv run python tools/generate_adr_authority.py --check` | Verified |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | Modify: Add the EventBus to the trust-boundary diagram and the threat vectors | Add the EventBus to the trust-boundary diagram and the threat vectors | REQ-003 / AC-03 | The trust-boundary diagram (lines 40-51) and the threat vector list (lines 65-75) name no EventBus; EventBus appears only in `Protected assets` (line 61) and `EventBus Authentication and Authorization` (line 272) (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain eventbus`, `check_docs_content_policy.py --strict` | Verified |
| `docs/24_eventbus/eventbus_01_system-overview.md` | Modify: State the keep decision and the producer/consumer status consistently with the ADRs | State the keep decision and the producer/consumer status consistently with the ADRs | REQ-001 / AC-01 | `eventbus_01` lines 25-28 and 52 say the Agent neither publishes nor subscribes and that any HTTP client may publish (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | Modify: Point the non-required reclassification text to the Group 7 outcome (outside the AUTO-GENERATED block) | Point the non-required reclassification text to the Group 7 outcome (outside the AUTO-GENERATED block) | REQ-002 / AC-02 | `agent_08_04` lines 43-49 and 70 describe non-required reclassification; the `AUTO-GENERATED` block (lines 53-68) is generated from `registry/component_mandatoriness.yaml` and is not edited (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/generate_reference_table.py --check` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `registry/component_mandatoriness.yaml` | Shows all 10 servers `required` (basis of option B) | REQ-002 |
| `config/adr_authority.toml` | Authority graph the ADR edits must keep valid | REQ-001, REQ-002 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR Acceptance Evidence Standard cited by the approval records | REQ-005 |
| `rules/coding.md` | "Explicit sign-off gates": the record is a maintainer statement | REQ-005 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Where an unconfirmed item (UNK-01) is registered | REQ-001 |

## Acceptance Criteria
- `AC-01` (REQ-001): ADR-006 and ADR-013 record the keep decision with date and source, and state the producer/consumer model as not yet defined; `eventbus_01` and the ADR index agree.
- `AC-02` (REQ-002): ADR-004 states Group 7 and INV-09 inapplicable until a non-required server exists, with an approval record that cites the repository-owner instruction of 2026-11-10; no registry or config change.
- `AC-03` (REQ-003): the `security_01` diagram and threat vectors name the EventBus.
- `AC-04` (REQ-004): follow-up issues exist (or are recorded as not needed with the reason) and the dependent Issues `adrrev010` and `adrrev014` are updated where the decisions change them.
- `AC-05` (REQ-005): `check_adr_authority.py`, `check_adr_structure.py`, `check_docs_consistency.py --domain eventbus`, `check_docs_content_policy.py --strict`, and `generate_adr_authority.py --check` pass; `check_adr_preservation.py` reports only the intended ADR-004 and ADR-013 changes.

## Tests
- `REQ-001`..`REQ-003`, `REQ-005`: documentation-only; the checkers listed under Validation plan are the tests. No code is changed, so no new automated tests are added (option B adds no partial-availability tests).
- `REQ-004`: `uv run python tools/check_workitem_structure.py --file issues/<new>.md` for each follow-up issue.

## Documentation Impact
- Required: ADR-004 (Group 7 outcome), ADR-006, ADR-013, the ADR index, `security_01`, `eventbus_01`, `agent_08_04` (REQ-001..REQ-003). State intent, the producer/consumer model (or its explicit absence), and failure behavior; docs are English and follow `skills/DESIGN.md` Docs content policy. Register the unconfirmed producers/consumers through `governance_03`.

## Assumptions
- The repository owner's statements of 2026-11-09 and 2026-11-10 are the approval inputs; the implementer records them as such ("repository owner instruction") and does not invent an approver name or a date for any other approval. Falsifiable by the owner.
- Option B leaves ADR-004 Group 7 text as written and adds an applicability statement; it does not amend INV-09. Falsifiable by `check_adr_preservation.py` (a WARNING at most).
- Overlap with other Frozen Plans (`tools/check_plan_target_overlaps.py`, Step 8b): `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` with the two EventBus plans, judged compatible: plan 001 edits `Current State`, plan 002 edits the `Review Triggers` caller assumption, this Plan adds the keep decision, the producer/consumer statement, and an approval note; the `Review Triggers` item is rewritten once, by plan 002, and this Plan only adds the decision text beside it (sequencing: plan 002 first). `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` with the RAG and MCP plans: different sections (Group 7 here; Group 10 and Group 1 there). `docs/10_adr/adr_01_index.md` with the RAG plan: different rows (ADR-010 there; ADR-004, ADR-006, ADR-013 here). `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` with the schema-fingerprint plan: different statements (the version stamp reference there; the keep decision here). `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` with the non-strict plan: different passages (`allowed_root` and `security_profile` there; non-required reclassification here). All judged compatible; any order works except plan 002 before this Plan for ADR-013.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The planned producers and consumers of the EventBus and the timing of the integration | A maintainer statement; nothing in the repository defines them | The ADRs state "not yet defined" with the defining component and timing left as a marked pending item; the maintainer completes it; register through `governance_03` | False |
| UNK-02 | Which follow-up issues the keep decision needs (for example, defining the first producer and consumer) | The maintainer's integration plan | Decided in Phase 4 with the maintainer; if none is needed, record the reason in the Plan's Work Items Created | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | modify | Medium: ADR preservation and authority checks apply | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | modify | Medium: ADR preservation and authority checks apply | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | modify | Medium: ADR preservation and authority checks apply | N/A | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_01_index.md` | modify | Medium: ADR preservation and authority checks apply | N/A | N/A | not applicable (rsynced) |
| `docs/91_security/security_01_architecture-and-trust-boundaries.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_01_system-overview.md` | modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- **Approach**: documentation-only, in dependency order: ADR-006 and ADR-013 (keep decision, producer/consumer status) and `eventbus_01` first (Phase 1), ADR-004 and `agent_08_04` (Phase 2), the ADR index (Phase 3), follow-up issues (Phase 4). Alternatives rejected: Group 7 option A (re-evaluate each server's mandatoriness; changes the registry and needs partial-availability tests) and deferring the decision (the Issue's gated work would stay blocked).
- **Compatibility impact**: none for code or configuration; ADR text changes are reviewed by `check_adr_preservation.py`.
- **Consumer scan**: not applicable (no persisted schema, public API, or shared constant changes).
- **Path B analysis** (Step 5): the change touches no Python or configuration; architecture, dependency graph, historical, and operational analyses are `N/A: documentation-only`. Classified Path B by file count (7 files), not by interface change.
- **Validation quality baseline**: `N/A: no Python target`.
- **Path classification**: Path B (more than 3 files).

## Implementation steps
1. **Phase 1: EventBus keep decision and producer/consumer status**
   - [ ] Update `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_01_system-overview.md`, and add the EventBus to `docs/91_security/security_01_architecture-and-trust-boundaries.md` (REQ-001, REQ-003).
2. **Phase 2: Group 7 outcome**
   - [ ] Update `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` and `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` (REQ-002).
3. **Phase 3: ADR index**
   - [ ] Update `docs/10_adr/adr_01_index.md`; run the ADR checkers (REQ-001, REQ-002, REQ-005).
4. **Phase 4: Follow-up issues**
   - [ ] Create the follow-up issues through `skills/issue-creator/SKILL.md` and update `issues/20261109-112952_adrrev010_eventbus-authz-harden.md` and `issues/20261109-113152_adrrev014_eventbus-spec-gaps.md` where the decisions change them (REQ-004; no `Implementation Target Files` row: these are workflow artifacts under `issues/`).
5. **Phase 5: Verification**
   - [ ] Run the documentation checkers; no deploy step (no `scripts/` or `config/` change) (REQ-005).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ADRs and index | Documentation checks | `check_adr_authority.py`, `check_adr_structure.py`, `generate_adr_authority.py --check`, `check_adr_preservation.py` | Pass; preservation reports only the intended ADR-004 and ADR-013 changes |
| EventBus and security documents | Documentation checks | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain eventbus|agent` | Pass |
| `agent_08_04` generated block | Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0 (block untouched) |
| Follow-up issues | Structure | `uv run python tools/check_workitem_structure.py --file issues/<new>.md` | No findings |

## Risks
- **Risk**: An approval record is written with an invented approver or date → **Mitigation**: only the repository-owner instructions of 2026-11-09 and 2026-11-10 are cited; UNK-01 stays a marked pending item.
- **Risk**: The ADR-004 applicability statement is read as amending INV-09 → **Mitigation**: the statement is worded as applicability only; `check_adr_preservation.py` runs.
- **Risk**: The ADR-013 caller model conflicts with plan 002's `Review Triggers` rewrite → **Mitigation**: plan 002 first (Depends on); this Plan adds text beside, not over, that item.
- **Risk**: Adding the EventBus to the `security_01` diagram duplicates ADR-013 content → **Mitigation**: the addition states the trust boundary and the threat vector and links to ADR-013 (Docs content policy).
- **Risk**: A later non-required server makes the Group 7 inapplicability stale → **Mitigation**: the statement names its own removal trigger (the first non-required classification) and `registry/component_mandatoriness.yaml` remains the checked source.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | EventBus keep decision and producer/consumer status | In Progress | — | — |  |
| 2 | Group 7 outcome | In Progress | — | — |  |
| 3 | ADR index | In Progress | — | — |  |
| 4 | Follow-up issues | Pending | — | — |  |
| 5 | Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261110-135353_01_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-135353_02_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-135353_03_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261110-135353_04_docs_10_adr_adr_01_index.md.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261110-135353_05_docs_91_security_security_01_architecture-and-trust-boundaries.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-135353_06_docs_24_eventbus_eventbus_01_system-overview.md.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261110-135353_07_docs_23_agent_agent_08_04_configuration-mcp-approval-obs.md.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-112739_adrrev006_eventbus-future-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-095718
- **Related target files**: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `docs/10_adr/adr_01_index.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/24_eventbus/eventbus_01_system-overview.md`, `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / repository evidence | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 1 | AC-01 | `check_adr_structure.py`, `check_adr_authority.py`, `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | 1 | AC-01 | `check_adr_structure.py`, `check_adr_authority.py`, `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | 2 | AC-02 | `check_adr_structure.py`, `check_adr_authority.py`, `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `docs/10_adr/adr_01_index.md` | 3 | AC-01 | `uv run python tools/generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `docs/10_adr/adr_01_index.md` | 3 | AC-02 | `uv run python tools/generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-003 | Required Changes / repository evidence | `docs/91_security/security_01_architecture-and-trust-boundaries.md` | 1 | AC-03 | `uv run python tools/check_docs_consistency.py --domain eventbus`, `check_docs_content_policy.py --strict` | Confirmed by repository evidence |
| REQ-001 | Required Changes / repository evidence | `docs/24_eventbus/eventbus_01_system-overview.md` | 1 | AC-01 | `uv run python tools/check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-002 | Required Changes / repository evidence | `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md` | 2 | AC-02 | `uv run python tools/check_docs_consistency.py --domain agent`, `uv run python tools/generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-004 | Required Changes / Acceptance Criteria: follow-up issues | N/A: workflow artifacts under `issues/`, no modification target | 4 | AC-04 | `check_workitem_structure.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261110-135353 -->