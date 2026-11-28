## Goal

Make the `search_docs` and `grep_docs` descriptions state the supported Markdown feature subset and the fence-search exclusion, so the descriptions agree with what the parser does and what the canonical document states (`REQ-001`, the fence decision stated in one place; `AC-1`).

## Scope
**Release unit**: N/A: not part of a release unit

- Two `description` strings change; no `inputSchema` field, no `status`, and no handler behavior changes.
- The golden tests in row 08 pin the behavior these descriptions state, so this row states a pinned fact rather than a claim.

## Assumptions

- No test asserts the description text: `tests/mcp_servers/mdq/test_mdq_tool_schema.py` compares schema values, and no module in `tests/mcp_servers/mdq/` references a description string (checked at current HEAD).
- The feature subset is the parser's documented one, so the wording is taken from `scripts/mcp_servers/mdq/parser.py`'s feature list (row 01) and from `docs/22_mcp/mcp_04_04_mdq.md` (row 06), not invented here.
- `status` stays `production` for all 7 tools, as `tests/mcp_servers/mdq/test_mdq_metadata_consistency.py` pins it (plan AC-2 and Design).

## Design decisions

- State the subset in the description rather than adding a schema field: `McpTool.status` has no closed vocabulary (`scripts/mcp_servers/models.py:244`) and `validate_tool_schema_v2()` validates the other vocabularies only (`scripts/shared/resource_scope.py:248`), so a field change would need the contract owner (plan UNK-04).
- Keep the description one sentence plus the scope clause, so the wording stays readable in a client tool list.

## Alternatives considered

- `N/A: text-only change confined to two fields.` An alternative that changes what the tools accept is a behavior change, which the issue excludes.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_tools.py`

### Procedure
1. Rewrite the `search_docs` description (line 16) to name the supported subset and state that content inside a fence is not searchable.
2. Rewrite the `grep_docs` description (line 234) with the same subset and the same exclusion.

### Method

- Wording is shared between the three sources so `AC-1` can be checked by reading them: "ATX headings and fenced code blocks; the searchable text is the section body, and content inside a fence is not part of it."
- Order: row 08's golden tests first, then row 01's parser statement, then these descriptions (plan Phases 1 and 2).
- Module size 10884 B, below the 24576 B gate; `tools/check_docstrings_baseline.txt` line 185 records this module as `missing separator`, which this change does not touch.

### Details

- `search_docs`: replace `"Search indexed Markdown documents using BM25/FTS5. Markdown-only, structure-aware retrieval."` with the subset sentence plus the fence clause.
- `grep_docs`: replace `"Search Markdown chunks with a regex pattern. Structure-aware, Markdown-only."` with the same subset sentence plus the fence clause, keeping the regex-pattern statement.
- `grep_docs` matches against the indexed chunk text, so the fence clause applies to it as well: fence content never enters the chunk text.

## Compatibility considerations

- Clients that read the description as free text are unaffected; no schema key is added or renamed.
- `tests/mcp_servers/mdq/test_mdq_tool_schema.py` and `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` continue to pass, which is what confirms the schema and metadata are unchanged.

## Security considerations

- `N/A: description text only.` No path, scope, or authorization field is touched.

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_parser.py tests/mcp_servers/mdq/test_mdq_service.py` — the golden parity the plan names for this row (`AC-1`)
- `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_schema.py tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- Both descriptions name the same subset the parser feature list names, and both state that fenced content is not searchable (`AC-1`).
- A token that appears only inside a fence is not returned by `search_docs`, so the description's claim is the pinned behavior (`AC-1`).

## Out of Scope

- The parser feature list (row 01) and the canonical document section (row 06).
- Any status, tier, or schema field change, which the plan records as an owner decision (UNK-04).

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
- **Related target files**: `scripts/mcp_servers/mdq/mdq_tools.py`
