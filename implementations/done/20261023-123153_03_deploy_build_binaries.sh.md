## Goal
Correct the `gen_launcher` comment so it no longer claims the launcher reproduces `__main__` behavior (`REQ-004`).

## Scope
- Comment lines 231-234 above `gen_launcher()` only; the generated launcher text is unchanged.

## Assumptions
- Existing comments in this script are Japanese; keep that language for consistency (the script is not under `docs/`).

## Design decisions
- State that the launcher calls `run_http()` and that the posture gate is enforced inside `run_http()`.

## Alternatives considered
- N/A: comment-only change.

## Implementation
### Target file
`deploy/build_binaries.sh`

### Procedure
1. Replace the sentence "そのエントリの __main__ で行っていた処理を再現する" with a sentence saying the launcher calls `run_http()`, whose common start path enforces the posture gate and config isolation.

### Method
- Edit only the comment; no shell logic, no heredoc content.

### Details
- Evidence: `deploy/build_binaries.sh:231-257`; the launcher template does `from <module> import <Class>` then `<Class>().run_http()`.

## Compatibility considerations
- N/A: comment-only.

## Security considerations
- N/A: comment-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `bash -n deploy/build_binaries.sh`, `uv run pytest tests/tools/test_manage_binaries.py`.

## Completion criteria
- The comment is accurate and the script still parses.

## Out of Scope
- Launcher template logic
- The `ENTRIES` table (changed by the config-isolation plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the comment change per Implementation > Procedure | Completed | 20261023-125625 | 20261023-125625 | implemented; targeted tests passed (tests/mcp_servers, startup, binaries: 2516 passed); full suite run at the end of the batch |
| 2 | Run the validation sequence (`rules/toolchain.md`): `bash -n` and the binaries tests | Completed | 20261023-125625 | 20261023-125625 |  |

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
- **Requirement ID**: `REQ-004` (launcher comment)
- **Source issue**: issues/20261023-114021_mcpstart002_posture-gate-bypassed-by-launchers-and-mdq-main.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114842_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123153
- **Related target files**: deploy/build_binaries.sh