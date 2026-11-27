## Goal

Order the chapter index table by chapter file number (REQ-006; AC-3).

## Scope
**Release unit**: N/A: no release unit

## Assumptions

- Confirmed in Step 3a: the table at `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md:30-40` lists the
  chapter files in the order 04, 05, 02, 03, 07, 08, 09, 10, 06.
- UNK-02 is resolved: the maintainer confirmed the chapter-numbering convention on 2026-11-26, so this step proceeds.
  No governance rule states the convention (`docs/00_governance/governance_00_document-guide.md`,
  `governance_01_documentation-policy.md`), so the change is a navigation normalization.
- The table lists the nine chapter files 02 to 10 and does not list the index file itself; the entry set is not
  changed, only the order.
- `tests/docs/test_command_docs_sync.py` enumerates the chapter-07 file paths (`:58-74`), not the index table order,
  so reordering the rows does not affect it. It is a validation reference, not a modification target.

## Design decisions

- Rows are sorted by the chapter file number in ascending order; the `Content` descriptions stay attached to their
  own rows rather than being rewritten.

## Alternatives considered

- Adding the index file as a row — rejected: the change responsibility is ordering only, and the file is the index
  itself.

## Implementation
### Target file
`docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`
### Procedure

- Reorder the table rows at `:32-40` to 02, 03, 04, 05, 06, 07, 08, 09, 10.

### Method

- Row reordering only; no link text or description text changes.

### Details

- Keep the table header and the surrounding paragraph unchanged.

## Compatibility considerations

- The chapter is referenced by `tests/docs/test_command_docs_sync.py`, `docs/00_index.md`,
  `docs/01_overview/overview_01_03-arch-features.md`, `routing.md`, and the chapter's own front-matter `related:`
  lists; content-only edits do not break those references.

## Security considerations

- N/A: documentation-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Structural gate — `uv run python tools/check_docs_structure.py 'docs/23_agent/agent_07_*.md'`: all checks passed.
- Link reachability — the same gate resolves the table's relative links.
- Unit — `uv run pytest tests/docs/test_command_docs_sync.py`: passes unchanged.
- Sequence: format → lint → type → arch → security → test → coverage (`rules/toolchain.md`).

## Completion criteria

- The chapter index lists the files in chapter numbering order, no empty section remains in the chapter, and the docs
  gates report no finding.

## Out of Scope

- Renaming files whose names do not match their content (out of scope per Scope).
- Adding the index file as a table row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reorder the index table per Procedure/Method/Details | Completed | 20261127-120618 | 20261127-120618 | Plan Phase 6 Plan Phase 6 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-120618 | 20261127-120618 | Plan Phase 7 Plan Phase 7 |

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
- **Requirement ID**: `REQ-006` (chapter index navigation order)
- **Source issue**: `issues/20261119-145312_cliplc014_cli-docs-consolidation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-223853_cliplc014_cli-docs-consolidation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-001124
- **Related target files**: `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`