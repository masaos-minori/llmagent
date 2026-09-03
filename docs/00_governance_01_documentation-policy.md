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
3. If documents span different areas, identify the decision target the conflict concerns and apply the Decision Target Canonical Source Matrix (see `## Canonical Source Precedence` > `### Decision Target Canonical Source Matrix`) to determine the authoritative source for that decision target
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

1. Identify the change category (architecture, configuration, command, behavioral, deployment, governance-policy, documentation-only)
2. Select which relation type governs the change, by category:
   - Architecture, behavioral, or command changes → Software Runtime Dependency Graph
   - Deployment changes → Deployment Management Graph
   - Documentation-only changes → Documentation Reference Graph
   - Governance-policy changes → Governance Applicability Matrix
   - Configuration or API changes → continue to use the existing Canonical Source
     Precedence matrix (Decision Target Canonical Source Matrix); no separate
     Configuration Ownership Map or API Consumer Map exists (tracked as a Needs
     Confirmation entry in `docs/00_governance_03_issue-and-uncertainty-management.md`)

   Map the change to the areas or components covered by the selected graph or matrix.
3. List all documents in affected areas that reference the changed element
4. Prioritize updates by document class priority: Specification > Guide > Reference > Operations > Note

## ADR Status Definitions

- `Proposed`: Under review, not yet adopted. A Proposed ADR is not a current
  architectural specification and must not be treated as one until it becomes
  Accepted.
- `Accepted`: Adopted and currently valid. An Accepted ADR is the current
  architectural specification for its decision.

### ADR Acceptance Evidence Standard

An ADR's `## Approval` > `### Approval Record` section satisfies the "RACI approval not
obtained from accountable party" Blocking Condition (see Merge Conditions) when either of
the following holds:

1. **Named Approval Record**: the section records a specific reviewer, approval date, and
   reference (e.g., a review ticket or PR) for that ADR.
2. **Task-level approval decision**: the accountable party (repository owner) issued an
   explicit instruction, given as part of a specific documented task, to set the ADR's
   Status to `Accepted`. That instruction is itself sufficient acceptance evidence; no
   separate named Approval Record is required.

Where an ADR relies on a task-level approval decision, its Approval Record section must
say so explicitly. It must not use `pending` for `Approved By` / `Approval Date` /
`Approval Reference` (`pending` asserts that acceptance evidence is still outstanding,
which is false once a task-level decision has been made), and must not fabricate a
reviewer name, date, or reference that was never given.

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

## Merge Conditions

### Blocking Conditions (Prevent Merge)
- Critical open issue exists in affected area
- RACI approval not obtained from accountable party (for ADRs, see ADR Acceptance
  Evidence Standard for what counts as approval)
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

## Software Runtime Dependency Graph

Node set: Agent, MCP, RAG, EventBus, Shared/DB. Governance, Overview, and Deployment
are not runtime components and are intentionally excluded — see the Governance
Applicability Matrix and Deployment Management Graph below for their own relation
types.

`A → B` means: A calls B at runtime, or requires B's data or functionality to
function.

**Cycles prohibited**: no circular dependencies are allowed among these 5 nodes.
Enforced automatically by `tools/check_dependency_graph_cycles.py` (see
`docs/00_governance_04_documentation-checks.md` "12. Area Dependency Graph
Validation").

Confirmed edges (direct source evidence —
`scripts/agent/services/mcp_tool_discovery.py` fetches every MCP server's
`/v1/tools` over HTTP):
- Agent → MCP
- Agent → Shared/DB
- EventBus → Shared/DB

Needs Confirmation (tracked as `NC-022` in
`docs/00_governance_03_issue-and-uncertainty-management.md`; no corresponding
import or HTTP-publish call found in current source):
- RAG → EventBus
- MCP → EventBus
- Agent → EventBus

Not represented as an edge: no direct RAG ↔ Agent call path exists in current
source (`scripts/agent/` contains no import of `scripts/rag/`) — RAG-related
functionality, if any, is reached only through the generic `Agent → MCP` edge
above. Whether `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/` are the same
or a different RAG implementation is unresolved and tracked as `NC-023`.

## Deployment Management Graph

Node set: Deployment, plus every Software Runtime Dependency Graph node (Agent,
MCP, RAG, EventBus, Shared/DB).

`A → B` means: A places, starts, stops, or validates B's runtime — a management
relation, not a call dependency.

Not cycle-checked: a management graph is not expected to be acyclic in the same
sense as a call-dependency graph.

Edges:
- Deployment → Agent, MCP, RAG, EventBus, Shared/DB

## Documentation Reference Graph

Node set: every documentation area — Overview, Deployment, RAG, MCP, Agent,
EventBus, Shared/DB, Governance.

`A → B` means: area A's documentation cross-references area B's documentation.

Not cycle-checked: mutual cross-references between areas (for example, Overview ↔
Governance) are expected and are not a violation of any rule in this graph.
Checked only for broken links, self-reference, and duplicate reference — see
`tools/check_docs_structure.py`.

## Governance Applicability Matrix

Governance's relationship to each area is expressed as applicability, not as a
directed graph edge — Governance applies across every area rather than depending
on, or being depended on by, any one of them. Governance therefore does not
participate as a node in the Software Runtime Dependency Graph, the Deployment
Management Graph, or the Documentation Reference Graph above.

| Area | Governance Applies |
|------|---------------------|
| Overview | Yes |
| Deployment | Yes |
| RAG | Yes |
| MCP | Yes |
| Agent | Yes |
| EventBus | Yes |
| Shared/DB | Yes |

Not cycle-checked: this is a matrix, not a directed graph.

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
