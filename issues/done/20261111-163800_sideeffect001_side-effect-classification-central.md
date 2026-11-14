# Centralize side-effect classification and remove contradictory authority claims

## Priority
High

## Summary
Define one canonical frozen set of side-effecting tools, use it in shared dispatch, HTTP transport retry suppression, and static policy validation, and remove the contradictory routing-authority comment in `tool_constants.py`.

## Background
Source: `memo-issue.md` (Issue H), re-verified against current source on 2026-11-11.

- `Explicit in code`: `scripts/mcp_servers/dispatch.py` builds a module-level `_write_tools` set as the union of `WRITE_TOOLS`, `DELETE_TOOLS`, `GIT_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `GITHUB_WRITE_TOOLS`, `GITHUB_DANGEROUS_TOOLS`, and `SHELL_TOOLS`. `MDQ_WRITE_TOOLS` is not in the union.
- `Explicit in code`: `scripts/shared/tool_constants.py` has a comment stating that `ToolRegistry` is the canonical/fallback routing source and that live `/v1/tools` discovery is validation-only. Its own module header says the registry seed is "not a fallback", so the two statements contradict each other.
- `Documentation only` (memo): the local set decides whether idempotency and dedup apply, so a category omitted from the union becomes a keyless, non-deduplicated path.
- `Needs confirmation`: whether MDQ side-effecting tools (`index_paths`, `refresh_index`) use `dispatch_tool()` at all.

## Problem
Side-effect classification is reconstructed locally in more than one place, so a new category or tool can silently bypass dedup. The authority comments in `tool_constants.py` give opposite answers to the question of which source routes tools.

## Reason for Change
A silent omission from the dispatch union turns a side-effecting tool into an unprotected execution path (correctness and security risk), and the sibling MCP route issue needs a single classification to enforce idempotency keys. This should land first or together with it.

## Implementation Intent
- Define one canonical frozen set of side-effecting tools in the shared constants and have dispatch, transport, and policy validation import it.
- Keep `WRITE_DANGEROUS`, retry class, approval tier, and `is_write` as separate dimensions; only classification for dedup and retry suppression is unified.
- Cross-test the metadata so drift fails in CI rather than at runtime.

## Target Files or Areas
- `scripts/shared/tool_constants.py`
- `scripts/mcp_servers/dispatch.py`
- The HTTP transport module under `scripts/shared/` (actual module `Unknown`)
- `scripts/agent/tool_policy.py`
- `scripts/mcp_servers/mdq/` server and dispatch modules
- `config/mcp_dedup.toml`, `config/agent.toml` (parity checks only)
- `tests/mcp_servers/test_tool_schema_contract.py` and existing dispatch/classification tests

## Required Changes
- Define `ALL_SIDE_EFFECTING_TOOLS` as one canonical frozen set covering write, delete, execute, API-write, and side-effecting index or refresh tools that use shared dispatch.
- Replace `dispatch.py` `_write_tools` with the shared set.
- Use the same set in HTTP transport retry suppression and static policy validation.
- Add exact-equality tests between `TOOL_LIST` entries with `is_write=True` and the canonical set, with explicit approved exceptions only.
- Verify the MDQ `index_paths` and `refresh_index` dispatch path and dedup requirements, and record an explicit classification decision.
- Delete the contradictory ToolRegistry fallback comment.

## Constraints
- Do not merge classification dimensions (`is_write`, retry class, safety tier, WRITE_DANGEROUS).
- The import layer contract must hold (`PYTHONPATH=scripts uv run lint-imports`).
- No behavior change for tools already classified correctly.

## Acceptance Criteria
- One frozen set controls shared-dispatch side-effect classification.
- No side-effecting shared-dispatch tool can bypass dedup because a union omitted its category.
- `TOOL_LIST` metadata, transport behavior, dispatch behavior, and policy validation are cross-tested.
- MDQ side effects have an explicit classification and dedup decision.
- The contradictory comment is removed and the module header is the only authority statement.

## Testing Expectations
- Parity tests across all MCP servers' `TOOL_LIST`, the canonical set, `config/mcp_dedup.toml` retry classes, and `config/agent.toml` safety tiers.
- Unit tests for dispatch dedup on each category, including MDQ if applicable.
- Run `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run ruff check scripts/`, `PYTHONPATH=scripts uv run lint-imports`, and targeted pytest under `tests/mcp_servers/`.

## Documentation Impact
Update MCP dispatch and tool-safety documents under `docs/22_mcp/` to state the single classification source and its relation to the other dimensions: intent, boundaries, and Needs Confirmation items. Do not list tools or counts in docs (`skills/DESIGN.md` Docs content policy).

## Out of Scope
- Removing direct MCP routes or enforcing key presence at the request boundary.
- Changing retry classes or safety tiers themselves.
- Diagnostics or workflow recovery changes.

## Dependencies
Duplicate and overlap check (2026-11-11): no open issue duplicates this one. Overlapping items:
- `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` (overlap: partial): classify `mcp_dedup.sqlite` as a disposable cache, fail closed for non-retryable tools, and give the dispatcher and the Agent separate dedup configuration. It does not unify the side-effect tool set.
- `issues/20261110-171040_rmcompat007_history-comment-sweep.md` (overlap: partial): remove or rewrite history comments in `scripts/` and `config/`. The contradictory authority comment in `tool_constants.py` is in this issue's scope as a behavior contradiction.
- Archived `plans/done/20261027-102512_mcpinv001_mcp-write-idempotency-backstop.md` introduced the write-set backstop in dispatch; re-verify its outcome.

Ordering and other dependencies:
- Blocks `issues/20261111-163724_mcproute001_remove-direct-mcp-routes.md`: the key requirement should use this canonical set.
- `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md` changes `config/mcp_dedup.toml` ownership; re-verify retry-class parity after it lands.
- Shares the `tool_constants.py` comment cleanup with `issues/20261111-163741_rtregistry001_runtime-registry-sole-authority.md`; assign it to one of them.

## Unresolved Questions
Decisions required from the maintainer before implementation:
- Decision 1 (MDQ classification): whether `index_paths` and `refresh_index` are side-effecting for dedup purposes and must be in the canonical set. This depends on the open fact below.
- Decision 2 (dimension mapping): how Shell and ADMIN tools map independently across `is_write`, retry class, safety tier, and audit tier.

Open facts (不明):
- whether MDQ tools use `dispatch_tool()` and whether the `MDQ_WRITE_TOOLS` omission is safe.
- 不明: the actual HTTP transport module and its write-set definition.

## AI Implementation Instruction
- Change only classification constants, their consumers, and tests; keep the diff minimal.
- Preserve each dimension separately.
- Stop and report if MDQ dispatch behavior cannot be established.
- Do not implement out-of-scope items.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261111-163800
- **Related target files**: `scripts/shared/tool_constants.py`, `scripts/mcp_servers/dispatch.py`, `scripts/agent/tool_policy.py`, `scripts/mcp_servers/mdq/`, `config/mcp_dedup.toml`, `config/agent.toml`, `tests/mcp_servers/test_tool_schema_contract.py`
