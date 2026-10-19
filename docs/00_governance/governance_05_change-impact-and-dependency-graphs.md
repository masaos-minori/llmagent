---
title: "Change Impact and Dependency Graphs"
area: governance
tags:
  - governance
related:
  - governance_01_documentation-policy.md
  - governance_04_documentation-checks.md
---

# Change Impact and Dependency Graphs

## Purpose

This document defines how a change maps to the documents it affects, the approval model for governed changes, and the dependency-graph taxonomy.

## Update Rule

When a change occurs, the following documents must be updated based on the change type:

- **Architecture change** — Update the Accepted ADR for the decision (see ADR Change Protocol) and the Reference documents in the affected area, update Guide documents for cross-area impacts, update Operations documents if operational behavior changes
- **Configuration change** — Update Reference documents for the affected configuration, update the affected area's Reference documents if behavior changes, update Guide documents if cross-area impacts exist
- **Command change** — Update Command Reference documents, update Guide documents for affected areas, update Known Issues if a documented command is removed or renamed
- **Behavioral change** — Update the Reference documents describing the behavior, update Operations documents if observable behavior changes, update Known Issues if discrepancies are found
- **Documentation-only change** — Update only the affected documents without triggering broader reviews

## Change Impact Rule

To determine which documents are affected by a change:

1. Identify the change category:
   - architecture
   - configuration
   - command
   - behavioral
   - deployment
   - governance-policy
   - documentation-only

2. Select the applicable relation type:
   - Architecture, behavioral, or command changes: Software Runtime Dependency Graph
   - Deployment changes: Deployment Management Graph
   - Documentation-only changes: Documentation Reference Graph
   - Governance-policy changes: Governance Applicability Matrix
   - Configuration or API changes: [Resolution Matrix](governance_01_documentation-policy.md#resolution-matrix)

   Note: owner decision: a dedicated Configuration Ownership Map or API Consumer Map is not adopted. The Resolution Matrix settles the canonical source per claim type (`production-effective-value`, `configuration-schema`, `api-contract`), and consumers of a changed key or interface are found through step 4's reference search. Reconsider only if that search repeatedly misses affected documents.

3. Map the change to the areas or components covered by the selected graph or matrix.

4. List the documents in affected areas that reference the changed element.

5. Prioritize updates by document class: Guide > Reference > Operations > Note.

## Change-Impact Matrix

| Change Type | Architecture Impact | Config Impact | Behavior Impact | Doc-Only Impact | Approval Required |
|-------------|---------------------|---------------|-----------------|-----------------|-------------------|
| Architecture | High | Medium | High | Low | Yes (RACI) |
| Config | Low | High | Medium | Low | Yes (Owner) |
| Behavior | Medium | Low | High | Low | Yes (RACI) |
| Doc-Only | Low | Low | Low | High | No |

### Reading the Approval Required Column

`Approval Required` means design approval of the change by the accountable party. `No` for Doc-Only means no design approval is needed and a documentation-only change does not trigger the broader reviews of the Update Rule. It does not remove the Review Rule or the Merge Conditions of [Documentation Policy](governance_01_documentation-policy.md#review-rule), which remain the canonical definition of when review is required and which conditions block a merge; this section defines only which change types also require RACI approval, as summarized in the table below.

| Change | Review | RACI approval | Merge condition |
|---|---|---|---|
| Ordinary documentation fix (non-Governance, no Review Rule trigger) | Not required | Not required | Blocking Conditions only |
| Governance-class document change | Required | Required | Blocking Conditions and RACI approval |
| ADR edit that does not change the decision (wording, evidence, references) | Required only if a Review Rule trigger holds | Not required; approval is not reopened | Blocking Conditions only |
| ADR edit that changes the decision | Required | Required; a new approval record in the same change | Blocking Conditions and RACI approval |

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

`@lead` is the repository owner: the accountable party named in `## Merge Conditions` and `### ADR Acceptance Evidence Standard` of [Documentation Policy](governance_01_documentation-policy.md). "RACI approval" is approval by that role.

## Software Runtime Dependency Graph

Node set: Agent, MCP, RAG, EventBus, Shared/DB. Governance, Overview, and
Deployment are not runtime components and are intentionally excluded — see the
Governance Applicability Matrix and Deployment Management Graph below for their own
relation types.

`A → B` means: A calls B at runtime, or requires B's data or functionality to
function.

**Cycles prohibited**: no circular dependencies are allowed among these 5 nodes.
Enforced automatically by `tools/check_dependency_graph_cycles.py` (see
`docs/00_governance/governance_04_documentation-checks.md` "18. Area Dependency Graph
Validation").

Confirmed edges (direct source evidence: `scripts/agent/services/mcp_tool_discovery.py`
fetches every MCP server's `/v1/tools` over HTTP; the import statements under
`scripts/agent/`, `scripts/mcp_servers/`, `scripts/rag/` and `scripts/eventbus/` show
the Shared/DB dependencies; `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
imports `rag.pipeline`):
- Agent → MCP
- Agent → Shared/DB
- MCP → Shared/DB
- MCP → RAG
- RAG → Shared/DB
- EventBus → Shared/DB

The `MCP → RAG` edge exists only through the rag-pipeline MCP server, an MCP-facing
wrapper around `scripts/rag/`'s `RagPipeline` (`RagPipelineMCPService.start()`
imports and instantiates it; no other file under `scripts/mcp_servers/rag_pipeline/`
duplicates RAG pipeline logic).

Not represented as an edge:
- Agent ↔ RAG: `scripts/agent/` contains no import of `scripts/rag/`; RAG
  functionality is reached only through the generic `Agent → MCP` edge.
- Agent, RAG or MCP → EventBus: no runtime component calls the Event Bus. The
  client modules under `scripts/agent/` (`eventbus_client.py` and its siblings) are
  imported only by their unit tests, so they create no runtime dependency.

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
Governed only by the link and Related Rules in
[Documentation Metadata](governance_02_documentation-metadata.md#related-rules) (broken links,
self-reference, duplicate reference); verified by `tools/check_docs_structure.py`.

## Governance Applicability Matrix

Governance's relationship to each area is expressed as applicability, not as a
directed runtime or deployment dependency — Governance applies across every area rather than depending
on, or being depended on by, any one of them. Governance therefore does not
participate as a node in the Software Runtime Dependency Graph or the Deployment
Management Graph above. It is a node of the Documentation Reference Graph, because Governance documents cross-reference, and are cross-referenced by, the area documents; the Applicability Matrix is the separate, non-graph view of how governance rules apply to each area. The cycle prohibition of the Software Runtime Dependency Graph does not apply to the Documentation Reference Graph.

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

## Keywords

- change impact
- RACI
- dependency graph
- governance
