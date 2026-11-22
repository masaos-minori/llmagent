## Goal

Add the server-owned `[dedup]` table so this process configures the shared dedup store through its own file (REQ-001).

## Scope
**Release unit**: dedup-config-isolation-core (shared-store config isolation, store-identity gate, and operational reference removal)

## Assumptions
- Values must be byte-identical in all ten `config/*_mcp_server.toml` files: the store fingerprint gate (seq 02 `identity_mismatch`) fails closed on accidental divergence, and intentional divergence is out of scope (plan UNK-04).
- Omit `pending_timeout_minutes` so the loader default (10) keeps the effective config — and therefore the computed fingerprint — identical to the store installed from the current shared file.

## Design decisions
- Table content mirrors the current `config/mcp_dedup.toml` `[dedup]` table exactly; no `[retry_class]` mirror is copied (REQ-005 removes it).

## Alternatives considered
- Per-server value tuning: rejected for this plan (UNK-04); divergence would change the fingerprint and refuse the shared store.

## Implementation
### Target file
`config/cicd_mcp_server.toml`
### Procedure
1. Append the table (exact values below) at the end of the file with a one-line comment naming the shared store owner:

```toml
[dedup]
db_path = "/opt/llm/db/mcp_dedup.sqlite"
retention_days = 14
lease_seconds = 30
max_attempts = 3
```
### Method
Text append only; the loader (`load_dedup_section()`, seq 01) validates it at bootstrap (seq 04).
### Details
- No existing key is moved or renamed; the rest of `cicd_mcp_server.toml` is untouched.

## Compatibility considerations
- Until Phase 2 bootstrap lands, this table is simply unread: harmless. After Phase 4 (seq 23) removes the shared file, it is the only source.

## Security considerations
- `db_path` stays inside the dedup database directory contract (`/opt/llm/db/`); the loader rejects anything else (REQ-006).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/cicd/ -q` (opt-in `isolated_dedup` fixtures unaffected); full-suite `uv run pytest -q`; bootstrap integration asserts come from seqs 04/35.

## Completion criteria
- `cicd_mcp_server.toml` parses with the four-value `[dedup]` table identical across all ten server files; the process opens the store through it after Phase 2.

## Out of Scope
- Retry classification config (removed, REQ-005); per-server semantics divergence (UNK-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `[dedup]` table | Completed | 2026-11-22 | 2026-11-22—[dedup] appended, byte-identical across the ten files (3-line owner comment instead of one-line)|
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22—tests/mcp_servers suite green with table present|

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
- **Requirement ID**: REQ-001; AC-002
- **Source issue**: issues/20261120-115842_mcpdl003_dedup-config-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-172154_mcpdl003_dedup-config-isolation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-192909
- **Related target files**: `config/cicd_mcp_server.toml`
