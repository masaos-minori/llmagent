## Goal
Correct the `Agent ↔ RAG` statement that `scripts/agent/` imports nothing from `scripts/rag/` (`REQ-007` / `AC-7`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/agent/services/rag_maintenance_service.py:16` imports `rag.corpus_identity` and it is the only file under `scripts/agent/` doing so (checked 2026-11-12).
- UNK-04: `rmcompat003` (corpus identity) may remove the import; re-run `rg "rag\." scripts/agent` at implementation and keep the old statement only if no import remains.

## Design decisions
- State the relationship as the code has it and cite the allowed exception from `.importlinter` if it declares one.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`

### Procedure
1. Re-run `rg "rag\." scripts/agent` and read `.importlinter` for the permitted dependency.
2. Rewrite the `Not represented as an edge` bullet for Agent ↔ RAG accordingly.

### Method
- If the import exists: `Agent → RAG: scripts/agent/services/rag_maintenance_service.py imports rag.corpus_identity (the only import of scripts/rag/ under scripts/agent/); RAG search and ingestion otherwise reach the Agent only through the generic Agent → MCP edge.` Move the sentence out of the not-an-edge list if it is now a real edge.

### Details
- Word the statement from the code at implementation time, not from this document.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain overview`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict` — pass.

## Completion criteria
- `governance_05` agrees with the code's Agent to RAG import; the consistency check passes.

## Out of Scope
- Removing the import (corpus identity Plan); other governance statements.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` — Agent to RAG statement matches the code
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
