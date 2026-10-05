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

This document defines how a change maps to the documents it affects, the approval model for governed changes, and the dependency-graph taxonomy. It was split out of the [Documentation Policy](governance_01_documentation-policy.md).

## Update Rule

When a change occurs, the following documents must be updated based on the change type:

- **Architecture change** — Update Specification documents in the affected area, update Guide documents for cross-area impacts, update Operations documents if operational behavior changes
- **Configuration change** — Update Reference documents for the affected configuration, update Specification documents if behavior changes, update Guide documents if cross-area impacts exist
- **Command change** — Update Command Reference documents, update Guide documents for affected areas, update Known Issues if deprecations occur
- **Behavioral change** — Update Specification documents describing the behavior, update Operations documents if observable behavior changes, update Known Issues if discrepancies are found
- **Documentation-only change** — Update only the affected documents without triggering broader reviews

## Change Impact Rule

To determine which documents are affected by a change:

1. Identify the change category (architecture, configuration, command, behavioral, deployment, governance-policy, documentation-only)
2. Select which relation type governs the change, by category:
   - Architecture, behavioral, or command changes → Software Runtime Dependency Graph
   - Deployment changes → Deployment Management Graph
   - Documentation-only changes → Documentation Reference Graph
   - Governance-policy changes → Governance Applicability Matrix
   - Configuration or API changes → continue to use the existing Canonical Source
     Precedence matrix ([Decision Target Canonical Source Matrix](governance_01_documentation-policy.md#decision-target-canonical-source-matrix)) until a dedicated
     map exists; owner decision: a Configuration Ownership Map or API
     Consumer Map is needed for per-key ownership traceability, but building it is
     separate, unstarted follow-up work — not part of this change

   Map the change to the areas or components covered by the selected graph or matrix.
3. List all documents in affected areas that reference the changed element
4. Prioritize updates by document class priority: Specification > Guide > Reference > Operations > Note

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

Node set: Agent, MCP, RAG, EventBus, Shared/DB. Governance, Overview, and
Deployment are not runtime components and are intentionally excluded — see the
Governance Applicability Matrix and Deployment Management Graph below for their own
relation types.

`A → B` means: A calls B at runtime, or requires B's data or functionality to
function.

**Cycles prohibited**: no circular dependencies are allowed among these 5 nodes.
Enforced automatically by `tools/check_dependency_graph_cycles.py` (see
`docs/00_governance/governance_04_documentation-checks.md` "12. Area Dependency Graph
Validation").

Security is not a node in this graph: `scripts/shared/security/` (`HighRiskToolPolicy`,
`SecurityMode`, `AuditLogger`) has no importers in `scripts/`/`tests/`, so no edge
exists for it. If it is wired in later, add it to the node set in
`tools/check_dependency_graph_cycles.py` together with its edge here.

Confirmed edges (direct source evidence —
`scripts/agent/services/mcp_tool_discovery.py` fetches every MCP server's
`/v1/tools` over HTTP; `scripts/agent/eventbus_client.py` publishes to the Event Bus
`/publish` endpoint over HTTP):
- Agent → MCP
- Agent → Shared/DB
- EventBus → Shared/DB
- Agent → EventBus

Planned (design intent, not yet implemented; these are
intended future integrations rather than a documentation error; no corresponding
import or HTTP-publish call exists in current source, and none is expected until
each integration is implemented):
- RAG → EventBus
- MCP → EventBus

Not represented as an edge: no direct RAG ↔ Agent call path exists in current
source (`scripts/agent/` contains no import of `scripts/rag/`) — RAG-related
functionality, if any, is reached only through the generic `Agent → MCP` edge
above. `scripts/mcp_servers/rag_pipeline/` is an MCP-facing wrapper around
`scripts/rag/`'s `RagPipeline` (confirmed via
`rag_pipeline_service.py::RagPipelineMCPService.start()`'s direct
import/instantiation of it, and confirmation that no other file under
`scripts/mcp_servers/rag_pipeline/` duplicates RAG pipeline logic), reachable
via the existing `Agent → MCP` edge with no separate node or edge needed.

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

## Keywords

change impact
RACI
dependency graph
governance
