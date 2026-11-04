## Goal
- Correct the `mcp_auth` bullet of the startup and health document so it states that the check applies to enabled servers and exempts disabled ones, and no longer calls the check unreachable through a real `McpServerConfig` (`REQ-005`: documentation states the disabled-server exemption and does not call the check unreachable).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation only: the first two sentences of the `mcp_auth` bullet in the severity-mapping notes of `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`. The third sentence (about `check_services()` and short-circuiting) is not edited here: the Plan for configuration-only validation corrects it.

## Assumptions
- The bullet currently says the check is FATAL if any `[mcp_servers.*]` entry has an empty `auth_token`, and that in practice it is unreachable via a real `McpServerConfig` because construction rejects an empty token (checked in Step 3a).
- Configuration construction accepts an empty `auth_token` for a disabled server (`startup_mode` none), so the check can fire for a real configuration only for an enabled server built some other way, and a disabled server is exempt after the production change.
- The document is also targeted by two other Frozen Plans (configuration-only validation order, interrupted-startup exit status); they edit different text, and the sequencing is recorded in the Plan.
- Step 2 start conditions held: the Plan is not gated and has no blocking Unknown.

## Design decisions
- Replace only the two sentences that are no longer true, keep the bullet's lead-in (`"1b. MCP authentication check"`, runs before the readiness check) and the link to `mcp_06_01`, and leave the rest of the bullet byte-identical.
- State the exemption and its reason (the configuration contract), not a file location.

## Alternatives considered
N/A: a bounded text correction.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
In the bullet that starts `` - `mcp_auth` ("1b. MCP authentication check" ``, replace the text from `FATAL if any` through `than the normal config-load path.` with the text below; leave the sentence that begins `` `check_services()` does not short-circuit `` and everything after it unchanged.

### Method
Before:

```text
FATAL if any `[mcp_servers.*]` entry has an empty `auth_token`, listing every offending server key in one outcome. In practice this is unreachable via a real `McpServerConfig` — construction itself already rejects an empty `auth_token` (see [mcp_06_01](../22_mcp/mcp_06_01_configuration-file-inventory.md)) — so this check only fires for a `ctx` assembled some other way than the normal config-load path.
```

After:

```text
FATAL if any enabled `[mcp_servers.*]` entry (`startup_mode` other than `none`) has an empty `auth_token`, listing every offending enabled server key in one outcome. A disabled entry is exempt, because configuration construction accepts an empty `auth_token` for it. For an enabled entry the check is a defense in depth: construction itself already rejects an empty `auth_token` (see [mcp_06_01](../22_mcp/mcp_06_01_configuration-file-inventory.md)), so it only fires for a `ctx` assembled some other way than the normal config-load path.
```

### Details
- Keep the relative link target exactly as it is.
- Do not edit the neighbouring bullets, the table above them, or the sentence about short-circuiting.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secret or concrete configuration value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff -U0 docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` shows one changed line (one removed, one added) for this bullet.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain agent` report no findings.

## Completion criteria
- The bullet states that disabled servers are exempt and that the check applies to enabled entries, and it no longer says the check is unreachable (`AC-5`).
- The docs checkers are clean and no other sentence changed.

## Out of Scope
- The short-circuit sentence, the other overlapping Plans' edits to this document, the MCP authentication document (separate procedure), and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the sentences as described in Implementation > Procedure/Method | Pending | — | — | |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — | |

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
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
