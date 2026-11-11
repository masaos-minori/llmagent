## Goal

Create ADR-017, the single authoritative record of MCP authentication: one shared variable per server resolved on both the Agent side and the server side, an empty token aborts startup on both sides, no bypass, changes apply only on restart, with a pending maintainer Approval statement (`REQ-003`, `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR numbering: 017 is free (`adr_00_document-guide.md` records ADR-011 as unassigned; files stop at 016).
- File naming follows the existing `adr_<group>_<NNN>_<slug>.md` convention with group `03` (mcp): `docs/10_adr/adr_02_03_017_mcp-authentication.md`.
- The authentication rules are already implemented; this ADR documents them, it does not introduce them.

## Design decisions
- Follow the `adr_02_03_012_mcp-git-server-side-write-enforcement.md` shape and the `check_adr_structure.py` section-header standard (required headings in order, conditional sections between Invariants and Verification).
- Draw wording from ADR-007 Decision 9, `mcp_06_14`, and the code (`require_auth_token`, `attach_auth_middleware`, `scripts/agent/startup_validation.py`) without copying token values.
- The Approval section carries a clearly marked pending maintainer statement, never an invented approver or date (UNK-03).

## Alternatives considered
- Extending ADR-007's decision text instead of a new ADR: ADR-007 already defers the details to a non-existent ADR; a dedicated ADR gives the rules a reviewable home. Rejected: keep ADR-007 as the pointer.

## Implementation
### Target file
`docs/10_adr/adr_02_03_017_mcp-authentication.md` (new)

### Procedure
1. Create `docs/10_adr/adr_02_03_017_mcp-authentication.md` with frontmatter (`title`, `area: governance`, `tags: [mcp]`, `related: [mcp_06_14_mcp-authentication-setup.md]`).
2. Write the required sections in the `check_adr_structure.py` order: Keywords, Status (Accepted), Summary, Context (Problem / Constraints), Assumptions, Decision (Decision Details / Scope / Out of Scope), Rationale, Alternatives Considered, Consequences, Invariants, Verification (table), Implementation Notes, Known Deviations, Review Triggers, Approval, Related ADRs, Implementation References, Completion Checklist.
3. State the rules: one `MCP_<SERVER_KEY>_AUTH_TOKEN` variable per server resolved on both the Agent side and the server side; an empty token aborts server startup (`require_auth_token` raises `RuntimeError`) and Agent startup (`startup_validation` rejects an enabled HTTP server whose `auth_token` is empty); fail-closed middleware returns 401 for an empty token; no bypass (the test-only bypass was removed in commit `cad5e91ea`); changes take effect only on restart.
4. Add an Approval section with a marked pending maintainer statement (approver, date, scope left for the maintainer).
5. Validate with `tools/check_adr_structure.py` and `tools/check_adr_authority.py`.

### Method
- Decision Details enumerate: (1) one shared secret per server, (2) resolution on both sides via `${ENV:...}` in `config/agent.toml`, (3) empty-token fail-closed abort, (4) no bypass (the test-only bypass was removed in commit `cad5e91ea`), (5) restart required, (6) tokens never logged.
- Invariants carry ADR-local `INV-NN` IDs (not global `INV-NNN`) and cite the existing tests.

### Details
- Do not copy environment-variable values or tokens into the ADR body.
- The `## Known Deviations` heading must be present (checked by `check_adr_structure.py`).
- No template instruction text (e.g. "Briefly describe") may remain in the body.

### Companion test files
N/A: this document is the ADR itself; validated by `check_adr_structure.py` and `check_adr_authority.py`.

## Compatibility considerations
- ADR-017 links to from ADR-007 (row 05) and is registered in the index, document guide, and authority model (row 06-09); the new ADR enlarges the authority graph, so add the entry and edges together and rerun `check_adr_authority.py`.

## Security considerations
- The ADR documents a security control; it must not contain token values. The fail-closed, no-bypass rules are the security substance.

## Rollback considerations
Delete the new ADR file; ADR-007 reverts to its out-of-scope line when row 05 is reverted.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `adr_02_03_017_mcp-authentication.md` | Structure | `uv run python tools/check_adr_structure.py` | Pass |
| Authority graph | Graph drift | `uv run python tools/check_adr_authority.py` | Pass |

## Completion criteria
- ADR-017 states the authentication rules and failure behavior, passes `check_adr_structure.py`, and its Approval section holds a clearly marked pending maintainer statement.

## Out of Scope
- Changing the Bearer-token mechanism itself.
- The authority-model registration (row 08) and ADR-007 link (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Draft ADR-017 with a pending maintainer approval record | Pending | — | — | Never invent an approver/date |
| 2 | Run the ADR checkers (`rules/toolchain.md`) | Pending | — | — | `check_adr_structure.py`, `check_adr_authority.py` |

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
- **Requirement ID**: `REQ-003` — a new ADR defining MCP authentication once, with failure behavior and a pending Approval statement.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `docs/10_adr/adr_02_03_017_mcp-authentication.md`
