## Goal

Add cross-references from `docs/03_rag_01_system_overview.md`'s Query Pipeline "Owned State" line (`RagPipeline` owns query execution lifecycle; SQLite owns the vector store layer) to the ADRs that actually explain this ownership's rationale (`ADR-005`: canonical-source/derived-index relationship; `ADR-010`: in-process fallback model; the repository's layered-architecture rule in `rules/env.md`), and state plainly that modification-rights implications and exceptions to the ownership rules are not separately recorded anywhere (REQ-001, REQ-002).

## Scope

- Add ADR/rule cross-references to the Query Pipeline's "Owned State" line, addressing the Issue's points 1-2 (why each component owns its state, rationale for the boundaries) with references to existing design documents
- Add a brief note that points 3-4 (modification-rights implications, known exceptions) are not separately recorded

## Assumptions

- `ADR-005` and `ADR-010` remain `Accepted` (not `Superseded`) as of this cycle — confirmed by reading their `## Status` sections, not merely assumed
- The targeted review of `rules/env.md`/`ADR-005`/`ADR-010` plus the repository-wide `grep` for modification-rights/exception terminology found the complete set of any existing guidance on those two points

## Design decisions

1. Cross-reference existing ADRs/rules rather than restate their content inline — `ADR-005` and `ADR-010` are the authoritative sources for their respective rationale; restating them here would create a second copy that could drift out of sync
2. State the modification-rights/exceptions gap as a confirmed fact (per the pattern established in sibling issues `183021`/`183024`/`183025` this cycle), not as an open question — this cycle's search was targeted and thorough enough to treat the absence as established, not merely unconfirmed

## Alternatives considered

1. Writing a new ADR or rationale document for the ownership model — rejected because existing ADRs already cover the relevant rationale — see Background; duplicating their content here would create a second source of truth
2. Fabricating modification-rights guidance or exception cases not backed by any existing document — rejected because per user direction, consistent with sibling issues `183021`/`183024`/`183025` processed this same cycle, where no such guidance existed
3. Correcting the Ingestion Pipeline section's own, separately-structured ownership description (lines 44-48) — rejected because the Issue's cited text is specific to the Query Pipeline section (lines 52-55)

## Implementation

### Target file

`docs/03_rag_01_system_overview.md`

### Procedure

1. Re-confirm each ADR's status and relevant content
2. Add cross-references and the gap note after the "Owned State" line
3. Manual verification

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-read `ADR-005`'s and `ADR-010`'s `## Status` sections to confirm both remain `Accepted` (REQ-001; `docs/03_rag_01_system_overview.md`)
- Re-confirm `rules/env.md`'s layered-architecture rule wording is unchanged (REQ-001; `docs/03_rag_01_system_overview.md`)

Phase 2: Core Logic — add cross-references and the gap note
- Add the 3 cross-references and the gap note after line 53 (REQ-001, REQ-002; `docs/03_rag_01_system_overview.md`)

Phase 3: Verification
- Manual review: confirm each cross-reference accurately summarizes its target document's relevant content (REQ-001)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_01_system_overview.md:52-53` contains the Query Pipeline "Owned State" line:
  - Line 52: "- **Component Responsibilities**: Agent turn invokes `RagPipeline.augment(query)` via MCP HTTP; RagPipeline executes MQE → Search → RRF → Rerank → Augment stages; KNN + BM25 search operates over SQLite (rag.db)."
  - Line 53: "- **Owned State**: RagPipeline owns the query execution lifecycle; SQLite (rag.db) owns the vector store layer."
- Layered-architecture rule confirmed in `rules/env.md:39-56`:
  - Line 41: "6 層構成（トップレベル `scripts/{agent,db,eventbus,mcp_servers,rag,shared}/`）。`.importlinter`（リポジトリ直下）が依存方向を強制する。"
  - Lines 44-49: Dependency chain showing `rag → db, shared`
- `ADR-005`'s Status confirmed as `Accepted` (line 20): canonical-source/derived-index rationale directly relevant to *why* SQLite is positioned as the vector-store layer's owner
- `ADR-010`'s Status confirmed as `Accepted` (line 20): in-process fallback rationale directly relevant to *why* `RagPipeline` owns the full query-execution lifecycle including fallback
- No modification-rights/exception documentation found via targeted review of `rules/env.md`, `ADR-005`, `ADR-010`, and a repository-wide `grep` for "modification rights"/"ownership exception" — no match

**Phase 2:** Append the following immediately after line 53:

```markdown
- **Ownership rationale**: `rag` layer's authority over query execution derives from the repository's layered-architecture rule (`rules/env.md`); SQLite's ownership of the vector store layer derives from `ADR-005` (canonical-source/derived-index relationship) and `ADR-010` (in-process fallback model). Note: modification-rights implications and known exceptions to these ownership rules are not separately documented anywhere in this repository.
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the rationale for the ownership model helps readers understand why the architecture is structured as it is, and prevents them from searching for governance documentation that does not exist.

## Security considerations

No security impact — documentation addition only. However, accurate documentation of the ownership model's rationale is important for understanding the pipeline's defense posture against injection attacks and other security concerns.

## Rollback considerations

Simple revert: remove the added cross-references and gap note. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_01_system_overview.md | Manual — verify cross-references against their target documents | Manual inspection | Each cross-reference accurately reflects its target's content |

## Completion criteria

- [ ] The Query Pipeline "Owned State" line is followed by cross-references to `rules/env.md`'s layered-architecture rule, `ADR-005`, and `ADR-010` (REQ-001)
- [ ] Each cross-reference states, in one clause, what specific aspect of the ownership model that document explains (REQ-001)
- [ ] A note states modification-rights implications and known exceptions are not separately recorded anywhere in this repository (REQ-002)
- [ ] The existing "Owned State"/"Reason for Process Separation" lines and the Ingestion Pipeline section (lines 44-48) remain unchanged

## Out of scope

- Writing a new ADR or rationale document for the ownership model (existing ADRs already cover the relevant rationale — see Background; duplicating their content here would create a second source of truth)
- Fabricating modification-rights guidance or exception cases not backed by any existing document (per user direction, consistent with sibling issues `183021`/`183024`/`183025` processed this same cycle, where no such guidance existed)
- Correcting the Ingestion Pipeline section's own, separately-structured ownership description (lines 44-48) — the Issue's cited text is specific to the Query Pipeline section (lines 52-55)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm each ADR's status and relevant content | Completed | — | 20260914-120100 | |
| 2 | Phase 2: Add cross-references and the gap note | Completed | — | 20260914-120100 | |
| 3 | Phase 3: Manual verification | Completed | — | 20260914-120100 | |

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
- **Source issue**: issues/20260913-183027_missing_system_overview_component_ownership_rationale.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-212340_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-101243
- **Related target files**: docs/03_rag_01_system_overview.md
