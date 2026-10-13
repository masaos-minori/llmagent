## Goal
- Update ADR-007's verification entry and Known Deviations for the new Bearer enforcement, and cite the new tests (REQ-007).

## Scope
- In: the INV-09 `Verifies` line, a new Test entry for the Bearer checks, and the Known Deviations body.
- Out: decisions, invariants, exceptions, and approval records (no change of design).

## Assumptions
- Apply after Steps 3-7; the three new test files (rows 29-31) exist, because `check_adr_reference`/`check_adr_invariant_matrix` verify cited paths.
- ADR size: the file is about 20 KB against the 24576-byte ceiling; the additions are small.

## Design decisions
- Keep INV-09's wording; only the verification evidence changes.
- Known Deviations becomes exactly `Not applicable` (governance_01: a required section with nothing to say).

## Alternatives considered
N/A: the edit follows from the Known Issue removal.

## Implementation
### Target file
`docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md`

### Procedure
1. Edit the `Verifies` line of the bind test.
2. Add a Test entry after that bind test block.
3. Replace the Known Deviations body.

### Method
- The bind test block (lines 304-310) ends with its `Implementation` line; the new entry follows it after one blank line, in the same bullet format.

### Details
Change A — the bind test's `Verifies` line (Before/After):

```markdown
# Before:
  - **Verifies**: INV-09 (partial: loopback bind only; see MCP-001 for the Bearer check)
# After:
  - **Verifies**: INV-09 (loopback bind)
```

Change B — add after the bind test block (new entry, same format as its neighbors):

```markdown
- **Test**: Each of the shell, github, and file-read/write/delete servers rejects a request without a matching Bearer token (401) and refuses to start with an empty token
  - **Verifies**: INV-09
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/mcp_servers/shell/test_shell_server_auth.py`, `tests/mcp_servers/github/test_github_server_auth.py`, `tests/mcp_servers/file/test_file_server_auth.py`
```

Change C — Known Deviations body (Before/After):

```markdown
# Before:
- Known Issue MCP-001: the shell, github, and file MCP servers register no Bearer-token authentication middleware (INV-09).
# After:
Not applicable
```

## Compatibility considerations
- Documentation only; the rest of the ADR and its numbering are unchanged.

## Security considerations
N/A: documentation of an existing invariant.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_known_deviation_sync.py`, `check_docs_structure.py`, `check_docs_quality.py`.

## Completion criteria
- ADR-007 carries no MCP-001 reference; the Bearer enforcement test entry cites the three new test files; the checkers pass.

## Out of scope
- Approval records and any change to INV-09's text or exceptions (the web-search loopback `/health` wording belongs to `mcp006`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply changes A, B, and C | Pending | — | — | Plan Step 8; after Steps 3-7 and rows 29-31 |
| 2 | Run the ADR and documentation checkers | Pending | — | — |  |

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
- **Requirement ID**: `REQ-007` (ADR-007 Known Deviations and INV-09 verification match the new behavior)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md
