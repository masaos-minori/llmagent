# Implementation Procedure: Rename the anti-loop assertions and field list in `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`

## Goal

Rename all key occurrences in the rag_pipeline MCP service tests so the adapter anti-loop pin
assertions and the config-field list check run against the renamed field with identical
semantics (REQ-004, REQ-006, AC-3).

## Scope

- Six occurrences on five lines (verified 2026-10-27): assertion `assert ns.rag_service_url ==
  ""` at L37; test name `test_rag_service_url_always_empty` at L76; comment naming the key at
  L77; assertion at L80; the expected-field-list entry `"rag_service_url"` at L119; assertion
  `assert adapter.rag_service_url == ""` at L148.
- No assertion-value or logic edits: every pinned value stays `""`.

## Assumptions

- Phase 3 row: land after the scripts renames (rows 01-07), specifically the
  `build_rag_cfg_adapter()` pin rename in `rag_pipeline_models.py` (row 06) — the adapter
  keyword and these assertions must carry the identical new name.
- Renaming the test function name is name-only (AC-6); the Plan does not pin this test's node
  ID, and no doc links to it.

## Design decisions

- Rename the test function `test_rag_service_url_always_empty` to
  `test_rag_query_service_url_always_empty` (new): leaving an old-spelling identifier in
  `tests/` would violate AC-1's zero-standalone-occurrence gate.

## Alternatives considered

- Keeping the test name unchanged — rejected: AC-1 greps all of `tests/` for the token.

## Implementation
### Target file

`tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`

### Procedure

1. Rename the attribute access `ns.rag_service_url` at L37 (verified) to the new spelling
   `rag_query_service_url` (new).
2. Rename the test function `test_rag_service_url_always_empty` (L76, verified) to
   `test_rag_query_service_url_always_empty` (new).
3. Rename the key named in the L77 comment ("... must always be \"\" to prevent HTTP loop in
   MCP process").
4. Rename the attribute access at L80 (verified).
5. Rename the field-list entry `"rag_service_url"` at L119 (verified) to the new spelling; the
   list is an expected-config-surface inventory, order unchanged.
6. Rename the attribute access `adapter.rag_service_url` at L148 (verified).

### Method

Mechanical token renames; pinned values (`""`) and list order unchanged.

### Details

- `rag_pipeline_service_url` appears elsewhere in this file (MCP server config surface) and
  must stay untouched (REQ-003).

## Compatibility considerations

- Test-only change; anti-loop contract semantics identical (AC-3).

## Security considerations

- N/A: the anti-loop guard assertion itself is preserved.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` — anti-loop
  assertions green after row 06 lands (Plan Validation row).
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: zero standalone old-spelling occurrences in this file; AC-3: adapter pin assertions
  still yield `""`.

## Out of Scope

- `rag_pipeline_models.py` pin rename (own procedure document) and all other rename rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 3 row; land after Phase 2 rows 01-07 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: rename only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-004, REQ-006
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py
