## Goal
- Reconcile the `required_capability` identifiers in `config/tool_catalog.toml` with the canonical capability model, declare the optional `github.api` capability, and remove the deferred-reconciliation note (REQ-005, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the catalog data file only.
- Out of scope: the discovery code that reads it (seq 09); the test file is covered by seq 26.

## Assumptions
- Verified in Step 3a: the header note (`tool_catalog.toml:18-20`) defers the canonical schema to cliplc008 — this Plan; the GitHub section (`:113-138`) declares `capabilities = ["github.operations"]` and `required_capability = "github.operations"`.
- Identifiers follow `docs/22_mcp/mcp_08_tool_capability_naming_convention.md` (`{domain}.{action}`); existing values (`filesystem.read`, `rag.pipeline`, `shell.execution`, `github.operations`) already match the convention, so reconciliation means confirming them and adding `github.api` as an optional capability for the GitHub server.

## Design decisions
- The catalog declares the optional capability list per server; required-ness is derived by the Agent from `required_capability` on a `required=true` server (D-6), so no new key is added.

### Corrections made in Step 3b
- Corrected in Step 3b: the header note replacement is written as three lines. `tools/check_config_comment_length.py` grandfathered the block at line 1 with 23 consecutive comment lines, and an entry whose length or position no longer matches is error-level, so the replacement cannot change the block's length.
- Corrected in Step 3b: no consumer reads the catalog `capabilities` list at runtime. The drift check reads `owned_tools`, and the capability classification reads the live `/health` block while the catalog supplies only `required_capability` through `shared.tool_catalog.required_capability_for()`. The added entry is the declared canonical set for GitHub, so it changes no behavior; the reconciliation is recorded in the docs update (seq 38).

## Alternatives considered
- N/A: data-only change.

## Implementation
### Target file
`config/tool_catalog.toml`

### Procedure
1. Replace the header note (`:18-20`) with a statement that these identifiers are the canonical capability model per this Plan.
2. Add `github.api` to the GitHub server's `capabilities` list (`:137`); `required_capability` stays `github.operations`.

### Method
- No other server's identifiers change; the reconciliation is a confirmation pass, recorded in the docs update (seq 38).

### Details
- `deploy.sh` copies `config/*.toml` individually, so the file must be synced at deploy (Plan Phase 6).

## Compatibility considerations
- The catalog is read at every discovery; adding a capability entry changes only the GitHub server's declared set.

## Security considerations
- N/A: catalog data; capability identifiers only, no credential values.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py` (catalog-driven cases added by seq 26); `uv run python tools/check_config_comment_length.py` (the header comment block must stay within the 5-line threshold); no other code gate applies to the data file itself.
- Ran: `check_config_comment_length.py` reports 0 errors and the catalog block is still the grandfathered one (line 1, 23 consecutive comment lines), so the replacement kept the block's recorded length. `tests/agent/services/test_mcp_tool_discovery.py` 96 passed with 6 failures, all the seq 09 report-based-proof fallout cases that seq 26 repairs; `tests/integration/test_standard_config_integration.py` passes, including the test that every catalog entry still declares `required_capability` and `owned_tools`. Full suite pending at end of batch.

## Completion criteria
- The note is removed, `github.api` is declared as optional for GitHub, and the discovery tests that read the catalog pass.

## Out of Scope
- Per-tool optional capabilities for other servers (UNK-01, follow-up).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the catalog change | Completed | 20261126-192857 | 20261126-192857 | Changed file: config/tool_catalog.toml. The header note is replaced by the canonical capability model statement written as three lines, so the grandfathered block (line 1, 23 consecutive comment lines) keeps its recorded length and position. github.api added to the GitHub server's capabilities; required_capability stays github.operations. No code path reads the catalog capabilities list, so behavior is unchanged. |
| 2 | Tests are covered by the test-file procedure (seq 26) | Completed | 20261126-192857 | 20261126-192857 | No test file in this row; the catalog-driven cases are seq 26. Ran tests/agent/services/test_mcp_tool_discovery.py: 96 passed, 6 failures are the seq 09 report-based-proof fallout cases seq 26 repairs. tests/integration/test_standard_config_integration.py passes, including the test that every catalog entry declares required_capability and owned_tools. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-192857 | 20261126-192857 | check_config_comment_length.py: 0 errors, the catalog block still matches its grandfathered entry. Reference table no drift; 75 cited ADR tests pass. Full suite pending at end of batch. Docs: N/A, the docs rows for this module are seq 33-38; seq 38 records the identifier reconciliation. Deploy: the file must be synced by deploy.sh (Plan Phase 6). |

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
- **Requirement ID**: `REQ-005` (catalog identifiers reconciled), `REQ-006` (optional `github.api` declared)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `config/tool_catalog.toml`