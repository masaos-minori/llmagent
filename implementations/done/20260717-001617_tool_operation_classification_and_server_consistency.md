# Implementation Procedure: Fix Tool Operation Classification Gap and Generalize Per-Server Consistency Guardrail

Source plan: `plans/20260716-145621_plan.md`
Source requirement: `requires/20260716_13_require.md`

## Goal

Every MCP tool across all 8 servers (mdq, github, shell, git, cicd, rag_pipeline, file[read/write/delete], web_search) has consistent classification across schema, dispatch, `ToolRegistry`, side-effect detection, risk/approval policy, and audit logging. Fix the confirmed gap where `classify_operation_type()` misclassifies every non-generic-`WRITE_TOOLS` write tool as `read`, and generalize the MDQ-only drift guardrail (`tests/test_mdq_tool_layer_consistency.py`) to all 8 servers.

## Scope

**In scope**
- Extend `agent/tool_policy.py::classify_operation_type()` to check `MDQ_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `GIT_WRITE_TOOLS` (and any other `*_DELETE_TOOLS` beyond the generic `DELETE_TOOLS`) from `shared/tool_constants.py`, not a hand-picked subset.
- Add regression tests covering every previously-unclassified write-tool set.
- Generalize the dispatch/schema/registry consistency guardrail to all 8 servers via a per-server dispatch adapter, accounting for 3 distinct dispatch shapes: MDQ's module-level `_DISPATCH_TABLE`, the other 6 servers' `get_dispatch_table()` instance method, and `web_search`'s single-tool direct `if`/`return` (no table).
- Confirm `validate_routing_against_config`/`validate_routing_against_live` actual server coverage in `tests/test_tool_registry.py`; extend if any server is untested.
- Document (comments only) the distinct relationship between `tool_executor.py`'s `is_side_effect()`-triggered batch downgrade and `tool_scheduler.py`'s per-tool `requires_serial` flag — **do NOT unify or redesign these two mechanisms** without explicit user sign-off first (see Assumptions #1, blocking).
- Update MCP routing/execution documentation (`docs/04_mcp_03_01_dispatch-and-routing.md`) describing the unified tool lifecycle.
- Correct the requirement's imprecise target-file references: use `agent/tool_approval.py` and `agent/workflow/approval_ops.py`, not a nonexistent `agent/approval/*` directory.

**Out of scope**
- Adding new MCP tools.
- Redesigning the approval UI.
- Changing individual tool business behavior beyond classification/dispatch drift fixes.
- Changing non-MCP command execution behavior.
- Merging `is_side_effect()`-based batch downgrade and `requires_serial` into one mechanism.

## Assumptions

1. **BLOCKING — requires explicit user decision before implementation touches `tool_executor_helpers.py` or `tool_scheduler.py` beyond comments**: whether the two serialization mechanisms (batch-level `is_side_effect()` downgrade vs. per-tool `requires_serial`) are intentional layered defense or should be unified. Until resolved, only clarifying code comments may be added — no redesign.
2. `classify_operation_type()`'s gap is confirmed unfixed as of this plan (`grep -n "MDQ_WRITE_TOOLS\|RAG_WRITE_TOOLS\|CICD_WRITE_TOOLS\|GIT_WRITE_TOOLS" scripts/agent/tool_policy.py` returns no matches).
3. The gap's currently-active real-world impact is confined to `operation_type` in audit records (`agent/tool_audit.py`) and `agent/repository_gateway.py`'s consumption of the same classification — NOT approval risk gating, which uses `cfg.approval.tool_safety_tiers` at higher priority and already has correct per-tool entries.
4. Every non-MDQ server dispatches via `_service.get_dispatch_table()` on an instantiated service, not a module-level dict — MDQ is the outlier.
5. `web_search` has a single tool (`search_web`) with no dispatch table; the guardrail test must handle it structurally (assert the one tool name matches `WEB_SEARCH_TOOLS`), not via key-set comparison.
6. `validate_routing_against_config`/`validate_routing_against_live` are already wired into `agent/repl_health.py` startup health check and tested in `tests/test_tool_registry.py`; exact fixture coverage (real configs vs. synthetic/partial) needs confirmation during implementation, not assumed.

## Implementation

### Target file

Primary: `scripts/agent/tool_policy.py`. Secondary: `tests/test_tool_policy_comprehensive.py`, `tests/test_tool_approval_risk.py`, new `tests/test_tool_server_layer_consistency.py`, `tests/test_tool_registry.py`, `scripts/shared/tool_executor_helpers.py`, `scripts/agent/tool_scheduler.py` (comments only), `docs/04_mcp_03_01_dispatch-and-routing.md`.

### Procedure

1. **Fix `classify_operation_type()`**: import and check `MDQ_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `GIT_WRITE_TOOLS` from `shared/tool_constants.py` in `scripts/agent/tool_policy.py`. Confirm during implementation whether any `*_DELETE_TOOLS` beyond the generic `DELETE_TOOLS` also exist and need the same treatment. Before changing the function's output, read every consumer of `classify_operation_type()`'s result in `scripts/agent/repository_gateway.py` in full to confirm no behavioral regression beyond audit logging.
2. **Add regression tests**: one assertion per previously-unclassified write-tool set (MDQ/RAG/CICD/Git) in `tests/test_tool_policy_comprehensive.py` and/or `tests/test_tool_approval_risk.py`, alongside the existing generic-set cases.
3. **Resolve the serialization-mechanism Unknown with the user** before touching `tool_executor_helpers.py`/`tool_scheduler.py` beyond doc comments — present the "layered defense vs. unify" question and get an explicit decision; this determines whether this step's scope stays "add clarifying comments" or expands to "redesign."
4. **Build the per-server dispatch adapter and generalized guardrail test**: create `tests/test_tool_server_layer_consistency.py`, defining one adapter function per server key (a mapping from server key → callable returning that server's live dispatch key set), reusing each server's existing test fixture patterns (e.g., temp DB paths) to avoid live HTTP calls or heavy service construction. Mirror `tests/test_mdq_tool_layer_consistency.py`'s six assertions (schema ⊆/⊇ dispatch, tool-constants set == schema names, registry membership, write/serial flag consistency) applied to all 8 servers, with MDQ using its module-level `_DISPATCH_TABLE` and the other 7 using `get_dispatch_table()` or the single-tool structural check for `web_search`.
5. **Confirm live-discovery drift validation's actual server coverage**: read `tests/test_tool_registry.py` in full; determine if `validate_routing_against_config`/`validate_routing_against_live` fixtures exercise real configs for all 8 servers or only synthetic/partial ones; extend coverage for any untested server.
6. **Update documentation**: describe the unified tool lifecycle (schema → dispatch → registry → side-effect → risk → audit) in `docs/04_mcp_03_01_dispatch-and-routing.md` (the existing home of routing-authority documentation from the earlier MDQ-only guardrail work).
7. **Deployment/verification**: run the full test suite; no service restart needed (no runtime config or deploy-relevant file changes).

### Method

- Direct source edits to `tool_policy.py` (additive import + condition extension, not a rewrite).
- New parametrized pytest module for the generalized guardrail, following the existing `test_mdq_tool_layer_consistency.py` pattern as a template.
- Ordered as independently committable increments: fix classification → its tests → resolve serialization Unknown → generalized guardrail → live-discovery coverage confirmation → docs.

### Details

- Do not implement step 3's redesign path without the user's explicit decision — if unresolved at implementation time, implement only the "document as two distinct mechanisms" comment-only path and flag the redesign question as still open.
- Do not assume `repository_gateway.py`'s behavior is audit-only; verify by reading its full use of `classify_operation_type()`'s result before changing the function.
- The generalized guardrail test must not instantiate services with real DB/network dependencies at construction time unless reusing an existing fixture pattern that already isolates it (e.g., temp DB paths) — avoid inventing new service-construction logic.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/tool_policy.py tests/` | 0 errors |
| Type check | `uv run mypy scripts/agent/tool_policy.py` | no new errors |
| Fixed classification tests | `uv run pytest tests/test_tool_policy_comprehensive.py tests/test_tool_approval_risk.py -v` | all pass, including new MDQ/RAG/CICD/Git cases |
| Generalized guardrail tests | `uv run pytest tests/test_tool_server_layer_consistency.py -v` | all pass across all 8 servers |
| Repository gateway regression | `uv run pytest tests/test_repository_gateway.py -v` | no behavioral regression from the classification change |
| Audit field correctness (manual) | trigger an MDQ `index_paths` call in dev, inspect the resulting audit record's `operation_type` | `"write"`, not `"read"` |
| Full suite | `uv run pytest -v` | no new failures beyond pre-existing unrelated failures |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
