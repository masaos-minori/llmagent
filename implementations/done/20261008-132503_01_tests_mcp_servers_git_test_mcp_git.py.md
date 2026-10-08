## Goal
Repair the dry-run push test so it builds the service with an authorized remote configuration instead of patching a removed config loader (REQ-001 of the Plan).

## Scope
- Change only the dry-run push test in the git MCP service test module.

## Assumptions
- The service constructor accepts an optional configuration object; the formatter now requires it and no longer falls back to loading one.
- The test's mocked repository exposes a remote whose URL is the one to authorize.

## Design decisions
- Build the service directly with the constructor's configuration argument, authorizing the mocked remote URL; drop the patch of the removed loader.

## Alternatives considered
- Re-adding a fallback loader in production: rejected; the upstream requirement made the configuration mandatory.

## Implementation
### Target file
tests/mcp_servers/git/test_mcp_git.py

### Procedure
1. Confirm the test still patches the removed loader and calls the service built by the module's helper.
2. Construct the service with the same arguments as the helper plus an authorized configuration for the mocked remote URL, and remove the loader patch.
3. Run the test and the module.

### Method
A direct edit of the test body; the helper used by other tests is left unchanged.

### Details
The service is created with the allowed repository path, writable mode, and a configuration whose allowed remote URLs contain the mocked remote's URL; the remaining patches (repository snapshot) and assertions are unchanged.

## Compatibility considerations
- Test only; no production change.

## Security considerations
- Fake values only; no secrets.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run ruff format` and `ruff check` on the file; `uv run pytest tests/mcp_servers/git/test_mcp_git.py -q --timeout=60`.

## Completion criteria
- The test passes without patching the removed loader (REQ-001).

## Out of scope
- The module's helper and other tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Inject an authorized configuration in the test | Completed | 20261008-134340 | 20261008-134340 |  |
| 2 | Run the module | Completed | 20261008-134340 | 20261008-134340 |  |

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
- **Requirement ID**: REQ-001 (repair the dry-run push test)
- **Source issue**: issues/20261008-125417_gitmcptest01_fix-failing-git-mcp-tests-after-the-audit-record-emission-change.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-131516_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-132503
- **Related target files**: tests/mcp_servers/git/test_mcp_git.py