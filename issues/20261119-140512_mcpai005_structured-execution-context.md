# Introduce structured execution context for dry-run and programmatic dispatch

## Priority
High

## Summary
Replace output-string dry-run detection and keyless programmatic dispatch with one typed execution context carrying execution mode, idempotency identity, request metadata, and whether side effects were applied.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 5).

Evidence (`Explicit in code`, by reading `scripts/mcp_servers/dispatch.py`): dry-run results are recognized by a marker scan over the output text (`_is_dry_run_output`, lines 82-119, comment "UNK-01: best-effort dry-run detection"); a dry-run outcome clears durable state after the fact (lines 460-465). The claims that programmatic dispatch accepts only a tool name and arguments, and that formatters differ, are from the review and `Needs confirmation`.

## Problem
Dry-run status depends on formatter wording, so a wording change silently changes deduplication behavior and a preview may be stored as a replayable completed execution. Programmatic dispatch can bypass the `X-Idempotency-Key` contract for side-effecting tools. Both are symptoms of implicit execution semantics.

## Reason for Change
Execution mode and identity must be explicit before the handler runs; this also removes the heuristic marker list that every new formatter would otherwise extend.

## Implementation Intent
Introduce an execution context (request id, session id, idempotency key, execution mode) and structured result metadata (`side_effect_applied`, `execution_mode`). Determine `dry_run` from validated arguments before durable pending state is created. Route HTTP and programmatic entry points through the same dispatcher path. Keep human-readable formatter output separate from control metadata; do not add more output markers.

## Target Files or Areas
- `scripts/mcp_servers/dispatch.py` and the base MCP server dispatch contract (`scripts/mcp_servers/server.py`)
- Git, GitHub, and file MCP server dispatch methods
- Shared request and result DTOs (`scripts/shared/transport_dto.py`, `scripts/mcp_servers/models.py`)
- Agent workflow state handling (preview representation)
- CI/CD programmatic dispatch (named by the later Web Search and CI/CD backlog; current callers `不明`)

## Required Changes
- Add the execution context and structured result metadata; remove all output-marker dry-run parsing.
- Create no replayable durable state for previews.
- Represent preview in Agent workflow state as `previewed`, or exclude previews from applied-operation state.
- Define the execution modes preview, applied, and no-op in documentation and result metadata.
- Restrict programmatic dispatch to read-only tools unless a context with an idempotency key is supplied; require a key for every side-effecting programmatic dispatch.

## Constraints
- A real execution after a preview must not be blocked or replaced by preview output.
- Read-only programmatic callers stay compatible.

## Acceptance Criteria
- [ ] Dry-run behavior is independent of formatter output and follows one contract for file, Git, and GitHub tools.
- [ ] A preview leaves no replayable completed side-effect record; a real execution after a preview is not blocked.
- [ ] Programmatic side-effecting dispatch without a key is rejected.
- [ ] HTTP and programmatic dispatch return the same structured result contract.
- [ ] Agent workflow state does not report a preview as an applied write.

## Testing Expectations
- Parameterized dry-run tests for file, Git, and GitHub tools; formatter wording-change regression tests.
- Dry-run followed by real execution; keyless and keyed programmatic dispatch; read-only compatibility.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Document the execution-context contract and failure behavior (final sweep in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Out of Scope
- Dedup storage state machine (`issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`); key generation and replay (`issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`); GitHub retry policy (`issues/20261119-140513_mcpai006_github-write-retry-policy.md`).

## Dependencies
- Depends on `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md` (published `dry_run` schema), `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (durable-state behavior), and `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md` (propagated key). Do not finalize programmatic side-effecting dispatch before the key contract exists.
- Blocks `issues/20261119-140516_mcpai009_file-mcp-hardening.md` and `issues/20261119-140517_mcpai010_github-http-contract-tests.md`.

## Unresolved Questions
- `不明`: which programmatic dispatch callers exist today (not enumerated in this session).
- `不明`: how a preview is represented across servers that do not support `dry_run`.

## AI Implementation Instruction
Replace marker detection rather than extending it. Keep formatter output untouched except where metadata is moved out. Write the formatter-wording regression test first; stop and report if a caller of programmatic dispatch cannot supply a key.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140512
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `scripts/mcp_servers/server.py`, `scripts/mcp_servers/models.py`, `scripts/shared/transport_dto.py`
