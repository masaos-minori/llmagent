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

## Completion criteria
- The note is removed, `github.api` is declared as optional for GitHub, and the discovery tests that read the catalog pass.

## Out of Scope
- Per-tool optional capabilities for other servers (UNK-01, follow-up).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the catalog change | Pending | — | — | |
| 2 | Tests are covered by the test-file procedure (seq 26) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
