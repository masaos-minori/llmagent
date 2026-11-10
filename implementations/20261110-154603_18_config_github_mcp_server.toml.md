## Goal
Annotate the shipped `path_denylist = []` so a reader knows the empty value is a deliberate, registered ADR-004 exception and not a missed setting (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit


## Assumptions
- `path_denylist = []` is at `config/github_mcp_server.toml:28` with a one-line comment at line 27; the shipped value must stay empty (rejecting it would make the shipped configuration unstartable, Plan Background).
- The maintainer's rationale text is pending (UNK-01); this document does not write or invent it. The annotation only states that the empty value is a registered exception and points to ADR-004.

## Design decisions
- Add one comment line above `path_denylist = []` of the form `# Empty is the registered ADR-004 exception (rationale: see the ADR-004 exception record, pending maintainer statement).`; the value line is unchanged.

## Alternatives considered
Making the comment carry the rationale was rejected (maintainer owns the text). Removing the key was rejected (would hide the exception).

## Implementation
### Target file
`config/github_mcp_server.toml`

### Procedure
- Insert the comment line between the existing description comment (line 27) and `path_denylist = []` (line 28).

### Method
- Comment-only edit; TOML value and key order unchanged.

### Details
- Confirm the file still parses: `GitHubConfig.load()` is exercised by `tests/mcp_servers/github/test_github_health_posture.py` (shipped-config case).

## Compatibility considerations
No behavior change; comment only.

## Security considerations
No change; documents an accepted, registered exception.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_security_validation.py tests/mcp_servers/github/test_github_health_posture.py -v`
- `uv run python -c "import tomllib,sys;tomllib.load(open('config/github_mcp_server.toml','rb'))"` parses

## Completion criteria
- `path_denylist = []` carries the ADR-004 exception comment and the file still loads.

## Out of Scope
- The ADR-004 exception record and its rationale (document row for `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, gated on the maintainer's statement).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the exception comment above `path_denylist = []` | Pending | — | — | |
| 2 | Run the github tests and the TOML parse check | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (annotate `path_denylist = []` as the registered ADR-004 exception)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `config/github_mcp_server.toml`
