## Goal
- Make execution mode explicit before any handler runs: one typed execution context (request id, session id, idempotency key, execution mode) and structured result metadata (`execution_mode`, `side_effect_applied`) replace output-string dry-run detection and keyless programmatic dispatch, so a preview never creates replayable durable state and every side-effecting dispatch, HTTP or programmatic, carries a key.

## Priority
High

## Scope
- **In-Scope**:
  - A shared execution-mode vocabulary (`preview`, `applied`, `no_op`) and one resolver that derives the mode from validated arguments and the tool's declared preview capability.
  - A typed MCP-side `ExecutionContext` built at every entry point and consumed by `dispatch_tool`; `MCPServer.dispatch` and every server's programmatic `dispatch` accept it.
  - Removal of `_IDEMPOTENCY_DRY_RUN_MARKERS`, `_is_dry_run_output`, and the clear-after-the-fact path in `_finalize_dedup`; a preview skips dedup acquisition entirely.
  - Structured result metadata on `DispatchResult` and `CallToolResponse`, carried to `ToolCallResult` on the Agent side.
  - Rejection of a side-effecting programmatic dispatch that has no idempotency key; read-only programmatic callers unchanged.
  - Agent side: the `ToolExecutionContext` gains `execution_mode`, sent as `X-Execution-Mode`; the approval pre-approval preview gets its own context; a preview call is excluded from applied-operation state (no `tool_call_state` row, no `attempt_side_effect`).
  - Parameterized dry-run tests for file, Git, and GitHub tools, including a formatter-wording regression test.
  - Documentation of the execution-context contract (MCP dispatch document) and regeneration of generated artifacts.
- **Out-of-Scope**:
  - Dedup storage state machine, key generation and replay, GitHub retry policy (separate work items).
  - A new `previewed` value in the `tool_call_state` vocabulary: the Issue allows either `previewed` or exclusion, and exclusion needs no persisted-schema change.
  - Final MCP design-document sweep (mcpai012), file MCP hardening (mcpai009), GitHub HTTP contract tests (mcpai010).
  - Enumerating or changing preview support for tools that do not declare `preview_capability = "dry_run"`.
- **Dependencies**:
  - The published `dry_run` schema, dispatcher durable-state behavior, propagated key contract, and the Agent execution context are all delivered by closed Plans (GitHub schema source, atomic dedup state machine, logical idempotency key, approval-grant intent); the replay-directive Plan (mcpai004) has procedures generated but not executed and edits `tool_preparation.py`, `tool_runner.py`, and `context.py`; see UNK-01. This Plan blocks mcpai009 and mcpai010.
  - **Depends on**: plans/done/20261120-222144_mcpdl001_approval-grant-intent.md | phase all | defines `ToolExecutionContext` and the logical call id that this Plan extends with `execution_mode`
  - **Depends on**: plans/done/20261125-105505_mcpai004_logical-idempotency-key-replay.md | phase all | both edit `tool_preparation.py` and `tool_runner.py`; land the replay directive first so the mode is attached to the context it extends (procedures still pending; UNK-01)

## Background
- Source: consolidated review backlog (`memo-issue.md`, Issue 5), filed as `issues/20261119-140512_mcpai005_structured-execution-context.md`.
- Path B: more than 3 files, new modules, public interface changes (`dispatch_tool`, `MCPServer.dispatch`, `CallToolResponse`, `ToolExecutionContext`), and a behavior change for programmatic dispatch.
- The Issue's line numbers are stale (`dispatch.py` has since been split; the dedup machinery lives in `mcp_servers/dedup_gate.py`); the claims were re-verified by symbol, not by line.

## Problem
- Dry-run status is inferred from the output text after the handler returned, so the durable pending row is created first and cleared afterward.
- The marker list recognizes only JSON `"dry_run": true` and `(dry_run)`; the Git formatters emit `[DRY RUN] ...` and the file write, delete, directory, and move formatters emit `Dry-run: ...`, which no marker matches. Those previews are finalized with `record_completed` and become replayable completed results (verified, see `Design`).
- Programmatic `MCPServer.dispatch(name, args)` on every server calls the dispatcher with no key, and `dispatch_tool` executes a keyless side-effecting call, bypassing the `X-Idempotency-Key` contract that only the HTTP middleware enforces.
- The Agent's pre-approval preview calls `tools.execute(tool, {..., "dry_run": True})` with no context, and `HttpTransport.call` refuses a call without a logical call id, so the preview of a dry-run-capable tool cannot reach the server at all.
- An LLM-issued side-effecting call with `dry_run: true` is recorded as a `pending` then `completed` `tool_call_state` row and sets `attempt_side_effect`, so workflow state reports a preview as an applied write.

## Reason for Change
- Execution mode and identity must be explicit before the handler runs; this also removes the heuristic marker list that every new formatter would otherwise extend.

## Implementation Intent
- Define the mode once in `shared`, resolve it from validated arguments plus declared capability at each entry, carry it in a frozen `ExecutionContext` into `dispatch_tool`, let a preview bypass dedup acquisition entirely, and report mode and side-effect status as structured fields. The Agent side adopts the same vocabulary and excludes previews from applied-operation state.

## Requirements
- `REQ-001`: Add `ExecutionMode` (`preview`, `applied`, `no_op`) and `resolve_execution_mode(tool, args, preview_capable)` in a shared leaf module; `preview` only when the tool declares `preview_capability = "dry_run"` and `args["dry_run"] is True`; a non-boolean `dry_run` on a preview-capable tool is a validation error before any durable state is created.
- `REQ-002`: Add a frozen MCP-side `ExecutionContext` (request id, session id, idempotency key, execution mode) built by one function from the request, and accepted by `dispatch_tool` in place of the bare `idempotency_key`; every server's HTTP `call_tool` and programmatic `dispatch` build and pass it.
- `REQ-003`: Remove all output-marker dry-run parsing (`_IDEMPOTENCY_DRY_RUN_MARKERS`, `_is_dry_run_output`) and the post-handler `dry_run` branch of `_finalize_dedup`.
- `REQ-004`: A preview-mode call performs no dedup acquisition, writes no durable row and no overlay entry, and reports `execution_mode="preview"`, `side_effect_applied=False`; a real execution after a preview with the same key is not blocked or replaced.
- `REQ-005`: Result metadata: `DispatchResult` and `CallToolResponse` carry `execution_mode` and `side_effect_applied`; `applied` plus success is `side_effect_applied=True`, a dedup replay is `no_op`, a preview is `preview`; formatter text is unchanged except where a control marker is removed.
- `REQ-006`: `dispatch_tool` rejects a side-effecting call with no non-blank idempotency key (`error_type="idempotency_key_required"`), preview included; read-only tools dispatch without a key; the HTTP and programmatic paths return the same metadata.
- `REQ-007`: `ToolExecutionContext` gains `execution_mode`; `HttpTransport` sends it as `X-Execution-Mode` and parses the response metadata into `ToolCallResult`; the server rejects a header that disagrees with the mode resolved from the arguments.
- `REQ-008`: The approval preview builds its own `ToolExecutionContext` (fresh logical call id, mode `preview`) so the preview reaches the server and is checked against the same contract.
- `REQ-009`: A prepared call whose mode is `preview` writes no `tool_call_state` row and does not set `attempt_side_effect`, so Agent workflow state never reports a preview as an applied write.
- `REQ-010`: Tests written first: parameterized dry-run tests for file, Git, and GitHub tools; a formatter-wording regression test; dry-run then real execution; keyless and keyed programmatic dispatch; read-only compatibility.
- `REQ-011`: Document the execution modes, the context contract, and the failure behavior in the MCP dispatch document; regenerate generated artifacts.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/execution_mode.py | Create (new file): `ExecutionMode`, `resolve_execution_mode` | One shared mode contract for Agent and MCP | REQ-001; AC-1 | No mode type exists: `rg ExecutionMode` finds none; `PreviewCapability` lives in `shared/tool_metadata.py:66` (checked in Step 3) | tests/shared/test_execution_mode.py | Verified |
| scripts/shared/transport_dto.py | Modify: `ToolExecutionContext.execution_mode`; `ToolCallResult.execution_mode` and `side_effect_applied` | Carry mode out and metadata back | REQ-005, REQ-007; AC-4 | `ToolExecutionContext` has `call_id, tool, args_hash, operation` only (checked in Step 3) | tests/shared/test_transport_dto.py | Verified |
| scripts/shared/http_transport.py | Modify: send `X-Execution-Mode`, parse response metadata | Wire the mode | REQ-007, REQ-008; AC-4 | Headers set at lines 213-217; call refused without context at line 197 (checked in Step 3) | tests/shared/test_http_transport.py | Verified |
| scripts/mcp_servers/execution_context.py | Create (new file): `ExecutionContext`, `build_execution_context` | Typed context built once per entry | REQ-002; AC-1, AC-3 | `extract_request_context` returns an untyped 3-tuple (`server.py:258`) (checked in Step 3) | tests/mcp_servers/test_execution_context.py | Verified |
| scripts/mcp_servers/dispatch.py | Modify: take `ExecutionContext`; preview bypass; remove markers; key rule; metadata | Core behavior | REQ-003, REQ-004, REQ-005, REQ-006; AC-1, AC-2, AC-3 | `_IDEMPOTENCY_DRY_RUN_MARKERS`, `_is_dry_run_output`, `_finalize_dedup(dry_run=...)`; keyless call executes (checked in Step 3) | tests/mcp_servers/test_mcp_dispatch.py | Verified |
| scripts/mcp_servers/dedup_gate.py | Modify: `DispatchResult` gains `execution_mode`, `side_effect_applied` | Result contract | REQ-005; AC-4 | `DispatchResult` has `output, is_error, error_type, dedup_state` (checked in Step 3) | tests/mcp_servers/test_mcp_dispatch.py | Verified |
| scripts/mcp_servers/models.py | Modify: `CallToolResponse` metadata fields | HTTP result contract | REQ-005; AC-4 | `CallToolResponse(result, is_error, dedup_state)` (checked in Step 3) | tests/mcp_servers/test_models.py | Verified |
| scripts/mcp_servers/server.py | Modify: `MCPServer.dispatch(name, args, context)`; header cross-check; preview-capability seam beside `configure_tool_retry_policies` | Base contract | REQ-002, REQ-006, REQ-007; AC-3, AC-4 | `dispatch` at line 293; seam at line 401 (checked in Step 3) | tests/mcp_servers/test_mcp_server_base.py | Verified |
| scripts/mcp_servers/git/git_server.py | Modify: build and pass context in `call_tool` and `dispatch` | Entry point | REQ-002, REQ-006; AC-3 | `dispatch_tool(..., idempotency_key=...)` at line 332; keyless at line 417 (checked in Step 3) | tests/mcp_servers/git/test_git_service_dispatch.py | Verified |
| scripts/mcp_servers/github/github_server.py | Modify: same | Entry point | REQ-002, REQ-006; AC-3 | `_dispatch_github_tool(..., idempotency_key=None)` at line 192 (checked in Step 3) | tests/mcp_servers/github/test_github_server_endpoints.py | Verified |
| scripts/mcp_servers/file/write_server.py | Modify: same | Entry point | REQ-002, REQ-006; AC-3 | `_dispatch_write_tool` at line 130 (checked in Step 3) | tests/mcp_servers/file/test_file_write_mcp_service.py | Verified |
| scripts/mcp_servers/file/delete_server.py | Modify: same | Entry point | REQ-002, REQ-006; AC-3 | `_dispatch_delete_tool` at line 137 (checked in Step 3) | tests/mcp_servers/file/test_file_delete_mcp_service.py | Verified |
| scripts/mcp_servers/file/read_server.py | Modify: same | Entry point (read-only; signature only) | REQ-002; AC-3 | `dispatch_tool` at line 140 (checked in Step 3) | tests/mcp_servers/file/test_read_service.py | Verified |
| scripts/mcp_servers/shell/shell_server.py | Modify: same | Entry point | REQ-002, REQ-006; AC-3 | `dispatch_tool` at line 166 (checked in Step 3) | tests/mcp_servers/test_mcp_dispatch.py | Verified |
| scripts/mcp_servers/cicd/cicd_server.py | Modify: same | Entry point (names the CI/CD programmatic dispatch) | REQ-002, REQ-006; AC-3 | `dispatch_tool` at line 138 (checked in Step 3) | tests/mcp_servers/test_mcp_dispatch.py | Verified |
| scripts/mcp_servers/web_search/formatters.py | Modify: same | Entry point (read-only) | REQ-002; AC-3 | `dispatch_tool` at line 65 (checked in Step 3) | tests/mcp_servers/web_search/test_web_search_server.py | Verified |
| scripts/mcp_servers/web_search/web_search_server.py | Modify: same | Entry point (read-only) | REQ-002; AC-3 | `dispatch` at line 336 (checked in Step 3) | tests/mcp_servers/web_search/test_web_search_server.py | Verified |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Modify: same | Entry point | REQ-002; AC-3 | `dispatch_tool` at line 241 (checked in Step 3) | tests/mcp_servers/test_mcp_dispatch.py | Verified |
| scripts/mcp_servers/mdq/mdq_server.py | Modify: same | Entry point | REQ-002; AC-3 | `dispatch_tool` at line 322; `dispatch` drops dedup metadata at line 495 (checked in Step 3) | tests/mcp_servers/mdq/test_mdq_exception_handlers.py | Verified |
| scripts/agent/tool_preparation.py | Modify: resolve and set `execution_mode` on the prepared context | Agent adopts the vocabulary | REQ-001, REQ-007, REQ-009; AC-5 | `ToolExecutionContext(...)` built at line 217 without a mode (checked in Step 3) | tests/agent/test_tool_preparation.py | Verified |
| scripts/agent/tool_runner.py | Modify: skip state row and `attempt_side_effect` for a preview | Preview is not an applied write | REQ-009; AC-5 | `_record_pending_state` and `_finalize_state` at lines 176-246; `attempt_side_effect = True` at line 286 (checked in Step 3) | tests/agent/test_tool_runner.py | Verified |
| scripts/agent/tool_approval.py | Modify: preview call carries its own preview context | Preview reaches the server | REQ-008; AC-4, AC-5 | `tools.execute(tool_name, {**args, "dry_run": True})` with no context at lines 144-147 (checked in Step 3) | tests/agent/test_tool_approval_preflight.py | Verified |
| tests/shared/test_execution_mode.py | Create (new file): resolver cases | Cover REQ-001 | REQ-001, REQ-010; AC-1 | New module has no test (checked in Step 3) | itself | Verified |
| tests/mcp_servers/test_execution_context.py | Create (new file): context building and header cross-check | Cover REQ-002, REQ-007 | REQ-002, REQ-010; AC-3 | New module has no test (checked in Step 3) | itself | Verified |
| tests/mcp_servers/test_dry_run_contract.py | Create (new file): parameterized file/Git/GitHub previews, wording-change regression, dry-run then real | Cover REQ-003 to REQ-006 | REQ-010; AC-1, AC-2 | Existing dry-run cases are 8 refs in `test_mcp_dispatch.py`; no cross-server contract test (checked in Step 3) | itself | Verified |
| tests/mcp_servers/test_mcp_dispatch.py | Modify: context-based calls, remove marker cases | Signature and behavior change | REQ-003, REQ-004, REQ-006, REQ-010; AC-2, AC-3 | 55 `idempotency_key=` call sites (checked in Step 3) | itself | Verified |
| tests/mcp_servers/test_mcp_dispatch_concurrency.py | Modify: context-based calls | Signature change | REQ-002, REQ-010; AC-3 | 3 `idempotency_key=` call sites (checked in Step 3) | itself | Verified |
| tests/mcp_servers/test_models.py | Modify: response metadata fields | Cover REQ-005 | REQ-005, REQ-010; AC-4 | `CallToolResponse` tests exist in this file (checked in Step 3) | itself | Verified |
| tests/mcp_servers/test_mcp_server_base.py | Modify: base `dispatch` with context | Signature change | REQ-002, REQ-010; AC-3 | Base-class dispatch tests (checked in Step 3) | itself | Verified |
| tests/shared/test_http_transport.py | Modify: header and metadata cases | Cover REQ-007 | REQ-007, REQ-010; AC-4 | Wire-gate tests exist (checked in Step 3) | itself | Verified |
| tests/shared/test_transport_dto.py | Modify: new fields | Cover REQ-005, REQ-007 | REQ-005, REQ-010; AC-4 | DTO tests exist (checked in Step 3) | itself | Verified |
| tests/agent/test_tool_preparation.py | Modify: mode set at preparation | Cover REQ-009 | REQ-009, REQ-010; AC-5 | Context creation tests exist (checked in Step 3) | itself | Verified |
| tests/agent/test_tool_runner.py | Modify: preview writes no state row | Cover REQ-009 | REQ-009, REQ-010; AC-5 | `_record_pending_state` tests exist (checked in Step 3) | itself | Verified |
| tests/agent/test_tool_approval_preflight.py | Modify: preview context | Cover REQ-008 | REQ-008, REQ-010; AC-4 | 24 dry-run references (checked in Step 3) | itself | Verified |
| docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Modify: execution modes, context contract, key rule; correct the "dry-run results are never cached" sentence | Documentation Impact | REQ-011; AC-6 | Line 68 states dry-run results are never cached (checked in Step 3) | docs gates | Verified |
| docs/23_agent/agent_13_reference-api-generated.md | Regenerate (never hand-edit) | Public symbols change | REQ-011; AC-6 | Lists agent public API (checked in Step 3) | generator check | Verified |
| registry/manifests/agent_api.yaml | Regenerate (never hand-edit) | Public symbols change | REQ-011; AC-6 | Lists `ToolExecutionContext` owners (checked in Step 3) | generator check | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/tool_metadata.py | Defines `PreviewCapability` and its closed vocabulary | REQ-001 |
| scripts/shared/runtime_tool.py | Agent-side `RuntimeTool.preview_capability` read at preparation | REQ-001, REQ-009 |
| scripts/shared/tool_constants.py | `ALL_SIDE_EFFECTING_TOOLS`, the key-rule scope | REQ-006 |
| scripts/mcp_servers/tool_validators.py | Per-tool argument validation that runs before dispatch | REQ-001 |
| scripts/mcp_servers/git/format_output.py | Emits `[DRY RUN] ...`, unmatched by any marker | REQ-003 |
| scripts/mcp_servers/file/write_formatter.py | Emits `Dry-run: ...`, unmatched by any marker | REQ-003 |
| scripts/mcp_servers/github/github_service_dispatch_writes.py | Emits JSON `"dry_run": true` through `_execute_with_dry_run` | REQ-003 |
| scripts/shared/tool_executor.py | `execute` forwards an optional context unchanged | REQ-008 |
| scripts/shared/mcp_dedup.py | Durable store whose acquisition a preview must not reach | REQ-004 |
| tests/mcp_servers/conftest.py | Fixtures that call `dispatch_tool`; read to judge fallout | UNK-03 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-003): Dry-run behavior is independent of formatter output: changing a formatter's preview wording does not change dedup behavior, and one contract covers file, Git, and GitHub tools.
- AC-2 (REQ-004): A preview leaves no durable row and no overlay entry; a real execution with the same key after a preview executes and is recorded.
- AC-3 (REQ-002, REQ-006): A programmatic side-effecting dispatch without a key is rejected with `idempotency_key_required`; a keyed one executes; a read-only one executes without a key.
- AC-4 (REQ-005, REQ-007, REQ-008): HTTP and programmatic dispatch return the same `execution_mode` and `side_effect_applied`; the Agent's approval preview reaches the server and returns `preview`.
- AC-5 (REQ-009): An LLM-issued `dry_run: true` call leaves no `tool_call_state` row and does not set `attempt_side_effect`.
- AC-6 (REQ-011): The MCP dispatch document describes the modes and the key rule, and generated artifacts are regenerated.

## Tests
- REQ-001: resolver table: preview-capable plus `dry_run=True` is `preview`; `dry_run=False`, missing, `"true"`, `1` is not; a non-bool on a capable tool is rejected; a tool without the capability never previews.
- REQ-003, REQ-004: for each of `write_file`, `git_commit`, a GitHub write: preview with a durable store leaves the ledger empty; a formatter-wording change (patched preview text) does not change the outcome; preview then real with the same key executes.
- REQ-005, REQ-006: keyless and keyed programmatic dispatch for a side-effecting and a read-only tool; the same call over HTTP and `dispatch` returns equal metadata; a dedup replay is `no_op`.
- REQ-007: header present and consistent, absent, and disagreeing with the arguments.
- REQ-008, REQ-009: approval preview call carries a `preview` context; a preview-mode prepared call writes no state row and leaves `attempt_side_effect` unset; a real call is unchanged.

## Documentation Impact
- Yes. REQ-011 drives an update of the MCP dispatch document located via `docs/00_index.md` "Document References by Task"; the final sweep of the MCP design documents stays with the separate documentation work item. `docs/23_agent/agent_13_reference-api-generated.md` and `registry/manifests/agent_api.yaml` are regenerated, not edited.

## Assumptions
- `no_op` is reported for a dedup replay served from a record (`duplicate_hit`, `replayed`); a handler that reports "No changes." stays `applied`, because the dispatcher cannot know the handler's internal effect (falsifiable at procedure review).
- Exclusion from applied-operation state is chosen over a new `previewed` `tool_call_state` value, which would require a persisted-schema change under `rules/persisted-schema-change.md`.
- The key requirement covers preview calls too: HTTP middleware already rejects a keyless side-effecting `POST /v1/call_tool` regardless of `dry_run`, and the Agent preview supplies its own logical call id.
- Programmatic `dispatch` has no in-tree production caller (`rg "\.dispatch\("` finds only the overrides and one test double), so the key rule changes behavior only for tests and out-of-tree callers.
- Overlap judgment (`tools/check_plan_target_overlaps.py`, run after the freeze): the Plan for the MCP launch spec and per-server credentials (cliplc006) also lists `docs/23_agent/agent_13_reference-api-generated.md` and `registry/manifests/agent_api.yaml`; both only regenerate those artifacts from the then-current source, so the overlap is compatible and either order works (regenerate once more after the second lands).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The replay-directive Plan's procedures (`implementations/20261125-112546_*`) are generated but unexecuted and edit `tool_preparation.py`, `tool_runner.py`, `context.py`; the dependency tool reads that Plan as closed | Implementation status when this Plan's procedures execute | Execute the replay-directive procedures first; re-read both files at procedure generation | False |
| UNK-02 | Whether `ToolExecutionContext` was meant to carry an execution mode already: the approval-grant Plan's REQ-002 lists "execution mode" but the shipped dataclass has no such field | The approval-grant procedure outcome for that field | This Plan adds `execution_mode` with default `applied`; confirm no other definition exists at procedure generation | False |
| UNK-03 | Which existing tests call `dispatch_tool` keyless on side-effecting tools (57 keyless call sites in `tests/`) and will now be rejected | Per-call-site classification | Run the suite after Phase 2; fallout files are added as Fallout-class amendments (`rules/workflow-lifecycle.md`) | False |
| UNK-04 | Preview representation for servers or tools that do not declare `dry_run` | Per-tool inventory beyond the declared `preview_capability` values | Such tools never resolve to `preview`; `dry_run` stays an ordinary argument handled by argument validation | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/execution_mode.py | Create | Medium | N/A | N/A | Yes: `scripts/` change needs a deploy |
| scripts/shared/transport_dto.py | Modify | High (Agent and MCP importers) | N/A | N/A | Yes |
| scripts/shared/http_transport.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/execution_context.py | Create | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/dispatch.py | Modify | High (18 direct importers) | N/A | N/A | Yes |
| scripts/mcp_servers/dedup_gate.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/models.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/server.py | Modify | High (base class of 10 servers) | N/A | N/A | Yes |
| scripts/mcp_servers/git/git_server.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/github/github_server.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/file/write_server.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/file/delete_server.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/file/read_server.py | Modify | Low | N/A | N/A | Yes |
| scripts/mcp_servers/shell/shell_server.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/cicd/cicd_server.py | Modify | Medium | N/A | N/A | Yes |
| scripts/mcp_servers/web_search/formatters.py | Modify | Low | N/A | N/A | Yes |
| scripts/mcp_servers/web_search/web_search_server.py | Modify | Low | N/A | N/A | Yes |
| scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | Modify | Low | N/A | N/A | Yes |
| scripts/mcp_servers/mdq/mdq_server.py | Modify | Low | N/A | N/A | Yes |
| scripts/agent/tool_preparation.py | Modify | Medium | N/A | N/A | Yes |
| scripts/agent/tool_runner.py | Modify | Medium | N/A | N/A | Yes |
| scripts/agent/tool_approval.py | Modify | Medium | N/A | N/A | Yes |
| tests/shared/test_execution_mode.py | Create | Low | N/A | N/A | None |
| tests/mcp_servers/test_execution_context.py | Create | Low | N/A | N/A | None |
| tests/mcp_servers/test_dry_run_contract.py | Create | Low | N/A | N/A | None |
| tests/mcp_servers/test_mcp_dispatch.py | Modify | Low | N/A | N/A | None |
| tests/mcp_servers/test_mcp_dispatch_concurrency.py | Modify | Low | N/A | N/A | None |
| tests/mcp_servers/test_models.py | Modify | Low | N/A | N/A | None |
| tests/mcp_servers/test_mcp_server_base.py | Modify | Low | N/A | N/A | None |
| tests/shared/test_http_transport.py | Modify | Low | N/A | N/A | None |
| tests/shared/test_transport_dto.py | Modify | Low | N/A | N/A | None |
| tests/agent/test_tool_preparation.py | Modify | Low | N/A | N/A | None |
| tests/agent/test_tool_runner.py | Modify | Low | N/A | N/A | None |
| tests/agent/test_tool_approval_preflight.py | Modify | Low | N/A | N/A | None |
| docs/22_mcp/mcp_03_01_dispatch-and-routing.md | Modify | Low | N/A | N/A | None |
| docs/23_agent/agent_13_reference-api-generated.md | Regenerate | Low | N/A | N/A | None |
| registry/manifests/agent_api.yaml | Regenerate | Low | N/A | N/A | None |

## Design
- **Issue Verification** (re-checked against current source by symbol; Step 2):

| Issue claim | Verdict | Evidence |
|---|---|---|
| Dry-run recognized by a marker scan over output text; "UNK-01: best-effort" | Confirmed | `_is_dry_run_output` and `_IDEMPOTENCY_DRY_RUN_MARKERS` in `mcp_servers/dispatch.py` (the Issue's line numbers are stale) |
| A dry-run outcome clears durable state after the fact | Confirmed | `_finalize_dedup(... dry_run ...)` calls `store.clear(key)` after the handler ran, so the pending row exists during the preview |
| A preview may be stored as a replayable completed execution | Confirmed, worse than stated | Runtime check of the real formatter outputs: `[DRY RUN] Would commit ...` (Git), `Dry-run: <path> (...)` (write_file, delete, create_directory, move_file) are not detected (`False`); only edit_file's `Diff only (dry_run)` and the JSON `"dry_run": true` of shell, cicd, and GitHub match. Undetected previews take `record_completed` |
| Programmatic dispatch accepts only tool name and arguments, bypassing the key contract | Confirmed | Every server's `dispatch(name, args)` override calls the dispatcher without a key; `dispatch_tool` executes a keyless side-effecting call. The HTTP middleware (`attach_auth_middleware`, REQ-004 boundary) enforces the key only on `POST /v1/call_tool` |
| Formatters differ | Confirmed | Three styles above |
| Programmatic callers are unknown | Resolved | No in-tree production caller of `MCPServer.dispatch`; only overrides and one test double (`tests/integration/test_production_security_regression.py`) |
| (Found) Agent preview of a dry-run-capable tool cannot reach the server | Confirmed by reading | `_build_preview_with_dry_run` calls `tools.execute(...)` with no context; `HttpTransport.call` refuses a call with no logical call id. Not run end to end; a REQ-008 test covers it |
| (Found) LLM-issued `dry_run: true` is recorded as an applied write in the Agent | Confirmed by reading | `_record_pending_state` and `_finalize_state("completed")` run for any side-effecting tool; no code reads `dry_run` in `tool_runner.py` or `tool_preparation.py` |

- **Mode resolution**: `resolve_execution_mode(tool, args, preview_capable)` in `shared/execution_mode.py` (a leaf, importable by Agent and MCP). The MCP side obtains `preview_capable` from the server's tool table through a new `configure_tool_preview_capabilities` seam called next to `configure_tool_retry_policies` in `server.py`; the Agent side reads `RuntimeTool.preview_capability`. Both apply the same rule, so the `X-Execution-Mode` header is a cross-check, not the authority.
- **Dispatcher**: `dispatch_tool(table, name, args, context)`. Order: name and handler checks, key rule for side-effecting tools, mode from the context; preview goes straight to the handler with no acquisition, no heartbeat, no finalization, no overlay write; applied follows the existing acquisition path. A dedup replay returns `no_op`.
- **Consumer scan** (`tools/scan_change_consumers.py`, seed `scripts/mcp_servers/dispatch.py`): 18 direct script candidates; the 10 servers and `web_search/formatters.py` are target rows; `control_api.py` only mentions the module in a docstring, `not affected`. Seed `shared/transport_dto.py` consumers are Agent and invoker modules that construct the context positionally by keyword; the new field has a default, so they are `not affected`.
- **Predictable fallout**: 57 keyless `dispatch_tool` test call sites (UNK-03); generated reference artifacts (last two rows); no tool inventory change; module size gate: `dispatch.py` shrinks.

## Implementation steps
1. **Phase 1: Tests first (REQ-010)**
   - [ ] Write the wording-regression, preview-no-state, dry-run-then-real, keyless/keyed, header cross-check, and Agent preview tests, expecting failure (REQ-010; tests/mcp_servers/test_dry_run_contract.py, tests/shared/test_execution_mode.py, tests/mcp_servers/test_execution_context.py, tests/mcp_servers/test_mcp_dispatch.py, tests/agent/test_tool_runner.py, tests/agent/test_tool_preparation.py, tests/agent/test_tool_approval_preflight.py)
2. **Phase 2: Shared vocabulary and DTOs (REQ-001, REQ-005, REQ-007)**
   - [ ] Mode type and resolver (scripts/shared/execution_mode.py)
   - [ ] Context and result fields (scripts/shared/transport_dto.py); wire header and metadata (scripts/shared/http_transport.py)
3. **Phase 3: MCP dispatcher and entry points (REQ-002 to REQ-006)**
   - [ ] `ExecutionContext` (scripts/mcp_servers/execution_context.py); result and response fields (scripts/mcp_servers/dedup_gate.py, scripts/mcp_servers/models.py)
   - [ ] Dispatcher rewrite, marker removal, preview bypass, key rule (scripts/mcp_servers/dispatch.py); base class and seam (scripts/mcp_servers/server.py)
   - [ ] Each server passes the context in `call_tool` and `dispatch` (git, github, file write, file delete, file read, shell, cicd, web_search, rag_pipeline, mdq server modules and scripts/mcp_servers/web_search/formatters.py)
4. **Phase 4: Agent adoption (REQ-007, REQ-008, REQ-009)**
   - [ ] Mode at preparation (scripts/agent/tool_preparation.py); preview excluded from state (scripts/agent/tool_runner.py); preview context (scripts/agent/tool_approval.py)
5. **Phase 5: Documentation and generated artifacts (REQ-011)**
   - [ ] docs/22_mcp/mcp_03_01_dispatch-and-routing.md; regenerate docs/23_agent/agent_13_reference-api-generated.md and registry/manifests/agent_api.yaml
6. **Phase 6: Deployment & Verification**
   - [ ] Run `uv run ruff format`, `uv run ruff check`, `uv run mypy`, and the full `uv run pytest`; hand off to `skills/deploy/SKILL.md` after commit and push (deploying is the user's decision); the Agent and every MCP server must be restarted together because the header and response fields change on both sides (REQ-007; scripts/mcp_servers/dispatch.py, scripts/shared/http_transport.py)

### Release units
**Unit**: R1-mode-contract | **Phases**: 2, 3, 4 | **Reason**: removing the marker path and requiring a context breaks every dispatcher caller and the Agent preview until the entry points and Agent adoption land together; Phase 1 tests are expected to fail until then.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/execution_mode.py | Unit | `uv run pytest tests/shared/test_execution_mode.py` | Resolver table passes |
| scripts/mcp_servers/dispatch.py and servers | Unit and contract | `uv run pytest tests/mcp_servers/test_dry_run_contract.py tests/mcp_servers/test_mcp_dispatch.py tests/mcp_servers/test_mcp_dispatch_concurrency.py` | Preview leaves no state; keyless side-effecting rejected |
| scripts/shared/http_transport.py, transport_dto.py | Unit | `uv run pytest tests/shared/test_http_transport.py tests/shared/test_transport_dto.py` | Header and metadata pass |
| scripts/agent/tool_runner.py, tool_preparation.py, tool_approval.py | Unit | `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_tool_preparation.py tests/agent/test_tool_approval_preflight.py` | Preview excluded from state; preview reaches server |
| All changed Python | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml` | Clean |
| Whole suite and coverage | Regression | `uv run pytest` and the diff-cover sequence in `rules/toolchain.md` | Green; changed lines at the Completion-checklist threshold |
| docs and generated artifacts | Gates | the checkers in `rules/tool-gates.md` "When to run which tool" | No findings |

Validation quality baseline (Step 5): `radon cc` average complexity is A for `dispatch.py` (4.3), `server.py` (3.5), `http_transport.py` (3.7), `tool_runner.py` (4.0), `tool_approval.py` (3.9), and `tool_preparation.py` (4.3); the vulture and bandit baselines were recorded in the previous Plan of this cycle on the same tree and are unchanged for these files (vulture: three unrelated findings; bandit: no finding in these modules is tied to this Plan); the diff-cover baseline is N/A in this document-only phase and is recorded at implementation.

## Risks
- **Risk**: Rejecting keyless side-effecting programmatic dispatch breaks the 57 keyless test call sites and any out-of-tree caller → **Mitigation**: UNK-03 triage after Phase 2; HTTP already rejects keyless calls, so production HTTP behavior does not change; out-of-tree callers are not known to exist.
- **Risk**: The Agent and the MCP servers must agree on the new header and response fields → **Mitigation**: both fields are optional on the wire (absent header: the server resolves the mode from the arguments; absent response fields: the Agent defaults to `applied`), and Phase 6 restarts both sides together.
- **Risk**: A bug in the resolver turns a real write into a preview and silently skips it → **Mitigation**: `preview` only for the strict `dry_run is True` on a tool that declares the capability; the table test covers truthy non-bool values; the server rejects a header that disagrees.
- **Risk**: Excluding previews from `tool_call_state` hides an LLM-issued preview from crash recovery → **Mitigation**: a preview has no side effect to recover; the audit event still records it with the mode.
- **Risk**: Overlap with the replay-directive Plan on `tool_preparation.py` and `tool_runner.py` → **Mitigation**: UNK-01 and the `Depends on` bullet; execute in that order.
- **Risk**: 11 server modules change in one release unit → **Mitigation**: the edit in each is mechanical (build the context, pass it on), and the contract test runs against every server module.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | Pending | — | — | Expected to fail until Phases 2-4 land |
| 2 | Phase 2: shared vocabulary and DTOs | Pending | — | — | Release unit R1-mode-contract |
| 3 | Phase 3: MCP dispatcher and entry points | Pending | — | — | Release unit R1-mode-contract |
| 4 | Phase 4: Agent adoption | Pending | — | — | Release unit R1-mode-contract |
| 5 | Phase 5: documentation and generated artifacts | Pending | — | — | Regenerate, do not hand-edit |
| 6 | Phase 6: deployment and verification | Pending | — | — | Deploy is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261125-121807
- **Related target files**: scripts/shared/execution_mode.py, scripts/shared/transport_dto.py, scripts/shared/http_transport.py, scripts/mcp_servers/execution_context.py, scripts/mcp_servers/dispatch.py, scripts/mcp_servers/dedup_gate.py, scripts/mcp_servers/models.py, scripts/mcp_servers/server.py, scripts/mcp_servers/git/git_server.py, scripts/mcp_servers/github/github_server.py, scripts/mcp_servers/file/write_server.py, scripts/mcp_servers/file/delete_server.py, scripts/mcp_servers/file/read_server.py, scripts/mcp_servers/shell/shell_server.py, scripts/mcp_servers/cicd/cicd_server.py, scripts/mcp_servers/web_search/formatters.py, scripts/mcp_servers/web_search/web_search_server.py, scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py, scripts/mcp_servers/mdq/mdq_server.py, scripts/agent/tool_preparation.py, scripts/agent/tool_runner.py, scripts/agent/tool_approval.py, tests/shared/test_execution_mode.py, tests/mcp_servers/test_execution_context.py, tests/mcp_servers/test_dry_run_contract.py, tests/mcp_servers/test_mcp_dispatch.py, tests/mcp_servers/test_mcp_dispatch_concurrency.py, tests/mcp_servers/test_models.py, tests/mcp_servers/test_mcp_server_base.py, tests/shared/test_http_transport.py, tests/shared/test_transport_dto.py, tests/agent/test_tool_preparation.py, tests/agent/test_tool_runner.py, tests/agent/test_tool_approval_preflight.py, docs/22_mcp/mcp_03_01_dispatch-and-routing.md, docs/23_agent/agent_13_reference-api-generated.md, registry/manifests/agent_api.yaml

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent (mode from validated arguments) | scripts/shared/execution_mode.py | 2 | AC-1 | tests/shared/test_execution_mode.py | Explicit in issue |
| REQ-001 | Required Changes; Agent resolves the same mode | scripts/agent/tool_preparation.py | 4 | AC-5 | tests/agent/test_tool_preparation.py | Derived from confirmed evidence |
| REQ-002 | Implementation Intent (execution context) | scripts/mcp_servers/execution_context.py | 3 | AC-3 | tests/mcp_servers/test_execution_context.py | Explicit in issue |
| REQ-002 | Implementation Intent (same dispatcher path) | scripts/mcp_servers/server.py | 3 | AC-3 | tests/mcp_servers/test_mcp_server_base.py | Explicit in issue |
| REQ-002 | Target Files (Git, GitHub, file dispatch) | scripts/mcp_servers/git/git_server.py | 3 | AC-3 | tests/mcp_servers/git/test_git_service_dispatch.py | Explicit in issue |
| REQ-002 | Target Files (Git, GitHub, file dispatch) | scripts/mcp_servers/github/github_server.py | 3 | AC-3 | tests/mcp_servers/github/test_github_server_endpoints.py | Explicit in issue |
| REQ-002 | Target Files (Git, GitHub, file dispatch) | scripts/mcp_servers/file/write_server.py | 3 | AC-3 | tests/mcp_servers/file/test_file_write_mcp_service.py | Explicit in issue |
| REQ-002 | Target Files (Git, GitHub, file dispatch) | scripts/mcp_servers/file/delete_server.py | 3 | AC-3 | tests/mcp_servers/file/test_file_delete_mcp_service.py | Explicit in issue |
| REQ-002 | Target Files (file dispatch); shared signature | scripts/mcp_servers/file/read_server.py | 3 | AC-3 | tests/mcp_servers/file/test_read_service.py | Derived from confirmed evidence |
| REQ-002 | Target Files (CI/CD programmatic dispatch); `cicd_server.py:138` | scripts/mcp_servers/cicd/cicd_server.py | 3 | AC-3 | tests/mcp_servers/test_mcp_dispatch.py | Confirmed by repository evidence |
| REQ-002 | Shared signature; `shell_server.py:166` | scripts/mcp_servers/shell/shell_server.py | 3 | AC-3 | tests/mcp_servers/test_mcp_dispatch.py | Confirmed by repository evidence |
| REQ-002 | Shared signature; `formatters.py:65` | scripts/mcp_servers/web_search/formatters.py | 3 | AC-3 | tests/mcp_servers/web_search/test_web_search_server.py | Confirmed by repository evidence |
| REQ-002 | Shared signature; `web_search_server.py:336` | scripts/mcp_servers/web_search/web_search_server.py | 3 | AC-3 | tests/mcp_servers/web_search/test_web_search_server.py | Confirmed by repository evidence |
| REQ-002 | Shared signature; `rag_pipeline_server.py:241` | scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py | 3 | AC-3 | tests/mcp_servers/test_mcp_dispatch.py | Confirmed by repository evidence |
| REQ-002 | Shared signature; `mdq_server.py:322` | scripts/mcp_servers/mdq/mdq_server.py | 3 | AC-3 | tests/mcp_servers/mdq/test_mdq_exception_handlers.py | Confirmed by repository evidence |
| REQ-003 | Required Changes (remove marker parsing); Background | scripts/mcp_servers/dispatch.py | 3 | AC-1 | tests/mcp_servers/test_dry_run_contract.py | Confirmed by repository evidence |
| REQ-004 | Required Changes (no replayable state for previews) | scripts/mcp_servers/dispatch.py | 3 | AC-2 | tests/mcp_servers/test_dry_run_contract.py | Confirmed by repository evidence |
| REQ-005 | Implementation Intent (structured result metadata) | scripts/mcp_servers/dedup_gate.py | 3 | AC-4 | tests/mcp_servers/test_mcp_dispatch.py | Explicit in issue |
| REQ-005 | Implementation Intent (structured result metadata) | scripts/mcp_servers/models.py | 3 | AC-4 | tests/mcp_servers/test_models.py | Explicit in issue |
| REQ-005 | Acceptance Criteria (same result contract) | scripts/shared/transport_dto.py | 2 | AC-4 | tests/shared/test_transport_dto.py | Explicit in issue |
| REQ-006 | Required Changes (programmatic key); `dispatch_tool` keyless path | scripts/mcp_servers/dispatch.py | 3 | AC-3 | tests/mcp_servers/test_mcp_dispatch.py | Confirmed by repository evidence |
| REQ-007 | Constraints; shared vocabulary with the Agent context | scripts/shared/http_transport.py | 2 | AC-4 | tests/shared/test_http_transport.py | Derived from confirmed evidence |
| REQ-008 | Verification finding: preview call has no context | scripts/agent/tool_approval.py | 4 | AC-4 | tests/agent/test_tool_approval_preflight.py | Confirmed by repository evidence |
| REQ-009 | Required Changes (represent preview in Agent workflow state) | scripts/agent/tool_runner.py | 4 | AC-5 | tests/agent/test_tool_runner.py | Confirmed by repository evidence |
| REQ-010 | Testing Expectations | tests/mcp_servers/test_dry_run_contract.py | 1 | AC-1, AC-2 | itself | Explicit in issue |
| REQ-010 | Testing Expectations | tests/shared/test_execution_mode.py | 1 | AC-1 | itself | Explicit in issue |
| REQ-010 | Testing Expectations | tests/mcp_servers/test_execution_context.py | 1 | AC-3 | itself | Explicit in issue |
| REQ-010 | Testing Expectations (keyed and keyless) | tests/mcp_servers/test_mcp_dispatch.py | 1 | AC-2, AC-3 | itself | Explicit in issue |
| REQ-010 | Signature change | tests/mcp_servers/test_mcp_dispatch_concurrency.py | 1 | AC-3 | itself | Derived from confirmed evidence |
| REQ-010 | Result metadata | tests/mcp_servers/test_models.py | 1 | AC-4 | itself | Explicit in issue |
| REQ-010 | Base dispatch with context | tests/mcp_servers/test_mcp_server_base.py | 1 | AC-3 | itself | Derived from confirmed evidence |
| REQ-010 | Wire header and metadata | tests/shared/test_http_transport.py | 1 | AC-4 | itself | Derived from confirmed evidence |
| REQ-010 | DTO fields | tests/shared/test_transport_dto.py | 1 | AC-4 | itself | Derived from confirmed evidence |
| REQ-010 | Agent preparation mode | tests/agent/test_tool_preparation.py | 1 | AC-5 | itself | Explicit in issue |
| REQ-010 | Agent preview excluded from state | tests/agent/test_tool_runner.py | 1 | AC-5 | itself | Explicit in issue |
| REQ-010 | Agent preview context | tests/agent/test_tool_approval_preflight.py | 1 | AC-4 | itself | Derived from confirmed evidence |
| REQ-011 | Documentation Impact | docs/22_mcp/mcp_03_01_dispatch-and-routing.md | 5 | AC-6 | docs gates | Explicit in issue |
| REQ-011 | Documentation Impact (generated reference) | docs/23_agent/agent_13_reference-api-generated.md | 5 | AC-6 | generator check | Derived from confirmed evidence |
| REQ-011 | Documentation Impact (generated manifest) | registry/manifests/agent_api.yaml | 5 | AC-6 | generator check | Derived from confirmed evidence |
