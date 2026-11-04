## Goal
- State in the MCP subprocess startup document that the runtime restart cooldown does not apply to the startup retry and that a start suppressed by shutdown ends startup as an interrupted start instead of being retried (`REQ-007`: documentation matches the corrected retry behavior).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation only: one added paragraph in `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md`. The existing retry-once-then-`[fatal]` paragraph is not edited, and no timing value is added.

## Assumptions
- The paragraph that starts `On failure, McpServerStarter` describes the retry after a fixed delay and the `[fatal]` error, and does not mention the cooldown (checked in Step 3a).
- The behavior the new text states is the one the production procedures create: the router's start entry ignores the cooldown, and a start suppressed by shutdown surfaces as `StartupInterrupted`.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Add a new paragraph right after the existing retry paragraph instead of editing it, so the existing description stays byte-identical and the diff has added lines only.
- Describe the behavior without symbol names or file locations, following the docs content policy.

## Alternatives considered
N/A: single added paragraph; no concrete timing value is copied (`skills/DESIGN.md`).

## Implementation
### Target file
`docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md`

### Procedure
1. Find the paragraph that starts `On failure, ` and ends with the `(Explicit in code — ` evidence label.
2. Insert the new paragraph, with one blank line before and after it, directly after that paragraph.

### Method
Add exactly this paragraph (English):

```text
The runtime failure cooldown, which throttles automatic restarts after a failed start, does not apply to this startup retry: the second attempt is a genuine launch attempt. A start that is suppressed because shutdown has begun ends startup as an interrupted start and is not retried.
```

### Details
- Do not edit any other paragraph, and do not add a port, a timeout, or a retry-count value.
- Keep the file's front matter and heading structure unchanged.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secret or concrete configuration value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff -U0 docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` shows added lines only.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain mcp` report no findings.

## Completion criteria
- The document states that the runtime restart cooldown does not apply to the startup retry and that a shutdown-suppressed start is an interrupted start (`AC-6`).
- The existing retry paragraph is unchanged and the docs checkers are clean.

## Out of Scope
- Any other section, the other two documents of the Plan, and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the paragraph as described in Implementation > Procedure/Method | Pending | — | — | |
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
- **Requirement ID**: `REQ-007` (documentation matches the corrected retry behavior)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md`
