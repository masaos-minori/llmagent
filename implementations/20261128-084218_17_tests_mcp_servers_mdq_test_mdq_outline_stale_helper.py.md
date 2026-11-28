## Goal

Read the returned text and metadata separately in the missing-document-row case, so the characterization of the "no matching documents row" branch stays valid after `outline()` returns a text-plus-metadata pair (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

- One test, `test_outline_no_stale_warning_when_document_row_missing`, lines 61-63.
- Line 62 asserts the metadata state is not stale; line 63 asserts the heading text through the returned text element.
- The fixture that deletes the `documents` row and the module docstring statement about the unreachable NULL half of the guard are unchanged.

## Assumptions

- `OutlineMetadata` carries the stale state (`stale: bool`) alongside `refresh_in_progress` and `index_generation`, per the Plan's Design statement that the display wording is kept and the state moves to metadata. Row 01 is the row that owns the metadata shapes; the recorded requirement text names only the two consistency fields, so the stale field is the reading this amended row depends on and is reported for confirmation.
- The branch being characterized is "no row at all", so the state must be reported as not stale, which is what the current assertion says through the absence of the warning wording.
- `Title` is display output from the formatted outline, so it stays asserted on the text element; the module's point is that the guard returns no stale state while the heading text is still produced.
- Module classification stays as it is: `tests/mcp_servers/mdq/` is not a classified area and the module carries no marker.

## Design decisions

- Assert the state through metadata and the wording through the text element, in separate assertions, so the module keeps characterizing the guard rather than the formatter.

## Alternatives considered

- Keep `in result` and apply it to the pair's text element only: rejected, that drops the state assertion, which is the point of the row.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`

### Procedure
1. Unpack the value `service.outline()` returns at line 61 into the text element and the metadata.
2. Assert `metadata["stale"] is False` in place of line 62.
3. Assert `"Title" in text` in place of line 63.

### Method

- The fixture, the connection, and the FK-disabled delete stay as they are; only the returned value is read differently.

### Details

- The unpacking is the same shape the sibling stale-detection module uses (row 16), so the two modules read the pair the same way.

## Compatibility considerations

- `N/A: test-only change.`

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The missing-row case asserts the consistency state through metadata while the heading text stays asserted as display output (`AC-4`, `AC-5`).

## Out of Scope

- The metadata shape definition (`scripts/mcp_servers/mdq/mdq_models.py`, row 01).
- The read path that fills it (`scripts/mcp_servers/mdq/mdq_service.py`, row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 4 (amendment 2026-11-28) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`
