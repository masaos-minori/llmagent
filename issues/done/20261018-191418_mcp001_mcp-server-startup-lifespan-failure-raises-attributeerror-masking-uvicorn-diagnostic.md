# MCP server startup lifespan failure raises AttributeError masking uvicorn diagnostic

## Priority
High

## Summary
The `_LoopbackVerifyingServer.startup()` override in the MCP server base class accesses `self.servers` unconditionally after calling `super().startup()`. When the FastAPI app's lifespan startup fails, uvicorn returns early without setting `self.servers`, so the override raises `AttributeError` instead of surfacing uvicorn's own "Application startup failed. Exiting." diagnostic. Fix the override so a failing lifespan produces a clear startup failure rather than an `AttributeError`.

## Background
`scripts/mcp_servers/server.py` defines `MCPServer.run_http()`, which launches every MCP server via uvicorn. It wraps `uvicorn.Server` in a subclass named `_LoopbackVerifyingServer` whose `startup()` override verifies that the actual bound socket address is loopback right after uvicorn starts. uvicorn 0.49.0's `Server.startup()` calls the ASGI lifespan startup first; if the lifespan requests exit (`should_exit` becomes True), `Server.startup()` returns early and does NOT assign `self.servers`. `Server.__init__` also never initializes `self.servers`. Only servers that define a FastAPI lifespan can therefore hit the early-return path. Of the MCP servers, `rag-pipeline-mcp` defines a lifespan (`_lifespan`) that awaits `RagPipelineMCPService.start()`, which initializes HTTP/DB resources and can raise.

## Problem
When a server whose lifespan startup fails reaches `run_http()`, the sequence is:
1. uvicorn logs its own clean diagnostic: `ERROR: Application startup failed. Exiting.`
2. `super().startup()` returns with `should_exit=True` and leaves `self.servers` unset.
3. The override's `for srv in self.servers:` raises `AttributeError: '<server>' object has no attribute 'servers'`.
4. The `AttributeError` propagates out of `run_http()` (only `KeyboardInterrupt` is caught) and out of the server's `__main__`, producing an unhandled traceback and exit code 1.

The real cause (lifespan/resource initialization failure) is masked behind an `AttributeError` about a missing attribute, making startup failures hard to diagnose.

## Reason for Change
The RAG pipeline server's lifespan can legitimately fail at startup (embedding/LLM endpoint unreachable, DB missing, invalid config). Every such failure currently surfaces as an `AttributeError` rather than uvicorn's diagnostic. This is a startup-failure diagnosis regression with no functional upside — the process still exits, but the operator gets the wrong error.

## Implementation Intent
Guard the socket-address verification in `_LoopbackVerifyingServer.startup()` so it only runs when the server actually started serving. Skip the verification whenever uvicorn requested exit or has not yet assigned `self.servers`. The loopback-only bind verification must remain intact for the normal start path. Describe the fix as a guard on the early-exit / unset-`self.servers` case, not as a change to the loopback policy.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (`_LoopbackVerifyingServer.startup`, `MCPServer.run_http`)
- `tests/mcp_servers/test_mcp_server_base.py` (add coverage for the failing-lifespan path)
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` (lifespan that can fail at startup)

## Required Changes
- Guard the socket iteration in `_LoopbackVerifyingServer.startup()` so it returns early when `self.should_exit` is True or `self.servers` is not yet set (e.g. `if self.should_exit or not getattr(self, "servers", None): return`), preserving the loopback verification for the normal start path.
- Add a unit test that drives `run_http()` (or the override) with a FastAPI app whose lifespan raises during startup and asserts the process fails without raising `AttributeError` (the diagnostic is uvicorn's own, not an `AttributeError`).
- Optionally add a regression test asserting a normal loopback start still performs the post-start bind verification.

## Constraints
- Must not change the loopback-only bind policy or the pre-bind `http_host` check in `run_http()`.
- Must not alter behavior for the normal (successful) start path.
- Keep the fix minimal; do not restructure `run_http()` or the uvicorn wiring.

## Acceptance Criteria
- A server whose lifespan startup raises no longer raises `AttributeError` about `self.servers`.
- The normal loopback start path still verifies the bound socket is loopback.
- A new or updated test reproduces the failing-lifespan case and passes.

## Testing Expectations
- Unit test for the failing-lifespan path (no `AttributeError`, clean startup failure).
- Existing `tests/mcp_servers/test_mcp_server_base.py` still passes.
- `uv run ruff check scripts/mcp_servers/server.py`, `uv run mypy --no-namespace-packages scripts/`, and `uv run bandit scripts/mcp_servers/server.py` remain clean.

## Documentation Impact
None required unless the maintainer decides the post-start verification should be documented as intentionally defensive. If the redundancy is noted, record it as a Known Issue / Needs Confirmation rather than implementation detail.

## Out of Scope
- Changing which servers define a lifespan.
- Changing the loopback bind validation policy.
- Refactoring `run_http()` beyond the override guard.

## Dependencies
N/A: none

## Unresolved Questions
- Whether any current server other than `rag-pipeline-mcp` could define a failing lifespan in the future (affects blast radius). Confirmed today: only `rag-pipeline-mcp` uses a lifespan.
- Whether the clean uvicorn diagnostic is sufficient on its own, or whether `run_http()` should log an explicit one-line message when the override detects the early-exit case.

## AI Implementation Instruction
Do not rewrite `run_http()` or the bind policy. Add a single guard at the top of `_LoopbackVerifyingServer.startup()` after `await super().startup(sockets=sockets)` so the `self.servers` iteration is skipped when `self.should_exit` is True or `self.servers` is unset. Reproduce the bug first with a failing-lifespan app, confirm the `AttributeError`, apply the guard, then confirm it is gone and the normal start path still verifies loopback binding. Do not touch unrelated servers.

## Traceability
- **Workflow phase**: python-code-review (GitHub Issue Conversion via issue-creator)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261018-191418
- **Related target files**: scripts/mcp_servers/server.py, tests/mcp_servers/test_mcp_server_base.py

## Verification

**Overall assessment:** The issue's core claim is verified against the current source and reproduced at runtime. The `_LoopbackVerifyingServer.startup()` override in `scripts/mcp_servers/server.py` accesses `self.servers` unconditionally after `await super().startup()`. In uvicorn 0.49.0, `Server.startup()` returns early (setting `self.should_exit = True` and leaving `self.servers` unset) whenever the ASGI lifespan startup fails, and `Server.__init__` never initializes `self.servers`. The override therefore raises `AttributeError` on the failing-lifespan path, masking uvicorn's own "Application startup failed. Exiting." diagnostic.

**Core claim status:** HOLDS. Reproduced with a subclass of the real `uvicorn.Server` and a FastAPI app whose lifespan raises during startup: uvicorn logged `ERROR: Application startup failed. Exiting.` and the override then raised `AttributeError: '_LoopbackVerifyingServer' object has no attribute 'servers'`. A guarded variant (`if self.should_exit or not getattr(self, "servers", None): return`) eliminated the `AttributeError` while preserving the clean diagnostic.

**Findings by severity:**

- **High — Diagnostic masking on failing lifespan (core).** `_LoopbackVerifyingServer.startup()` iterates `self.servers` with no guard. On the early-exit path `self.servers` is never assigned, so the override raises `AttributeError`, which escapes `run_http()` (its `try/except` catches only `KeyboardInterrupt`) and produces an unhandled traceback and exit code 1. The underlying cause (embedding/LLM endpoint unreachable, DB missing, invalid config) is hidden. Only `rag-pipeline-mcp` defines a FastAPI lifespan (`_lifespan` awaiting `RagPipelineMCPService.start()`), so it is the sole affected server. Evidence: `scripts/mcp_servers/server.py` `_LoopbackVerifyingServer.startup()`; uvicorn 0.49.0 `Server.startup()` early-return; `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` `_lifespan`; runtime reproduction under `/tmp/mcprepro/`.

- **Medium — No test coverage of the failing-lifespan path.** Every bind-path test in `tests/mcp_servers/test_mcp_server_base.py` patches `uvicorn.Server.run` to a no-op (`_fake_run`) that sets `self.started` and never calls the real `startup()`, so the override's early-exit branch is never exercised. This is why the defect survived. The requested regression test closes this gap. Evidence: `tests/mcp_servers/test_mcp_server_base.py` `TestBindAddressValidation._fake_run`.

- **Low — Wording inconsistency in Documentation Impact.** The "Documentation Impact" section refers to "the redundancy" of the post-start verification without ever establishing that redundancy elsewhere in the document; reads as template residue. Does not affect the core claim.

- **Informational — Guard formulation.** The suggested guard `if self.should_exit or not getattr(self, "servers", None): return` is correct and minimal. An equally valid, simpler signal is `if not self.started: return`, since `self.started` is set True only on the normal path. Either preserves the loopback verification for the successful start.

**Verdict:** Holds — the issue describes a real, currently-unresolved defect. Proceed to plan.
