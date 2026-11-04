## Goal
- Correct the shutdown-guard sentence of the MCP lifecycle document, which says `start_http_subprocess()` returns immediately under shutdown, so it states that this method raises a typed suppression error while the other guarded methods still return immediately (`REQ-007`: documentation matches the corrected shutdown guard).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation only: one sentence in `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`. No other line is edited.

## Assumptions
- The current sentence reads: `_ServerLifecycleRouter._shutting_down` protects `ensure_ready()`, `start_http_subprocess()`, `restart()`, and `shutdown_idle()`: once `shutdown_all()` is called, these methods return immediately after logging a line, without delegating to `HttpServerLifecycleManager` (checked in Step 3a).
- After the production procedures, `ensure_ready()`, `restart()`, and `shutdown_idle()` still return immediately under shutdown, and `start_http_subprocess()` raises `StartSuppressedError` (declared by the router procedure).
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Keep the sentence structure and the symbol names the document already uses; change only the part that is no longer true, and add the exception for the start method.
- Do not copy a timing value or location mapping beyond what the sentence already has.

## Alternatives considered
N/A: single-sentence correction.

## Implementation
### Target file
`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`

### Procedure
Replace the one sentence that begins with the `_ServerLifecycleRouter._shutting_down` symbol with the corrected sentence below; leave the lines around it as they are.

### Method
Before:

```text
`_ServerLifecycleRouter._shutting_down` protects `ensure_ready()`, `start_http_subprocess()`, `restart()`, and `shutdown_idle()`: once `shutdown_all()` is called, these methods return immediately after logging a line, without delegating to `HttpServerLifecycleManager`.
```

After:

```text
`_ServerLifecycleRouter._shutting_down` protects `ensure_ready()`, `start_http_subprocess()`, `restart()`, and `shutdown_idle()`: once `shutdown_all()` is called, `ensure_ready()`, `restart()`, and `shutdown_idle()` return immediately after logging a line, and `start_http_subprocess()` raises a typed suppression error so a suppressed start is never mistaken for success; none of them delegates to `HttpServerLifecycleManager`.
```

### Details
- The single line is replaced; the surrounding paragraphs and the code fence above it are untouched.
- Keep the symbol names in backticks as in the original.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secret or concrete configuration value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff -U0 docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` shows exactly one removed and one added line.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain mcp` report no findings.

## Completion criteria
- The sentence says that `start_http_subprocess()` raises a typed suppression error under shutdown and that the other guarded methods return immediately (`AC-6`).
- The docs checkers are clean and no other line changed.

## Out of Scope
- Any other sentence of the document, the other two documents of the Plan, and any code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the sentence as described in Implementation > Procedure/Method | Done | 20261104 | Corrected the shutdown-guard sentence: start_http_subprocess() raises a typed suppression error; the other guarded methods return immediately. |
| 2 | Run the documentation checkers named in the Validation plan | Done | 20261104 | check_docs_quality, check_docs_structure, check_docs_content_policy --strict, check_docs_japanese, check_docs_consistency --domain mcp all clean; diff is one removed/one added line. |

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
- **Requirement ID**: `REQ-007` (documentation matches the corrected shutdown guard)
- **Source issue**: `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-095204_startretry001_startup-retry-blocked-cooldown.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-140850
- **Related target files**: `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`
