## Goal

Classify `tests/mcp_servers/mdq/test_parser.py` as `characterization` and add the fence golden tests for Python, JSON, shell, and Mermaid blocks, so the heading rule and the section-body exclusion are pinned before any wording change (`REQ-001`, `REQ-003`; `AC-1`, `AC-3`).

## Scope
**Release unit**: mdq-taxonomy-gate

- One `pytestmark` line and four golden tests; the two existing tests are unchanged.
- The search-exclusion golden stays in `tests/mcp_servers/mdq/test_mdq_service.py:665`, which is not a target of this row.

## Assumptions

- The module has no `pytestmark` today and already imports `pytest` (line 18), so `add_import` is `false` in the records file.
- The module already carries an accepted citation through the Canonical Source Registry path `scripts/mcp_servers/` named in its docstring; as a characterization module it needs no citation for `AC-3` anyway.
- Golden values are inline literals, following the repository precedent (`tests/rag/ingestion/test_chunk_utils.py:129`, `tests/tools/test_tool_report_output.py:183`); no fixtures directory is introduced.
- The existing `service` fixture (lines 26-37) is reused, because `parse_markdown()` needs a service with `allowed_dirs` and a temp DB path.
- The four fence languages are the ones the plan names; a fifth language is not added, so the pinned set matches `AC-1`.

## Design decisions

- Classify as `characterization` rather than `contract`: the tests pin observed behavior ahead of a possible owner decision about fence search (`UNK-01`), so a change of the documented semantics flips these tests, which is the characterization case; only the characterization section is report-only in the CI report step (`AC-6`).
- Keep the golden tests in this module rather than in `tests/mcp_servers/mdq/test_mdq_service.py`, so the parser-level assertion (section body content) stays separate from the search-level assertion in the service module.
- Assert the parsed section content against a literal string, not against a computed value, so a change to the accumulation loop is caught rather than mirrored.

## Alternatives considered

- Assert the search exclusion here: rejected, the search-level golden already exists in `tests/mcp_servers/mdq/test_mdq_service.py:665` and duplicating it would create two pins for one behavior.
- Classify as `contract`: rejected, the plan's `AC-1` names these as golden pins of current behavior, and the classification rule reserves `contract` for assertions that trace to a requirement source; the citation here is a registry path, not a requirement clause.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_parser.py`

### Procedure
1. Add `pytestmark = pytest.mark.characterization` after the module-level import block (imports end at line 21), through `tools/apply_test_taxonomy_markers.py`.
2. Add one golden test per fence language (Python, JSON, shell, Mermaid) that asserts the section content excludes the fence body and that a `#` line inside the fence does not create a section.

### Method

- Write the records file with one record for this module: `path`, `pytestmark` as `characterization`, `tests` empty, `add_import` `false`; run `uv run python tools/apply_test_taxonomy_markers.py RECORDS.json --dry-run` before applying, which is the path the plan's Phase 4 uses for all 38 modules.
- Land the marker in the same commit as the classified-area addition (the `mdq-taxonomy-gate` release unit), so `tools/check_test_taxonomy.py` reports no `unclassified-module` finding for the area.
- Order: this row is plan Phase 1, so the pins exist before the parser feature list (row 01) and the tool descriptions (row 02) restate the behavior.

### Details

- Each golden test writes one Markdown file with an H1, a fence of its language containing a `#` line and a unique token, and text after the fence; the assertion compares the section content with an inline literal and asserts the heading list contains only the H1.
- The four languages are covered by one test each rather than a parametrized table, so each golden string stays readable as a literal.
- The existing `TestFrontmatterInvalidYamlSyntax` tests continue to pass unchanged, which is what confirms the marker is the only change to them.

## Compatibility considerations

- The module is inside `tests/mcp_servers/mdq/`, which becomes a classified area through row 05; before row 05 lands the checker treats this module as unclassified with no finding, so the marker alone is safe to land earlier.
- `tests/mcp_servers/mdq/` has no `__init__.py`, so the module is imported as `tests.mcp_servers.mdq.test_parser` as it is today.
- A characterization failure is report-only in the CI report step (`AC-6`); the tests must not be relied on as a blocking gate until the fence semantics are agreed.

## Security considerations

- `N/A: test content only.` No authorization, path, or scope behavior is asserted.

## Rollback considerations

- `N/A: revert the commit.` The pins add no persisted state.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_parser.py` — the four golden tests pass (`AC-1`)
- `uv run python tools/check_test_taxonomy.py` — no finding for this module (`AC-3`)
- `uv run python tools/apply_test_taxonomy_markers.py RECORDS.json --dry-run` — the record validates before writing
- Full sequence per `rules/toolchain.md`, including the diff-scoped coverage gate at the 90 percent threshold.

## Completion criteria

- The module carries exactly one taxonomy marker, `characterization` (`AC-3`).
- The four golden tests pass: a `#` inside a fence is not a heading, and fence content is not part of the section body (`AC-1`).
- The tests assert the documented semantics, so a fence-search change flips them rather than leaving them silently green.

## Out of Scope

- The parser feature list wording (`scripts/mcp_servers/mdq/parser.py`, row 01) and the tool descriptions (row 02).
- The search-exclusion golden in `tests/mcp_servers/mdq/test_mdq_service.py:665`.
- `tools/check_test_taxonomy.py`'s classified-area list (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1 pins, Phase 4 marker (release unit) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | The "Add or update tests" step does not apply: this row is the test module itself |

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
- **Requirement ID**: REQ-001 (the fence decision pinned by golden tests), REQ-003 (machine-readable test classification), AC-1, AC-3
- **Source issue**: `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-095153
- **Related target files**: `tests/mcp_servers/mdq/test_parser.py`
