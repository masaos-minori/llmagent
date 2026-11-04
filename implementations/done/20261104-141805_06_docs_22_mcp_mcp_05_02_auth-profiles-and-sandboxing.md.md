## Goal
- Limit the "Enforcement Point" statement of the MCP authentication document to enabled entries, so it no longer says that startup records a fatal `mcp_auth` outcome for any entry with an empty `auth_token` (`REQ-005`: documentation states the disabled-server exemption).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation only: one clause of the `**Enforcement Point:**` paragraph in `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`. The Authentication section, which already states the disabled exemption, is not edited.

## Assumptions
- The paragraph currently says Agent startup records a FATAL `mcp_auth` outcome for any `[mcp_servers.*]` entry with an empty `auth_token` (checked in Step 3a).
- The Authentication section of the same document already says the empty-token rejection at config-load time applies unless the server is disabled (`startup_mode="none"`), so the new clause matches it.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown.

## Design decisions
- Change only the `mcp_auth` clause; keep the rest of the paragraph (server-side refusal, posture report, shell sandbox statement) byte-identical.

## Alternatives considered
N/A: a bounded clause correction.

## Implementation
### Target file
`docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`

### Procedure
In the paragraph that starts `**Enforcement Point:**`, replace the clause that ends with `for any [mcp_servers.*] entry with an empty auth_token` by the clause below.

### Method
Before:

```text
and Agent startup records a FATAL `mcp_auth` outcome for any `[mcp_servers.*]` entry with an empty `auth_token`.
```

After:

```text
and Agent startup records a FATAL `mcp_auth` outcome for any enabled `[mcp_servers.*]` entry with an empty `auth_token` (a disabled entry, `startup_mode="none"`, is exempt).
```

### Details
- Do not edit the paragraphs above and below, the Authentication section, or the `Reload Boundary` paragraph.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secret or concrete configuration value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff -U0 docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` shows one changed line.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain mcp` report no findings.

## Completion criteria
- The paragraph limits the fatal `mcp_auth` outcome to enabled entries and names the disabled exemption (`AC-5`).
- The docs checkers are clean and no other text changed.

## Out of Scope
- The Authentication section, the startup and health document (separate procedure), and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the clause as described in Implementation > Procedure/Method | Completed | 20261104-165352 | 20261104-165352 |  |
| 2 | Run the documentation checkers named in the Validation plan | Completed | 20261104-165352 | 20261104-165352 |  |

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
- **Requirement ID**: `REQ-005` (documentation states the disabled-server exemption)
- **Source issue**: `issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095503_disabledauth001_disabled-server-auth-fatal.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-141805
- **Related target files**: `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`