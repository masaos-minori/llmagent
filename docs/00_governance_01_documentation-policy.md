---
title: "Documentation Policy"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Documentation Policy

## Purpose

This document consolidates policy-level rules for the LLM agent design documentation set. It covers document classification, canonical source precedence, conflict resolution, ADR conventions, and dependency graph management.

## Current-Specification-Only Policy

The active design documentation set describes the current system only: what is
required to understand, implement, configure, operate, and validate the system as it
exists today.

The active documentation set does not retain:

- Deprecated specifications
- Superseded specifications
- Rejected architectural decisions
- Migration history
- Change history
- Archived issues
- Resolved Needs Confirmation entries
- Historical document structures
- Replacement mappings for removed items
- Historical compatibility records

Before historical content of this kind is removed from a document, any requirement,
constraint, invariant, rationale, or verification rule it contains that still applies
to the current system must be transferred into the appropriate current canonical
document. Removal of the historical content itself is a separate, later change and is
not performed by adding or updating this policy.

## Document Classification

Documents in the design documentation set are classified into seven classes:

- **Governance** — Cross-cutting rules, policies, and standards that apply across areas
- **Guide** — Navigation documents that provide an overview of an area's documentation structure
- **Specification** — Detailed technical specifications describing how components work
- **Reference** — API references, command references, and configuration reference materials
- **Operations** — Operational guidance including monitoring, troubleshooting, and diagnostics
- **Note** — Working notes, investigation results, and temporary documentation
- **Known Issues** — Documents tracking known inconsistencies between documentation and implementation

## Canonical Source Precedence

When conflicts arise between documentation and code/config, the following precedence applies:

| Rank | Source Type | Example | Notes |
|------|-------------|---------|-------|
| 1 | Code | `scripts/eventbus/publisher.py` | Authoritative for runtime behavior |
| 2 | Tests | `tests/eventbus/test_publisher.py` | Authoritative for expected behavior |
| 3 | ADRs | `docs/adr/ADR-001-workflow-engine-mandatory.md` | Authoritative for architectural decisions |
| 4 | Specifications | `docs/specification.md` | Authoritative for functional requirements |
| 5 | Configuration | `config/system.toml` | Authoritative for operational parameters |
| 6 | Documentation | `docs/architecture.md` | Authoritative for conceptual understanding |

### Decision Target Canonical Source Matrix

Defines which artifact is authoritative for each decision target, so Code is not
treated as the top canonical source for every kind of decision.

| Decision Target | Canonical | Auxiliary Evidence | Discrepancy Registration Target |
|-----------------|-----------|--------------------|----------------------------------|
| Adopted Architecture Decision | `docs/adr/ADR-{NNN}-*.md` | Code, Test, Operational Observation | Known Issues |
| Requirements, External Behavior | `docs/{area}_*_specification.md` | Acceptance Test | Known Issues |
| Current Runtime Behavior | Source under `scripts/`, `implementations/` | Runtime Log, Test | Known Issues |
| Expected Behavior | `tests/` + Specification | ADR | Known Issues |
| Effective Value in Production | Deployed Configuration (`config/*.toml`) | Startup Diagnostics | Configuration Drift |
| DB Schema | Schema Generator or official DDL | Schema Test | Known Issues |
| API Contract | API Schema or official Contract | Integration Test | Known Issues |
| Operational Procedures | Operations / Runbook | Operational Validation | Known Issues |
| Unconfirmed Items | `00_governance_03_issue-and-uncertainty-management.md` | Investigation Evidence | Needs Confirmation |

**Code is canonical for current behavior, NOT for adopted design.** When code
contradicts an ADR, the ADR represents the intended architecture and the discrepancy
must be registered as a Known Issue. Each area's document-guide identifies the
canonical source within that area — this matrix provides cross-cutting guidance only.

## Area Canonical Maps

### Overview
| Document | Authority | Status |
|----------|-----------|--------|
| docs/00_index.md | Primary | Active |
| docs/architecture.md | Secondary | Active |

### Deployment
| Document | Authority | Status |
|----------|-----------|--------|
| docs/deployment_guide.md | Primary | Active |
| deploy.sh | Operational | Active |

### RAG
| Document | Authority | Status |
|----------|-----------|--------|
| docs/rag/specification.md | Primary | Active |
| scripts/rag/embedding.py | Runtime | Active |

### MCP
| Document | Authority | Status |
|----------|-----------|--------|
| docs/mcp/specification.md | Primary | Active |
| scripts/mcp_servers/*.py | Runtime | Active |

### Agent
| Document | Authority | Status |
|----------|-----------|--------|
| docs/agent/specification.md | Primary | Active |
| scripts/agent/*.py | Runtime | Active |

### EventBus
| Document | Authority | Status |
|----------|-----------|--------|
| docs/eventbus/specification.md | Primary | Active |
| scripts/eventbus/*.py | Runtime | Active |

### Shared/DB
| Document | Authority | Status |
|----------|-----------|--------|
| docs/shared/specification.md | Primary | Active |
| scripts/shared/*.py | Runtime | Active |

### Governance
| Document | Authority | Status |
|----------|-----------|--------|
| docs/00_governance_01_documentation-policy.md | Primary | Active |
| docs/00_governance_02_documentation-metadata.md | Primary | Active |
| docs/00_governance_03_issue-and-uncertainty-management.md | Primary | Active |
| docs/00_governance_04_documentation-checks.md | Primary | Active |

## Conflict Resolution Rule

When two documents contradict each other:

1. Identify the area(s) each document belongs to
2. Determine if both documents are in the same area — if so, consult the area's document-guide for the canonical source
3. If documents span different areas, check whether one area's specification supersedes another's based on dependency direction
4. If neither rule resolves the conflict, register a Known Issue and defer resolution until the next review cycle

## Code vs Document Conflict Rule

When code contradicts a document, classify the conflict into one of five categories:

- **Outdated code** — Code has not been updated to reflect a recent design decision documented elsewhere
- **Design deviation** — Code intentionally deviates from the documented design (documented as such)
- **Provisional implementation** — Code implements a feature before formal documentation approval
- **Bug** — Code contains an error that produces behavior inconsistent with the documented intent
- **Missing documentation** — Code works correctly but no corresponding documentation exists

## Known Issues Registration Rule

Register a Known Issue when:

- A document-to-document conflict cannot be resolved using the Conflict Resolution Rule
- A code-vs-document conflict is classified as "design deviation" without documented justification
- A suspected bug requires investigation to confirm whether code or documentation is incorrect
- An unresolved conflict affects more than one area simultaneously

## Resolution Workflow

From detection to record-keeping:

1. Detect the conflict during normal review or through automated checks
2. Classify the conflict type using the rules above
3. Apply the appropriate resolution rule based on classification
4. Update affected documents or code to eliminate the conflict
5. Record the resolution in the relevant Known Issues document if applicable

## Update Rule

When a change occurs, the following documents must be updated based on the change type:

- **Architecture change** — Update Specification documents in the affected area, update Guide documents for cross-area impacts, update Operations documents if operational behavior changes
- **Configuration change** — Update Reference documents for the affected configuration, update Specification documents if behavior changes, update Guide documents if cross-area impacts exist
- **Command change** — Update Command Reference documents, update Guide documents for affected areas, update Known Issues if deprecations occur
- **Behavioral change** — Update Specification documents describing the behavior, update Operations documents if observable behavior changes, update Known Issues if discrepancies are found
- **Documentation-only change** — Update only the affected documents without triggering broader reviews

## Review Rule

The following conditions require review before merging:

- Any change to Governance-class documents
- Any change affecting more than three area documents simultaneously
- Any change that removes or renames a documented feature
- Any change that alters cross-area relationships or dependencies

## Change Impact Rule

To determine which documents are affected by a change:

1. Identify the change category (architecture, configuration, command, behavioral, documentation-only)
2. Map the change to affected areas using the area dependency graph
3. List all documents in affected areas that reference the changed element
4. Prioritize updates by document class priority: Specification > Guide > Reference > Operations > Note

## ADR Status Definitions

- `Proposed`: Under review, not yet adopted. A Proposed ADR is not a current
  architectural specification and must not be treated as one until it becomes
  Accepted.
- `Accepted`: Adopted and currently valid. An Accepted ADR is the current
  architectural specification for its decision.

## ADR Change Protocol

When the current architectural decision changes, update the current Accepted ADR
directly rather than creating a new ADR. In the same change, update every
Specification, Reference, Operations document, and verification requirement that the
changed decision affects.

## ADR Section Header Standardization

All ADRs must use these section headers in order: Context (Problem, Constraints), Assumptions, Decision, Rationale, Alternatives Considered, Consequences (Positive/Negative), Invariants, Verification, Implementation Notes, Known Deviations, Review Triggers, Approval, Related Documents, Completion Checklist.

Duplicate notes shared across all ADRs:
- "この章は設計判断の根拠にしない" (Do not use this chapter as the basis for design decisions)
- "該当しない場合は「対象外」と記載する" (If not applicable, write "Not applicable")
- "ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する" (Do not unconditionally align ADR text to current implementation; manage discrepancies via Known Issues)

The ADR list, dependency graph, and invariant verification matrix are maintained in
`adr-index.md`, not here.

## Software Dependency Graph vs Documentation Reference Graph Separation

Governance documents are excluded from the software component dependency graph because they do not represent runtime components. The software dependency graph covers only Agent, MCP Server, RAG, EventBus, and Shared/DB components.

Governance documents form their own reference graph within the documentation set. This separation prevents confusion between runtime architecture dependencies and documentation cross-references.

## Merge Conditions

### Blocking Conditions (Prevent Merge)
- Critical open issue exists in affected area
- RACI approval not obtained from accountable party
- Canonical source conflict unresolved
- Test suite failing

### Non-Blocking Conditions (Allow Merge with Warning)
- High-severity open issue exists in affected area
- Documentation outdated but code is correct
- Config drift detected but no behavioral impact

### Merge Workflow
1. Check blocking conditions — if any fail, reject merge.
2. If non-blocking conditions exist, add warning to PR description.
3. Obtain RACI approval from accountable party.
4. Resolve canonical source conflicts before merging.
5. Verify test suite passes before merging.

## Change-Impact Matrix

| Change Type | Architecture Impact | Config Impact | Behavior Impact | Doc-Only Impact | Approval Required |
|-------------|---------------------|---------------|-----------------|-----------------|-------------------|
| Architecture | High | Medium | High | Low | Yes (RACI) |
| Config | Low | High | Medium | Low | Yes (Owner) |
| Behavior | Medium | Low | High | Low | Yes (RACI) |
| Doc-Only | Low | Low | Low | High | No |

## RACI Model

Each area follows the same role pattern; substitute `<area-lead>` with that area's
lead role (Overview: `@architect`; Deployment: `@devops`; RAG: `@data-eng`; MCP:
`@mcp-dev`; Agent: `@agent-dev`; EventBus: `@eventbus-dev`; Shared/DB: `@db-admin`;
Governance: `@governance-lead`, accountable to `@executive`, consulted `@all-areas`).

| Role | Responsible | Accountable | Consulted | Informed |
|------|-------------|-------------|-----------|----------|
| `<area-lead>` | `<area-lead>` | @lead | @dev-team / @architect | @team / @stakeholders |
| Developer | @developer | `<area-lead>` | @reviewer | @team |
| Reviewer | @reviewer | `<area-lead>` | @developer | @team |

## Area Dependency Graph

Permitted dependency directions:

- Overview → Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance
- Deployment → RAG, MCP, Agent, EventBus, Shared/DB
- RAG → Agent, EventBus
- MCP → Agent, EventBus
- Agent → EventBus, Shared/DB
- EventBus → Shared/DB
- Governance → Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB

**Cycles prohibited**: No circular dependencies allowed.
**Direction constraint**: Dependencies only flow downward (Overview → Governance).

## Maintenance Rules

- New ADRs must be created within one week of the decision being made
- "Proposed" ADRs must be reviewed quarterly
- "Needs confirmation" items must be reviewed quarterly

## Non-Goals

This document does not cover:

- Source code review processes
- Testing strategy per area
- Individual area architectural decisions
- Document formatting conventions within Specification documents
- Defining how AI agents parse or use metadata fields
- Specifying enforcement mechanisms for metadata compliance
- Defining metadata for non-document assets (code, configuration files)

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Metadata](00_governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)
- [ADR Index](adr-index.md)

## Keywords

documentation
policy
governance
canonical source
ADR
conflict resolution
dependency graph
RACI
