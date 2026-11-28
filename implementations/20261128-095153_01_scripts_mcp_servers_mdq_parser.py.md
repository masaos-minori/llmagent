## Goal

Make `scripts/mcp_servers/mdq/parser.py` state the fence-content exclusion in its own feature list, so the module, the two tool descriptions, and the canonical MDQ document state the same subset (`REQ-001`, the fence decision stated in one place; `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

- One bullet is added to the module docstring's feature list; no parsing behavior changes.
- The plan's Phase 1 golden tests (row 08) already pin the behavior this statement describes, so this row follows them.

## Assumptions

- The documented exclusion is the plan default (plan UNK-01): fence content stays out of the searchable section body. This row states it; it does not change it, because the issue excludes behavior changes.
- The exclusion is implemented at lines 96-99 (`if in_fence:` then `continue`), so the statement describes existing behavior rather than a planned behavior.
- `tools/check_docstrings_baseline.txt` line 186 records `mcp_servers/mdq/parser.py` as `empty description`; the change adds content to the description, so the entry stays valid and the docstring gate stays green.
- The module is 9551 B, below the 24576 B gate in `tools/check_module_size.py`.

## Design decisions

- State the exclusion inside the existing feature list rather than as a new section: the feature list is the module's stated scope, and `docs/22_mcp/mcp_04_04_mdq.md` already states the same rule in its Markdown Compatibility Scope table.
- Word the bullet as the consequence for retrieval, not as an implementation note, because `AC-1` compares three sources that a client can read.

## Alternatives considered

- `N/A: docstring-only change.` Making fence content searchable is the owner decision recorded as plan UNK-01; that is a behavior change owned by another plan.

## Implementation
### Target file
`scripts/mcp_servers/mdq/parser.py`

### Procedure
1. In the Supported Markdown features list (lines 9-16), add one bullet after the fenced-code bullet (line 11) that states the section-body exclusion.

### Method

- Order: the golden tests in row 08 are written first (plan Phase 1), so this wording is checked against tests that already pin it, and the descriptions in row 02 are aligned after it (plan Phase 2).
- The wording has to match what `docs/22_mcp/mcp_04_04_mdq.md` states, so `uv run python tools/check_docs_consistency.py --domain mcp` cannot show a doc-versus-code divergence on this point.

### Details

- Wording: `- Content inside a fence is not part of the section body, so it is not indexed and not searchable.`
- The existing bullet at line 11 keeps the heading rule (`#` inside fences are not headings); the added bullet covers the body exclusion, which is the part the feature list never stated.

## Compatibility considerations

- No test asserts docstring content in this module, and `tools/check_docstrings.py` checks only the path prefix, the separator, and that the description is non-empty.
- `tests/mcp_servers/mdq/test_mdq_service.py` and `tests/mcp_servers/mdq/test_parser.py` continue to pass unchanged, which is what confirms no behavior moved.

## Security considerations

- `N/A: docstring text only.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_docstrings.py`
- `uv run pytest tests/mcp_servers/mdq/test_parser.py tests/mcp_servers/mdq/test_mdq_service.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The feature list states the section-body exclusion (`AC-1`).
- The parser statement, the two tool descriptions (row 02), and `docs/22_mcp/mcp_04_04_mdq.md` (row 06) agree on the same subset (`AC-1`).
- The four fence-language golden tests in row 08 pass, so the statement matches the behavior.

## Out of Scope

- The tool descriptions (`scripts/mcp_servers/mdq/mdq_tools.py`, row 02) and the canonical document (`docs/22_mcp/mcp_04_04_mdq.md`, row 06).
- The fence-handling loop itself: no behavior change is in scope for this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Assertions live in row 08; this row adds none |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A for this row: the documentation change is row 06 |

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
- **Requirement ID**: REQ-001 (the fence decision stated in one place), AC-1
- **Source issue**: `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-095153
- **Related target files**: `scripts/mcp_servers/mdq/parser.py`
