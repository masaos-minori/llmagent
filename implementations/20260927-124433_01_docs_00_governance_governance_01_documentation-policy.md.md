## Goal

Present the confirmed Security-runtime-package findings to the owner and record their decision on Security's Software Runtime Dependency Graph node status (REQ-001, REQ-002).

## Scope

In scope: presenting the two candidate outcomes and recording whichever the owner selects, in the Software Runtime Dependency Graph section. Out of scope: wiring `scripts/shared/security/` into any caller.

## Assumptions

N/A: none — the evidence (package exists, zero importers) is confirmed, re-verified this cycle.

## Design decisions

Record the decision inline in the Software Runtime Dependency Graph section, near the Node set sentence, rather than in a separate note elsewhere — keeps the decision co-located with what it affects.

## Alternatives considered

Recording the decision only in the (to-be-removed) NC-024 entry rather than in `governance_01` itself: rejected — the NC-024 entry is being removed (row 2 of this Plan), so the decision must live in the document it actually affects to survive that removal.

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

1. Re-confirm `scripts/shared/security/`'s zero-importer status via a fresh `rg -l "from shared.security|from scripts.shared.security|import shared.security" scripts/ tests/` immediately before presenting the decision (still zero matches as of this cycle).
2. Present the owner with the two options:
   - (a) Add `Security` to the Node set (currently "Agent, MCP, RAG, EventBus, Shared/DB", confirmed at line 441) with whatever edges reflect its actual (future) wiring, if wiring is imminent.
   - (b) Add a brief note near the Node set sentence stating `scripts/shared/security/` exists but has zero current importers, so it is intentionally excluded as a graph node until wired in — preventing this question from being re-investigated from scratch later.
3. Record whichever option the owner selects, in place.

### Method

Present-and-record decision task; the exact edit depends on which option is chosen — do not pre-select one.

### Details

- Confirmed current Node set sentence (re-verified this cycle, line 441): "Node set: Agent, MCP, RAG, EventBus, Shared/DB. Governance, Overview, and Deployment are not runtime components and are intentionally excluded — see the Governance Applicability Matrix and Deployment Management Graph below for their own relation types."
- If option (a): also add whatever edges the owner specifies to the "Confirmed edges" or "Planned" list (lines 454-467, not otherwise touched by this Plan).
- If option (b): insert a new sentence directly after the Node set paragraph, e.g.: "A `scripts/shared/security/` package exists (`HighRiskToolPolicy`, `SecurityMode`, `AuditLogger`) but has zero current importers anywhere in `scripts/`/`tests/` as of {date} — intentionally excluded from the node set until it is actually wired into a caller."

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change (the target file is a governance document, not the security package itself).

## Rollback considerations

`git revert` the commit, or manually remove the added note/node.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Automated | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py` | Pass, no new findings |

## Completion criteria

- The section states the owner's decision, with supporting evidence (AC-1).

## Out of scope

- Any other Software Runtime Dependency Graph node or edge.
- Wiring `scripts/shared/security/` into any caller.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Requires an owner decision between options (a)/(b) before the exact edit can be made |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, automated checks per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | N/A: documentation-only; docs checkers run instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own target file IS the documentation being updated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20260927-115816_nc024_determine-whether-security-should-be-a-runtime-dependency-graph-node.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121352_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124433
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
