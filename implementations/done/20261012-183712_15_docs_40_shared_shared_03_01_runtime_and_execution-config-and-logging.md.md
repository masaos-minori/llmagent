## Goal
- Drop the browser token from the list of secret fields that use the environment-reference convention (`REQ-005`)

## Scope
- The environment-variable secret references paragraph in `docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md`.

## Assumptions
- Lightweight fill: change one phrase in English.

## Design decisions
- Say that every auth_token field uses the convention; the other claims in the paragraph stay.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md`

### Procedure
1. Replace the phrase naming the auth_token and browser token fields with every auth_token field.

### Method
- Keep the paragraph otherwise unchanged.

### Details
- Do not reflow the paragraph.

## Compatibility considerations
Documentation only.

## Security considerations
N/A: documentation only; no token values are written.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- The documentation checkers named in `routing.md` Tools "When to run which tool" for an edited docs file (quality, structure, content policy, the consistency check for the mcp or deployment domain, and the English-only check).
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The paragraph no longer mentions the browser token and the checkers pass.

## Out of scope
- Other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the paragraph | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md |
| 2 | Run the documentation checkers | Completed | 20261012-184531 | 20261012-184531 | documentation checkers pass |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: docs/40_shared/shared_03_01_runtime_and_execution-config-and-logging.md