## Goal
Replace `docs/00_governance_01_documentation-policy.md`'s single, self-contradictory
`## Area Dependency Graph` (contains a direct `Overview → Governance` /
`Governance → Overview` cycle while also declaring "Cycles prohibited") and its
disconnected `## Software Dependency Graph vs Documentation Reference Graph
Separation` section with four separately-scoped relation types (Software Runtime
Dependency Graph, Deployment Management Graph, Documentation Reference Graph,
Governance Applicability Matrix), and update Conflict Resolution Rule rule 3 and
Change Impact Rule so neither cites the removed cyclic graph as an authority/impact
mechanism.

## Scope
- **In-Scope**: `docs/00_governance_01_documentation-policy.md` only — the four new
  relation-type sections, Conflict Resolution Rule rule 3, Change Impact Rule (steps 1
  and 2).
- **Out-of-Scope**: `docs/00_governance_04_documentation-checks.md` (section 12,
  GV-015, Change Impact Assessment — seq 02 of this Plan's implementation-procedure
  set), `docs/00_governance_03_issue-and-uncertainty-management.md` (NC-022–025 —
  seq 03), `tools/check_dependency_graph_cycles.py` and its test (seq 04/05), the CI
  workflow step (seq 06). Resolving `docs/adr-index.md`'s own CDR-1/CDR-2 cycles
  (unrelated graph, out of this Plan's scope per the Plan's own Out-of-Scope).

## Assumptions
- The Runtime Dependency Graph's edge list stays in the current plain-text
  `A → B, C` bullet format (matching the existing graph's format), per the Plan's own
  Assumptions, so `tools/check_dependency_graph_cycles.py` (seq 04) can regex-parse it
  without a new data format.
- The four new sections are added as new sections within this existing document
  rather than as a new standalone document, per the Plan's own Design decision 1.
- Configuration/API-affecting changes continue to use the existing Canonical Source
  Precedence matrix; no new Configuration Ownership Map / API Consumer Map is created
  by this row (registered as an NC entry by seq 03), per the Plan's Design decision 2.

## Design decisions
- **Placement**: the four new sections replace `## Area Dependency Graph` in place
  (after `## RACI Model`, before `## Maintenance Rules`), and
  `## Software Dependency Graph vs Documentation Reference Graph Separation` is
  deleted from its original location (between `## ADR Section Header Standardization`
  and `## Merge Conditions`) with no replacement left there, since its content is now
  fully subsumed by the new Software Runtime Dependency Graph section. Verified via
  `grep -rn "Software Dependency Graph vs Documentation Reference Graph
  Separation|Area Dependency Graph" --include="*.md" .` that no other active document
  (only historical `issues/done/`, `requires/done/`, and one unrelated
  `implementations/done/…governance_framework.py.md` file, none of them live
  documents this policy links to) references either heading by markdown anchor, so no
  other file needs an anchor-link update.
- **Governance Applicability Matrix representation**: expressed as a table
  (area × "Governance Applies") rather than a topic-by-topic breakdown, because this
  document's own `## Purpose` already states its rules "apply across areas"
  uniformly — inventing a differentiated per-area/per-topic breakdown not evidenced
  anywhere in the current document would be a fabricated distinction, not a
  documented one. The matrix explicitly states it is not cycle-checked and is not a
  directed-edge relation, satisfying REQ-001's "state node set / `A → B` meaning /
  cycle-tolerance" requirement in the form appropriate to a matrix rather than a
  graph (the Plan's own Implementation intent describes this section as "a matrix …
  not as directed graph edges").
- **`RAG → Agent` edge removal**: REQ-002 requires "no direct `RAG → Agent`". Rather
  than keeping a "known-false" edge annotated as disproven, the edge is simply omitted
  from the Software Runtime Dependency Graph's edge list, with a prose note
  explaining RAG is reached only via the generic `Agent → MCP` edge — consistent with
  how the graph already omits any edge that does not exist (a graph is its edge list,
  not an exhaustive matrix of asserted-absent pairs).
- **Change Impact Rule step 1 category list extension**: REQ-006 requires selecting
  among four graphs/matrix by category, including "deployment" and
  "governance-policy" categories that step 1's original category list
  (architecture, configuration, command, behavioral, documentation-only) does not
  enumerate. Step 1 is extended to add `deployment` and `governance-policy` so step
  2's category-based selection is well-defined for every category it names. This is a
  direct, minimal consequence of REQ-006's own requirement, not scope creep — no
  other Update Rule / Change-Impact Matrix category list is touched, since those are
  separate rules this Plan's Requirements do not target.
- **`command` category mapping**: not explicitly assigned a graph by REQ-006. Mapped
  to the Software Runtime Dependency Graph alongside architecture/behavioral changes,
  since a command change is a runtime-behavior change (Update Rule already groups
  "Command change" near "Behavioral change" in its own list) — recorded here as a
  design call, not left undefined.

## Alternatives considered
- **Keep the two old sections' locations, editing each into one of the four new
  sections in place (Separation → Software Runtime Dependency Graph at its original
  line ~253; the other three new sections inserted at the old Area Dependency Graph
  location)** — rejected: it would split four closely-related relation-type
  definitions across two distant parts of the document, working against the
  Reference Files' and Change Impact Rule's need to cite all four together; grouping
  them in one place (where `## Area Dependency Graph` already was) is more readable
  and is what the Plan's Implementation intent bullet list already presents as one
  group.
- **Represent the Governance Applicability Matrix as directed graph edges
  (`Governance → <area>`) instead of a matrix** — rejected: this is exactly the
  "special-casing" the Plan's Implementation intent explicitly rules out ("removing
  Governance from graph traversal entirely rather than special-casing it"); it would
  also reintroduce Governance as a graph node that the Software Runtime Dependency
  Graph, Deployment Management Graph, and Documentation Reference Graph all
  deliberately exclude or treat differently.
- **Leave `RAG → Agent` in the graph but annotate it "disproven"** — rejected in
  favor of omission (see Design decisions) because an edge list that includes
  known-false edges (even annotated) invites a future editor to treat the annotation
  as optional metadata and restore the edge; omission is the graph's own native way
  of expressing "no such relation."

## Implementation
### Target file
`docs/00_governance_01_documentation-policy.md`

### Procedure
1. Re-read the current file in full immediately before editing (line numbers below
   were confirmed 2026-09-03 against this file's current content; re-confirm they
   have not drifted further before applying any edit, per this workflow's
   revalidation requirement).
2. Delete `## Software Dependency Graph vs Documentation Reference Graph Separation`
   (currently lines 253-258, i.e. through the blank line immediately preceding
   `## Merge Conditions`) with no replacement text.
3. Replace `## Area Dependency Graph` (currently lines 302-316, i.e. through the
   blank line immediately preceding `## Maintenance Rules`) with the four new
   sections (Software Runtime Dependency Graph, Deployment Management Graph,
   Documentation Reference Graph, Governance Applicability Matrix) given in Details
   below.
4. Rewrite Conflict Resolution Rule item 3 (currently line 147) as given in Details
   below; leave items 1, 2, and 4 unchanged.
5. Rewrite Change Impact Rule steps 1 and 2 (currently lines 202-203) as given in
   Details below; leave steps 3 and 4 unchanged.

### Method
Direct text edit (e.g. via the `Edit` tool) using the exact before/after blocks in
Details. Apply steps 2-3 (the section replacement) as one contiguous edit and steps
4-5 (the two rule rewrites) as separate, independent edits, since they are not
textually adjacent.

### Details

**Edit 1 — delete the Separation section** (between
`## ADR Section Header Standardization`'s closing paragraph and `## Merge
Conditions`):

Before:
```
## Software Dependency Graph vs Documentation Reference Graph Separation

Governance documents are excluded from the software component dependency graph because they do not represent runtime components. The software dependency graph covers only Agent, MCP Server, RAG, EventBus, and Shared/DB components.

Governance documents form their own reference graph within the documentation set. This separation prevents confusion between runtime architecture dependencies and documentation cross-references.

## Merge Conditions
```

After:
```
## Merge Conditions
```

**Edit 2 — replace the Area Dependency Graph section** (between `## RACI Model`'s
table and `## Maintenance Rules`):

Before:
```
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
```

After:
```
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
```

**Edit 3 — Conflict Resolution Rule item 3** (REQ-005):

Before:
```
3. If documents span different areas, check whether one area's specification supersedes another's based on dependency direction
```

After:
```
3. If documents span different areas, identify the decision target the conflict concerns and apply the Decision Target Canonical Source Matrix (see `## Canonical Source Precedence` > `### Decision Target Canonical Source Matrix`) to determine the authoritative source for that decision target
```

**Edit 4 — Change Impact Rule steps 1 and 2** (REQ-006):

Before:
```
1. Identify the change category (architecture, configuration, command, behavioral, documentation-only)
2. Map the change to affected areas using the area dependency graph
```

After:
```
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
```

## Compatibility considerations
No other live document links to the removed section headings by markdown anchor
(verified by repository-wide `grep`, see Design decisions). `docs/00_governance_04_documentation-checks.md`'s section 12 (seq 02 of this Plan)
still names "Area Dependency Graph Validation" as its own heading — seq 02 updates
that section's body to reference this document as canonical rather than duplicating
the graph, so no naming collision results. This row does not modify section 12
itself.

## Security considerations
None — documentation-only change to governance policy text; no code, credentials, or
access-control content is affected.

## Rollback considerations
Single-file, four-edit change to a Markdown document under version control; revert
via `git revert` of the commit containing these edits. No other file's content
depends on the removed sections' exact text (see Compatibility considerations), so
rollback carries no cross-file follow-up.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_01_documentation-policy.md | Automated doc structure/quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/00_governance_01_documentation-policy.md | Automated doc structure check | `uv run python tools/check_docs_structure.py docs/00_governance_01_documentation-policy.md` | No new errors, no broken links introduced |
| docs/00_governance_01_documentation-policy.md | Manual review | Re-read the four new sections and both rewritten rules | Each new section states its own node set, `A → B` meaning (or explicit non-applicability for the matrix), and cycle-tolerance; rule 3 and Change Impact Rule cite no removed section |

Note: the cycle-freedom claim for the Software Runtime Dependency Graph's edges
(AC-2) is validated by `tools/check_dependency_graph_cycles.py`, added in seq 04/05
of this Plan — not re-validated by this row in isolation, since the tool does not
exist yet at this row's implementation time.

## Completion criteria
- `## Area Dependency Graph` and `## Software Dependency Graph vs Documentation
  Reference Graph Separation` no longer exist in this file.
- Four new sections exist, each naming its node set, `A → B` meaning (or explicit
  non-applicability), and cycle-tolerance (AC-1).
- The Software Runtime Dependency Graph excludes Governance/Overview/Deployment,
  omits `RAG → Agent` and `MCP → Agent`, includes `Agent → MCP`, and marks the three
  EventBus edges Needs Confirmation (AC-2).
- Conflict Resolution Rule item 3 no longer mentions "dependency direction" and
  instead references the Decision Target Canonical Source Matrix (AC-5).
- Change Impact Rule states which of the four graphs/matrix applies per change
  category and states that configuration/API changes use the existing Canonical
  Source Precedence matrix (AC-6).
- `uv run python tools/check_docs_quality.py` and `uv run python
  tools/check_docs_structure.py docs/00_governance_01_documentation-policy.md`
  report no new errors.

## Out of scope
`docs/00_governance_04_documentation-checks.md`, `docs/00_governance_03_issue-and-uncertainty-management.md`,
`tools/check_dependency_graph_cycles.py`, its test file, and the CI workflow step —
each has its own implementation-procedure document (seq 02-06) per this Plan's
Implementation Target Files table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Initially Blocked (see Blocker Log, resolved) — Edits 1-4 applied as originally designed once the blocker was resolved. |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | N/A: documentation-only row, no test file owned by this row; test coverage for the blocker's resolution (`MAX_SIZE`) was added to `tests/tools/test_check_docs_structure.py` as part of resolving Step 1 — see Blocker Log |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `uv run python tools/check_docs_quality.py` (0 errors, 1 pre-existing unrelated warning) and `uv run python tools/check_docs_structure.py docs/00_governance_01_documentation-policy.md` (All checks passed) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | This row's own target file is the documentation update; no `docs/00_index.md` task-scope mapping applies (governance self-edit, per the Plan's own Documentation Impact note) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `docs/00_governance_01_documentation-policy.md` is a hard-capped 16KB file (`tools/check_docs_structure.py` `MAX_SIZE`) that was already at 16252/16384 bytes before this Plan — REQ-001/002/005/006's mandated 4-section replacement cannot fit within the remaining ~132 bytes even after 4 rounds of prose compression (best reached: 16808 bytes, 424 over). Escalated to the user via `AskUserQuestion`; user selected "revisit the 16KB limit check itself" over splitting the document or further content loss. Resolved by raising `tools/check_docs_structure.py`'s `MAX_SIZE` from 16384 to 24576 (comment explains why; `docs/00_governance_03_issue-and-uncertainty-management.md` at ~46KB was found to already exceed even the old limit as a pre-existing, unrelated condition — confirming the old limit was already stale/under-enforced) and adding `TestCheckSize` regression coverage to `tests/tools/test_check_docs_structure.py`. Edits 1-4 then re-applied with their original (non-compressed) text; `docs/00_governance_01_documentation-policy.md` is 19183 bytes, under the new 24576 limit. This resolution touched `tools/check_docs_structure.py` and its test file, outside this row's originally-declared Scope/Target file — authorized by explicit, current-turn user instruction (`rules/ai-execution.md` Instruction Precedence, layer 1). | Yes | 2026-09-03 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| tools/check_docs_structure.py MAX_SIZE change | 1 | Code Change | Completed | N/A | N/A |
| tests/tools/test_check_docs_structure.py TestCheckSize | 2 | Test | Completed | N/A | N/A |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-005, REQ-006
- **Source issue**: issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142052
- **Related target files**: docs/00_governance_01_documentation-policy.md
