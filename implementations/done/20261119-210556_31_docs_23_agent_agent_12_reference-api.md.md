## Goal

- Register the new generated subpackage index in the curated agent API entry document, so a reader of `agent_12_reference-api.md` is routed to both generated indexes (`REQ-012`, `REQ-015`; `AC-013`).

## Scope
**Release unit**: reference-completeness

## Assumptions

- This curated document names `agent_13_reference-api-generated.md` in front matter (line 9) and nowhere else, so the body needs one new statement rather than a restructure.

## Design decisions

- `related:` front matter is the single cross-reference store (the rule stated in `tools/check_docs_structure.py:5`), so the new document is added as a `related:` entry rather than as a body link.
- The body statement says which half of the symbol index lives where: top-level `scripts/agent/` symbols in `agent_13_reference-api-generated.md`, subpackage symbols in `agent_14_reference-api-subpackages-generated.md.

## Alternatives considered

- Point only at `agent_13_reference-api-generated.md` and let readers discover the sibling: rejected by `REQ-015` - the documents that register the new index are named in the requirement.
- Move the curated per-component sections into the generated document: rejected - the curated narrative and the generated index have different owners per ADR-015.

## Implementation
### Target file
`docs/23_agent/agent_12_reference-api.md`
### Procedure
1. Add `agent_14_reference-api-subpackages-generated.md` to the front matter `related:` list beside `agent_13_reference-api-generated.md` (line 9).
2. In the Operational Notes section (line 48) add one bullet stating that the generated class and function index is split: top-level `scripts/agent/` symbols in `agent_13_reference-api-generated.md`, `scripts/agent/` subpackage symbols in `agent_14_reference-api-subpackages-generated.md`.

### Method
- Front matter entry plus one bullet; the curated per-component sections (Purpose through Keywords) are unchanged.

### Details
- Current front matter `related:` block spans lines 8-21 and names `agent_13_reference-api-generated.md` at line 9.
- File size 12155 B, far below `MAX_SIZE = 32768`, so the added bullet needs no size accounting.
- `tools/check_docs_structure.py` validates `related:` entries as plain `.md` basenames (lines 219-233), which the new entry satisfies.

## Compatibility considerations

- Row 30 creates the target document before this row's link resolves; run order is Phase 6 with row 30 first.

## Security considerations

- N/A: documentation only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py` — related links resolve, no finding for this file (docs: documentation structure)
- `uv run python tools/check_docs_consistency.py --domain agent` — no stale or missing reference (docs: documentation consistency)

## Completion criteria

- `AC-013`: the curated entry document names both generated indexes.

## Out of Scope

- Any rewrite of the curated component sections.
- Editing the generated documents themselves (rows 15, 30).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the related entry and the split statement | Completed | 20261119-232759 | 20261119-232759 | front matter plus one bullet related entry for agent_14 and the split-index Operational Note added; agent structure and consistency gates pass |
| 2 | Run the agent documentation checkers | Completed | 20261119-232759 | 20261119-232759 | structure and consistency gates related entry for agent_14 and the split-index Operational Note added; agent structure and consistency gates pass |

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
- **Requirement ID**: `REQ-012` (agent_api covers the scripts/agent/ subpackages (workflow/, services/, commands/, shared/) so the generated API reference is complete), `REQ-015` (the generated agent API index stays within the documentation size ceiling)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `docs/23_agent/agent_12_reference-api.md`