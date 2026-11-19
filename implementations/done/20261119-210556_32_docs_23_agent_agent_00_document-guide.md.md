## Goal

- Add the new generated subpackage index to the agent documentation guide, so the query-routing table that sends signature questions to the API reference points at both generated indexes (`REQ-015`; `AC-013`).

## Scope
**Release unit**: reference-completeness

## Assumptions

- The guide routes through `agent_12` (routing rows at lines 62 and 71), so the new document enters through the same rows rather than as a new row.

## Design decisions

- Keep the guide's routing shape: the generated index is reached through the curated entry document, and the guide names both halves only where a reader is looking for a symbol.

## Alternatives considered

- Add a separate routing row for the subpackage index: rejected - the existing rows already describe the question class, and a second row would split one question across two entries.

## Implementation
### Target file
`docs/23_agent/agent_00_document-guide.md`
### Procedure
1. Add `agent_14_reference-api-subpackages-generated.md` to the front matter `related:` list (it currently names `agent_12_reference-api.md` at line 13).
2. Extend the routing row at line 62 (`What is the agent? Major components/deps, function signatures`) so its target column names `agent_13_reference-api-generated.md` and `agent_14_reference-api-subpackages-generated.md` beside `agent_12_reference-api.md`.
3. Extend the routing row at line 71 (`Where is class X defined and who calls it`) the same way.

### Method
- One front matter entry and two table-cell edits; no new table rows.

### Details
- Current routing rows: line 62 targets `agent_01` / `agent_02` / `agent_12`; line 71 targets `agent_12` -> `agent_02`.
- File size 4786 B, so the additions need no size accounting.
- The guide is the area entry point `tools/check_docs_structure.py` validates for front matter and related-link resolution.

## Compatibility considerations

- Row 30 creates the document this row routes to; row 31 registers it in the curated entry document.

## Security considerations

- N/A: documentation only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py` — front matter and related links pass (docs: documentation structure)

## Completion criteria

- `AC-013`: the area guide routes to both generated indexes.

## Out of Scope

- Any change to other routing rows.
- Editing generated documents (rows 15, 30).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the related entry and extend the two routing rows | Completed | 20261119-232759 | 20261119-232759 | docs only related entry added and both routing rows now name agent_13 and agent_14; uv run python tools/check_docs_structure.py: All checks passed |
| 2 | Run `uv run python tools/check_docs_structure.py` | Completed | 20261119-232759 | 20261119-232759 | structure gate related entry added and both routing rows now name agent_13 and agent_14; uv run python tools/check_docs_structure.py: All checks passed |

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
- **Requirement ID**: `REQ-015` (the generated agent API index stays within the documentation size ceiling)
- **Source issue**: issues/20261117-123014_adrchk014_contract-manifest-sources.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-181257_adrchk014_contract-manifest-sources.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-210556
- **Related target files**: `docs/23_agent/agent_00_document-guide.md`