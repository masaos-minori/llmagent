# Align MDQ write approval, dry-run previews, and structured response metadata

## Goal
Make MDQ write approval risk match the operation, and give the two MDQ write tools a real dry-run preview that shares discovery, authorization, and the per-file decision with execution while performing no mutation.

## Priority
High

## Scope
- **In-Scope**:
  - The declared tier for `index_paths` and `refresh_index` moves to the tier that maps to `medium`, so MDQ writes prompt; forced refresh resolves to `high` through the existing `force` special case.
  - `dry_run` on the two MDQ write request models and their public input schemas, and the handlers routing a preview call to a no-write path.
  - Preview reporting planned add, update, delete, skip, warning, and failure counts from the same decision inputs as execution.
  - MDQ-specific approval preview formatting (common root and representative paths) in the agent display layer.
  - Pins that assert the current tier and preview capability; new per-mode approval-risk and dry-run tests.
  - Documentation alignment for the tier, the dry-run support list, and the mdq per-server section.
- **Out-of-Scope**:
  - The shared execution-context and dispatcher dry-run contract: already implemented, not redefined here.
  - Reordering `classify_risk()`'s `NONE` short-circuit globally: the MEDIUM floor makes the existing special-case and escalation branches reachable for MDQ without changing the order for other tools.
  - Changing the persistent audit payload shape (`resource_scope`), and the MEDIUM floor for non-MDQ write tools.
  - The MDQ file-identity, transaction-atomicity, and FTS5-schema work owned by the earlier plans.
- **Dependencies**: depends on the mdqmcp003 plan (the per-file result DTO and its statuses that the preview counts reuse) and on the mdqmcp005 plan (the caller-owned transaction that makes "no write transaction in preview" a defined boundary); follows the already-implemented execution-mode contract of the mcpai005 plan. Blocks mdqmcp008.
  - **Depends on**: `plans/20261127-163030_mdqmcp003_mdq-file-processing-outcomes.md` | all | the per-file DTO statuses, reason codes, and counters this Plan's preview counts reuse; the preview must not invent a second outcome vocabulary
  - **Depends on**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md` | all | the caller-owned transaction design: the preview path must run the decision logic without opening a write transaction on a connection it does not own
  - **Depends on**: `plans/done/20261125-121807_mcpai005_structured-execution-context.md` | all | already landed (`scripts/shared/execution_mode.py`, `scripts/mcp_servers/execution_context.py`, `scripts/mcp_servers/dispatch.py`); this Plan consumes the mode and preview-capability contract, it does not restate or extend it

## Background
Approval risk is supposed to match what a tool does, and the approval prompt is supposed to show what will change. MDQ writes modify indexed state but resolve to the lowest risk, so they are auto-approved, and their preview is a truncated argument dump with no planned effect. The safety-tier decision was moved into tool metadata by the agentcfg003 plan, so the tier declaration in the MDQ tool list is the place this change belongs.

## Problem
Verified against the source at the evidence revision:

- `index_paths` and `refresh_index` declare `agent_safety_tier: "WRITE_SAFE"` (`scripts/mcp_servers/mdq/mdq_tools.py:170,203`), which maps to `RiskLevel.NONE` through `_TIER_TO_RISK` (`scripts/agent/tool_policy.py:80-85`), so `classify_risk()` returns before the special-case and escalation checks (`489-490`): both tools are auto-approved.
- Forced refresh does not escalate because the `force` rule in `_special_case_risk()` (`394-396`) is unreachable for a `NONE` base, not because the rule is missing.
- Corrected claim: `config/agent.toml` does not set the tiers. The per-tool tier and risk maps were removed (ADR-002.02 Decision Detail 18); `config/agent.toml:186-187` are tool allowlist entries. The tiers live in tool metadata, so the change lands in `scripts/mcp_servers/mdq/mdq_tools.py`, not in configuration.
- Both tools declare `preview_capability: "none"` (`mdq_tools.py:175,208`), so the approval preview falls through to `_json_dumps(args)[:300]` (`scripts/agent/tool_result_formatter.py:131`): no file-level planned effects, and the display cannot show a common root or representative paths.
- The handlers do not read `dry_run` (`scripts/mcp_servers/mdq/mdq_server.py:264,272`), so a `dry_run=True` call performs a real write even though the dispatcher would report it as a preview.
- The preview path has no decision logic separated from the write path: `_refresh_changed_file()` and `_detect_deleted_files()` (`scripts/mcp_servers/mdq/indexer.py:304,258`) mutate `index_state` and delete rows inside the same call that decides.
- Corrected claim: the issue's "existing automatic-approval tests are replaced" — no MDQ-specific automatic-approval test exists. The pins that assert the current behavior are `tests/mcp_servers/mdq/test_mdq_routing.py::TestMdqSafetyTiers` (line 96) and `tests/agent/test_tool_policy.py::TestTierNoneGapProvenance` (line 2141), which lists `index_paths` and `refresh_index` as shipped tier-`NONE` tools.
- Corrected claim: absolute paths are persisted in audit today through the declared path-kind key joined with `;` (`scripts/agent/tool_audit.py:57-92`), which is the canonical audit contract. The display requirement does not change that contract (UNK-03).
- Amendment 2026-11-28: `scripts/agent/tool_policy.py` needs no classification change, but its `classify_risk()` docstring (line 464) names `index_paths` and `refresh_index` in the tier-`NONE` enumeration, so that enumeration becomes a stale claim when the tier changes; the file is a target row for the docstring alignment only.

## Reason for Change
User safety: an unreviewed write that changes indexed state is currently auto-approved, and the prompt shows no planned effect. The fail-closed path for a failed required preview already exists (`scripts/mcp_servers/dedup_gate.py:273`, `scripts/mcp_servers/dispatch.py:432-449`); the classification change is what activates it for MDQ.

## Implementation Intent
Express the MEDIUM floor as the declared tier, the single risk source, rather than as a new per-tool risk rule or a change to the classification order. Add `dry_run` to the MDQ write contracts and route preview calls to a decision-only path that shares discovery, authorization, and the per-file decision with execution and never opens a write transaction. Keep the approval display formatter separate from the persistent audit redaction path.

## Requirements
- `REQ-001`: `index_paths` and `refresh_index` declare the tier that maps to `medium` (`WRITE_DANGEROUS` under `_TIER_TO_RISK`), so MDQ writes reach an approval prompt.
- `REQ-002`: Forced refresh resolves to `high` through the existing `force` special case, and a protected in-jail path on either tool resolves to `high` through the existing path escalation; both become reachable because the base is no longer `NONE`. The lookup order in `classify_risk()` is not changed.
- `REQ-003`: `dry_run` is added to the two MDQ write request models and to their public input schemas, following the shared execution-mode contract; the handlers pass it through instead of ignoring it.
- `REQ-004`: The preview path runs the same discovery, authorization, and per-file decision as execution and performs no database write, no `index_state` change, no dedup acquisition, and no row deletion; authorization failure still denies before any decision output.
- `REQ-005`: The preview reports planned add, update, delete, skip, warning, and failure counts from the same decision inputs as execution, using the per-file DTO statuses from the mdqmcp003 plan; add and update are action labels derived from the decision, not new status vocabulary.
- `REQ-006`: The approval preview for the two tools shows the common root and representative paths instead of the full argument dump; the display formatter stays separate from the persistent audit redaction path and the audit payload shape is unchanged.
- `REQ-007`: Replace the pins that assert the current tier and capability, and add per-mode approval-risk tests, dry-run no-op tests, and preview/execution parity tests.
- `REQ-008`: Align the documentation that states the current tier, the dry-run support list, and the mdq per-server behavior.

## Implementation Target Files
**Freeze status**: Frozen — `issue-to-plan` Step 8's Implementation Target Files Validation passes (backtick and structure checks, `tools/audit_plan_target_paths.py`, `tools/check_plan_target_overlaps.py`).
Amended 2026-11-28 (fallout): added scripts/agent/tool_policy.py — Align the classify_risk() docstring's tier-NONE tool enumeration, which names index_paths and refresh_index as tier-NONE examples and becomes a stale claim once the declared tier changes

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_tools.py` | Modify | Declare the tier that maps to `medium` and `preview_capability: "dry_run"` for the two write tools, and add the `dry_run` boolean property to both input schemas | REQ-001, REQ-003, AC-1, AC-5 | `"agent_safety_tier": "WRITE_SAFE"` at lines 170 and 203, `"preview_capability": "none"` at lines 175 and 208; neither `inputSchema` has a `dry_run` property | `tests/mcp_servers/mdq/test_mdq_routing.py`, `tests/mcp_servers/mdq/test_mdq_tool_schema.py`, `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | Add `dry_run` to `IndexPathsRequest` and `RefreshIndexRequest`, and add the planned-outcome metadata model that carries the planned counts and the representative paths | REQ-003, REQ-005, AC-2, AC-3 | `IndexPathsRequest` (line 163) and `RefreshIndexRequest` (line 169) have no `dry_run` field; `IndexPathsMetadata` carries executed counters only | `tests/mcp_servers/mdq/test_mdq_dry_run.py` | Verified |
| `scripts/mcp_servers/mdq/indexer.py` | Modify | Separate the per-file decision from the write so the preview path runs discovery and decision without a write transaction, and produce the planned add/update/delete/skip/warning/failure counts | REQ-004, REQ-005, AC-2, AC-3 | `_refresh_changed_file()` (line 304) writes `index_state` inside the same call that decides; `_detect_deleted_files()` (line 258) deletes rows during discovery | `tests/mcp_servers/mdq/test_mdq_dry_run.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_index_delete.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | Honor `dry_run` on the two request models and return the planned metadata for a preview call | REQ-004, REQ-005, AC-2, AC-3 | `index_paths()` (lines 279-290) and `refresh_index()` (lines 293-305) call the writer unconditionally and return the executed metadata | `tests/mcp_servers/mdq/test_mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_dry_run.py` | Verified |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Pass `dry_run` from the call arguments into the two request models in the handlers | REQ-003, AC-2 | `_handle_index_paths()` (line 264) and `_handle_refresh_index()` (line 272) build requests from `paths` and `force` only, so a `dry_run=True` call executes for real | `tests/mcp_servers/mdq/test_mdq_dry_run.py`, `tests/mcp_servers/mdq/test_mdq_routing.py` | Verified |
| `scripts/agent/tool_result_formatter.py` | Modify | Add the MDQ write preview branch that renders the common root and representative paths from masked arguments | REQ-006, AC-4 | `build_preview()` (lines 109-131) has no mdq branch and falls through to `_json_dumps(args)[:300]` | `tests/agent/test_tool_result_formatter.py` | Verified |
| `tests/mcp_servers/mdq/test_mdq_routing.py` | Modify | Replace the `WRITE_SAFE` pins for the two write tools with the new tier | REQ-001, REQ-007, AC-1 | `TestMdqSafetyTiers` asserts `declared[tool_name] == "WRITE_SAFE"` for `index_paths` and `refresh_index` (lines 96-97) | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_tool_schema.py` | Modify | Add the `dry_run` property assertions for both write-tool schemas | REQ-003, REQ-007, AC-5 | `test_index_paths_and_refresh_index_paths_items_and_min_items` (line 75) pins `paths` only; no test pins a `dry_run` property | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Modify | Add the preview-capability pin for the two write tools | REQ-003, REQ-007, AC-5 | The file pins tool-list, dispatch, registry, `is_write`, and `requires_serial` consistency (lines 16-41) and has no capability pin | itself | Verified |
| `tests/mcp_servers/mdq/test_mdq_dry_run.py` | Create (new file) | Cover the dry-run no-op, authorization still enforced in preview, and preview/execution count parity | REQ-004, REQ-005, REQ-007, AC-2, AC-3 | No mdq dry-run test exists (`ls tests/mcp_servers/mdq/` lists 36 entries, none named for dry-run) | itself | Verified |
| `tests/agent/test_tool_policy.py` | Modify | Remove the two MDQ write tools from the shipped tier-`NONE` set and add the medium-base and force-escalation cases | REQ-001, REQ-002, REQ-007, AC-1 | `TestTierNoneGapProvenance.SHIPPED_NONE_TIER_TOOLS` lists `index_paths` and `refresh_index` (line 2141); `test_tier_none_short_circuits_escalation` (line 2122) pins the current order | itself | Verified |
| `tests/agent/test_tool_approval_risk.py` | Modify | Add per-mode approval-risk tests: index medium, normal refresh medium, forced refresh high, protected in-jail path high | REQ-002, REQ-007, AC-1 | `TestClassifyOperationType.test_mdq_rag_cicd_git_write_tools` (method at line 402, class at line 389) pins operation type only, with the two mdq names at lines 412-413; no test resolves MDQ risk per mode | itself | Verified |
| `tests/agent/test_tool_result_formatter.py` | Modify | Add the MDQ preview formatting tests: common root, representative paths, masked values, large path lists | REQ-006, REQ-007, AC-4 | Existing `build_preview` tests (`class TestBuildPreview` at line 198, tests at lines 199-226) cover write_file, edit_file, delete_file, delete_directory, create_directory, and move_file; no mdq case | itself | Verified |
| `docs/22_mcp/mcp_01_tool_ownership_matrix.md` | Modify | Update the mdq write row: tier and the approval column | REQ-001, REQ-008, AC-1 | Line 33 states `WRITE_SAFE` and "No by default (`none` via tier mapping)" | `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Modify | Add the two MDQ write tools to the Dry-Run Support list and align the `WRITE_SAFE` example row and the tier-`none` reachability counts | REQ-003, REQ-008, AC-5 | The Dry-Run Support section (heading line 69, list sentence line 72) names file-write, file-delete, shell, git, and cicd tools only; line 86 names `index_paths` as a `WRITE_SAFE` example and line 90 states that the 50 tier-`none` tools (39 `READ_ONLY` plus 11 `WRITE_SAFE`) never reach escalation, both of which change when the two tools move to `WRITE_DANGEROUS`; line 104 is the dry-run preview-injection note, not a tier statement | `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Document the mdq dry-run contract, the planned-count fields, and the preview display rule in the mdq per-server section | REQ-004, REQ-005, REQ-006, REQ-008, AC-2, AC-3, AC-4 | The mdq section has no dry-run or preview statement; the audit statement at line 68 describes the shared `mcp_tool_exec` record | `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py` | Verified |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Modify | Align the shipped-tier examples and the protected-path scope sentence, which name the MDQ write tools as tier-`NONE` tools that never escalate | REQ-002, REQ-008, AC-1 | Line 48 states a tier-derived `none` returns before overrides and escalation; line 91 lists the tools that escalate under the shipped tiers and excludes the mdq writes | `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_consistency.py --domain agent` | Verified |
| `scripts/agent/tool_policy.py` | Modify | Align the classify_risk() docstring's tier-NONE tool enumeration, which names index_paths and refresh_index as tier-NONE examples and becomes a stale claim once the declared tier changes | REQ-002, AC-1 | Docstring at line 464 lists 'index_paths, refresh_index, git_add, git_commit, write_file, edit_file, create_directory, move_file, every READ_ONLY tool' as tier-NONE tools that return before escalation; the tier change moves the two mdq tools out of that set | `tests/agent/test_tool_policy.py` | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/tool_approval.py` | `_declared_dry_run_capable()` (83) and `_build_preview_with_dry_run()` (125): the dry-run path activates by declaration, so no change is needed; the display layer must stay separate from audit | REQ-003, REQ-006 |
| `scripts/agent/tool_audit.py` | `_extract_resource_scope()` (57-92) and the args-preview envelope: the canonical audit shape is not changed by this Plan (UNK-03) | REQ-006, AC-4 |
| `scripts/shared/execution_mode.py` | `resolve_execution_mode()` (27-54): the shared contract that decides `preview` from the declared capability and the `dry_run` argument | REQ-003 |
| `scripts/mcp_servers/execution_context.py` | `configure_tool_preview_capabilities()` (63-79): the seam that registers the declared capability at server bootstrap | REQ-003 |
| `scripts/mcp_servers/dispatch.py` | The preview branch (432-449): a preview never acquires dedup, so the mdq preview path must not create durable state | REQ-004 |
| `scripts/mcp_servers/mdq/auth.py` | `authorize_path()`: authorization must run in preview exactly as in execution | REQ-004 |
| `scripts/mcp_servers/mdq/index_scan.py` | `iter_indexable_files()`: the discovery the preview path reuses; no change is needed because it holds no database access | REQ-004 |
| `config/agent.toml` | Lines 186-187 are tool allowlist entries, not tier settings: read to confirm the issue's stale claim and that no configuration row is a target | REQ-001 |
| `tests/mcp_servers/conftest.py` | The preview-capability bootstrap seam (66-94) that endpoint tests rely on to resolve `dry_run` as `preview` | REQ-004 |
| `tests/mcp_servers/test_tool_schema_contract.py` | The tool field-set contract (line 40): `preview_capability` presence is already asserted, so no change is needed | REQ-003 |
| `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` | The mdq enforcement and lockdown section, read to confirm the per-layer status statement does not change | REQ-008 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): `index_paths` and a non-forced `refresh_index` resolve to `medium`; `force=True` and a protected in-jail path resolve to `high`. No MDQ write is auto-approved.
- `AC-2` (REQ-004): a dry-run call performs no database write, no `index_state` change, no row deletion, and no dedup acquisition, and reports `execution_mode="preview"` with `side_effect_applied=False`; an unauthorized path is still denied in preview.
- `AC-3` (REQ-005): with the filesystem and index state unchanged between the preview and the subsequent execution, the planned counts equal the executed counts.
- `AC-4` (REQ-006): the approval preview shows the common root and representative paths, and the persistent audit payload shape is unchanged.
- `AC-5` (REQ-003, REQ-007): the pins that asserted the current tier and capability are replaced, the new tests pass, and the full validation sequence passes.

## Tests
- Approval-risk tests per mode: index medium, normal refresh medium, forced refresh high, protected in-jail path high (REQ-002, AC-1; `tests/agent/test_tool_approval_risk.py`, `tests/agent/test_tool_policy.py`).
- Tier and capability pins updated, plus a new capability pin for the two write tools (REQ-001, REQ-003, AC-5; `tests/mcp_servers/mdq/test_mdq_routing.py`, `tests/mcp_servers/mdq/test_mdq_tool_schema.py`, `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`).
- Dry-run no-op tests: no write transaction, no `index_state` change, no dedup row, authorization enforced (REQ-004, AC-2; `tests/mcp_servers/mdq/test_mdq_dry_run.py`).
- Preview/execution parity tests, including a directory case and a large path list (REQ-005, AC-3; `tests/mcp_servers/mdq/test_mdq_dry_run.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`, `tests/mcp_servers/mdq/test_index_delete.py`).
- Preview formatting tests: common root, representative paths, masked values, and the separation from the audit redaction path (REQ-006, AC-4; `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_tool_audit.py` unchanged as a guard).
- Run the full validation sequence: `uv run python tools/run_validation_gates.py`, `uv run lint-imports`, then `uv run pytest` (`rules/toolchain.md`).

## Documentation Impact
Yes. Per `docs/00_index.md` "Document References by Task":
- The high-risk MCP tool policy row (approval-to-risk-tier mapping) drives `docs/22_mcp/mcp_01_tool_ownership_matrix.md`, which is the canonical mapping that states the mdq write tier and the approval consequence.
- The mdq-mcp specifics row drives `docs/22_mcp/mcp_04_04_mdq.md` (the dry-run contract, the planned-count fields, and the preview display rule).
- The Agent tool-execution row drives `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`, which is the canonical source for the evaluation order and the shipped-tier examples that name the mdq writes as tier-`NONE`; the order itself does not change, only the tools named under it.
- `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` is the canonical Dry-Run Support list and must name the two mdq write tools.
- No new design document is created: the dry-run contract already has canonical docs, and the MDQ-specific behavior belongs in the mdq per-server section named by the task mapping. A separate MDQ design document would require registration in `docs/00_index.md` and `docs/22_mcp/mcp_00_document-guide.md` and is left as a maintainer decision (UNK-04). No ADR change: an ADR change needs a maintainer approval record (governance_01, governance_05) and is not written or simulated here.
- Doc content policy applies: the per-file status vocabulary and the reason codes are closed and are not extended; run `uv run python tools/check_docs_content_policy.py` and `uv run python tools/check_docs_structure.py` per `rules/tool-gates.md`.

## Assumptions
- The MEDIUM floor is expressed as the declared tier, because the per-tool risk maps were removed by an adopted decision and the declared tier is the single risk source; `WRITE_DANGEROUS` is the only tier in the closed vocabulary that maps to `medium`.
- The classification lookup order is not changed: the floor makes the existing `force` special case and path escalation reachable for MDQ. A global reorder would change behavior for every tier-`NONE` tool, which is a policy decision outside this Plan (UNK-02).
- The preview path never opens a write transaction; it reads `index_state` for the decision, which is a read-only operation and does not need the mdqmcp005 transaction owner.
- Add and update are preview action labels derived from the decision (file absent from `index_state` versus present with a changed mtime), not new DTO statuses; the mdqmcp003 status vocabulary is not extended.
- The documented dependency hierarchy restricts `agent` to `mcp_servers` through the installer only, and the import-linter contract `agent-mcp-config-models` forbids the four producer config models but not `mcp_servers.mdq.mdq_models` (`scripts/agent/services/mcp_tool_discovery_fetch.py:29` already imports `mcp_servers.server`). So the MDQ preview formatter not importing mdq models is a hierarchy-convention choice, not a contract-enforced one, and it works from masked arguments only.
- Bus factor is 1 for both the mdq module set and the agent files: the recorded author names (`Masao SUGIMOTO`, `Masao Sugimoto`, `Sugimoto Masao`, `sugimoma-c`) are name variants of one person across two email addresses (`sugimoma@gmail.com`, `sugimoto.masao@scskminori.co.jp`), so the Affected areas column reports distinct recorded addresses, not distinct people.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether a reviewed exception to the MEDIUM floor exists for any write tool, and whether the floor applies beyond MDQ | No owner decision recorded; the floor as written in the issue would move every `WRITE_SAFE` tool to `medium` if applied through `_TIER_TO_RISK` | Plan default: apply the floor to the two MDQ write tools only; confirm the general policy with the maintainer before widening it | False |
| UNK-02 | Whether `classify_risk()` should evaluate the force flag and protected paths before the `NONE` short-circuit for tools that remain `NONE` | No owner decision recorded; the canonical policy doc states the current order as a design decision | Plan default: keep the order and satisfy the requirement through the tier floor for MDQ; a global reorder needs the approval-policy owner | False |
| UNK-03 | Whether the persistent audit `resource_scope` shape must change so absolute path lists are not persisted | The canonical audit contract records path-kind list values joined with `;` (`scripts/agent/tool_audit.py:57-92`); no document records the alternative | Plan default: the display layer shows the common root and representative paths and the audit shape is unchanged; a change to the audit payload needs the audit contract owner | False |
| UNK-04 | Whether a separate MDQ dry-run design document is required, and where it would be registered | No mdq design document exists; the dry-run contract is documented in `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` and `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Plan default: document the mdq-specific behavior in the mdq per-server section; a new file needs registration in `docs/00_index.md` and the MCP document guide | False |
| UNK-05 | The preview metadata field names, which must stay consistent with the shared result metadata contract | The shared contract defines `execution_mode` and `side_effect_applied` only; the planned-count field names are not defined by it | Plan default: name the planned counts after the mdqmcp003 counters with a `planned_` prefix and keep the shared fields unchanged; confirm with the shared-contract owner before publishing them as a public shape | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_tools.py` | Modify | MDQ write tools only; the tier and capability declarations are read by approval classification, plan-mode blocking, and the preview seam | 1 | 1 | None |
| `scripts/mcp_servers/mdq/mdq_models.py` | Modify | mdq service and handler layer; new optional field and new metadata model | 0 | 1 | None |
| `scripts/mcp_servers/mdq/indexer.py` | Modify | mdq indexing and refresh flow; the decision path is split from the write path | 0 | 1 | None |
| `scripts/mcp_servers/mdq/mdq_service.py` | Modify | mdq service callers and the audit detail builder that reads metadata keys | 1 | 1 | None |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | mdq handler dispatch for two tools | 6 | 3 | None |
| `scripts/agent/tool_result_formatter.py` | Modify | Every approval preview display; the change adds one tool branch and leaves the fallback path intact | 2 | 1 | None |
| `docs/22_mcp/mcp_01_tool_ownership_matrix.md` | Modify | Documentation only | — | 1 | None |
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Modify | Documentation only | — | 1 | None |
| `docs/22_mcp/mcp_04_04_mdq.md` | Modify | Documentation only | — | 1 | None |
| `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Modify | Documentation only | — | 1 | None |
| `scripts/agent/tool_policy.py` | Modify | Documentation inside the module only: the `classify_risk()` docstring enumeration; no classification behavior changes | 10 | 1 | None |

## Design
Path B classification rationale: a cross-module change (agent layer plus mdq layer), more than three files, and a semantic change to the risk-classification outcome for the two MDQ write tools.

Design decisions (narrow `python-design` application):
- Risk source: the declared tier is the single risk source, so the floor is expressed as the tier declaration in `scripts/mcp_servers/mdq/mdq_tools.py`. Alternative considered — a per-tool risk rule or a configuration map; rejected, those maps were removed by an adopted decision (ADR-002.02.003 Decision Details #2, #8, #9, #14, agentcfg003, recorded in `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` and cited by `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` line 48) and re-adding one would contradict the canonical approval doc.
- Tier choice: `WRITE_DANGEROUS` is the only tier in the closed vocabulary that maps to `medium`. Alternative considered — change `_TIER_TO_RISK["WRITE_SAFE"]` to `medium`; rejected because it moves every `WRITE_SAFE` tool (file writes, git writes) at once, which is a policy decision requiring an owner record (UNK-01). Alternative considered — add a new tier value; rejected, the tier vocabulary is closed and validated at registration.
- Lookup order: unchanged. The issue's requirement to evaluate force and protected paths before the `NONE` short-circuit is satisfied for MDQ by the floor, which makes the base non-`NONE`. A global reorder would change behavior for every tier-`NONE` tool, including `READ_ONLY` tools with path arguments, and contradicts the canonical policy statement and `tests/agent/test_tool_policy.py::test_tier_none_short_circuits_escalation` (UNK-02).
- Preview shape: the preview path reuses `iter_indexable_files()` and the per-file decision, and reads `index_state` for comparison; it never calls the writer, so it never opens a write transaction on a connection it does not own. Alternative considered — run the writer with a rollback; rejected, a rollback is still a write transaction and the mdqmcp005 design makes transaction ownership explicit.
- Preview counts: derived from the decision, using the mdqmcp003 statuses and reason codes; add and update are action labels, not new statuses, so the closed vocabulary is not extended. Preview and execution parity is asserted by running the decision twice against an unchanged filesystem and index state.
- Display versus audit: the formatter change is display-only. The agent layer must not import `mcp_servers` (import-linter contract), so the formatter derives the common root and representative paths from masked arguments, not from mdq models. The persistent audit path (`_extract_resource_scope`, the args-preview envelope) is not modified (UNK-03).
- Consumer scan: `classify_risk()` consumers are `scripts/agent/tool_approval.py` (253, 380) and `scripts/agent/production_config_validator.py` (108-111); the validator's fail-safe statement about an unknown tool is unaffected. `build_preview()` consumers are `scripts/agent/tool_approval.py` (122) only. `_extract_resource_scope()` consumers are `scripts/agent/tool_audit.py` (138, 280). No consumer asserts the mdq tier value except the pins listed as target rows.
- Predictable fallout: module size — all target source files are under the 24576 B gate (largest `scripts/mcp_servers/mdq/mdq_server.py` at 20547 B; `scripts/agent/tool_policy.py` at 22975 B is a target row for a docstring-only change); pinned counts — `tests/mcp_servers/mdq/test_mdq_routing.py` pins the tier set and `tests/agent/test_tool_policy.py` pins the shipped tier-`NONE` tool list, both target rows; tool inventory — the field set contract is unchanged, only values; generated blocks — the doc edits are prose, and `uv run python tools/generate_reference_table.py --check` is run as a validation gate.
- Import graph: `uv run lint-imports` reports 6 contracts kept (re-run at the current revision). No contract forbids `agent → mcp_servers`; the `.importlinter` hierarchy comment allows that edge for the installer only, so the formatter change adds no cross-layer import by convention, and the mdq layer continues to import only `db` and `shared`. Radon worst-function grades at the current revision: `mdq_tools.py` has no function blocks, `mdq_models.py` and `indexer.py` are grade A, `mdq_service.py` and `tool_result_formatter.py` are grade B, `mdq_server.py` is grade C (`_build_call_tool_audit_detail`, C 11); the decision split keeps the new preview helper a small function. Bandit (medium and above) and vulture (min-confidence 80) on the target modules: no findings at the current revision. Churn (30d, re-run at the current revision) and bus factor are recorded in the Affected areas table.

## Implementation steps
1. **Phase 1: Characterization tests first**
   - [ ] Pin the current behavior before any change: the mdq tier pins, the shipped tier-`NONE` provenance set, and the current preview fallback (REQ-007, AC-5; `tests/mcp_servers/mdq/test_mdq_routing.py`, `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_result_formatter.py`)
2. **Phase 2: Approval risk**
   - [ ] Declare the tier that maps to `medium` for the two write tools (REQ-001; `scripts/mcp_servers/mdq/mdq_tools.py`)
   - [ ] Add the per-mode risk tests: index medium, normal refresh medium, forced refresh high, protected in-jail path high, and remove the two tools from the tier-`NONE` set (REQ-002, AC-1; `tests/agent/test_tool_approval_risk.py`, `tests/agent/test_tool_policy.py`)
   - [ ] Modify (REQ-002; `scripts/agent/tool_policy.py`) — amendment 2026-11-28
3. **Phase 3: Dry-run contract and preview path**
   - [ ] Add `dry_run` to the two request models and to both public input schemas, and add the planned-outcome metadata model (REQ-003, AC-5; `scripts/mcp_servers/mdq/mdq_models.py`, `tests/mcp_servers/mdq/test_mdq_tool_schema.py`, `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`)
   - [ ] Pass `dry_run` from the call arguments into the request models in the two handlers (REQ-003, AC-2; `scripts/mcp_servers/mdq/mdq_server.py`)
   - [ ] Split the per-file decision from the write so the preview path runs discovery, authorization, and decision without a write transaction, and produce the planned counts (REQ-004, REQ-005, AC-2, AC-3; `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/mdq_service.py`)
   - [ ] Add the dry-run no-op, authorization, and parity tests in a new test file (REQ-004, REQ-005, AC-2, AC-3; `tests/mcp_servers/mdq/test_mdq_dry_run.py`)
4. **Phase 4: Preview display**
   - [ ] Add the MDQ write preview branch that renders the common root and representative paths from masked arguments (REQ-006, AC-4; `scripts/agent/tool_result_formatter.py`)
   - [ ] Add the display tests for common root, representative paths, masked values, and a large path list, and confirm the audit redaction path is unchanged (REQ-006, AC-4; `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_tool_audit.py`)
5. **Phase 5: Documentation and full validation**
   - [ ] Align the tool-ownership row, the Dry-Run Support list, the mdq per-server section, and the approval doc's shipped-tier examples (REQ-008, AC-1, AC-4, AC-5; `docs/22_mcp/mcp_01_tool_ownership_matrix.md`, `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `docs/22_mcp/mcp_04_04_mdq.md`, `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`)
   - [ ] Deployment check: no `deploy.sh` or `deploy/init_db.sh` gate is affected; confirm the mdq service starts with the new capability declaration and that the preview seam resolves `dry_run` as `preview` in an endpoint test (REQ-003, REQ-004; `scripts/mcp_servers/mdq/mdq_server.py`)
   - [ ] Run the full validation sequence: `uv run python tools/run_validation_gates.py`, `uv run lint-imports`, then `uv run pytest` (all requirements)

### Release units
**Unit**: tier change and its pins | **Phases**: 2 | **Reason**: the tier declaration and the pins that assert it are in the same phase, but the risk tests in Phase 2 fail until the declaration lands, so the declaration and the pins cannot be validated separately.
**Unit**: preview path | **Phases**: 3 | **Reason**: the request model field, the handler pass-through, and the decision split must land together: a `dry_run` field without the handler pass-through performs a real write, and the parity test cannot pass until both land.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/mdq/mdq_tools.py` | Unit: declared tier and capability values, schema property presence | `uv run pytest tests/mcp_servers/mdq/test_mdq_routing.py tests/mcp_servers/mdq/test_mdq_tool_schema.py tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | The two write tools resolve to `medium` and declare `dry_run` |
| `scripts/mcp_servers/mdq/indexer.py` | Integration: decision-only path against a scratch store, no write transaction | `uv run pytest tests/mcp_servers/mdq/test_mdq_dry_run.py tests/mcp_servers/mdq/test_mdq_incremental_refresh.py tests/mcp_servers/mdq/test_index_delete.py` | Preview performs no mutation; counts match a subsequent execution |
| `scripts/mcp_servers/mdq/mdq_service.py` | Unit: `dry_run` honored, planned metadata returned | `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py tests/mcp_servers/mdq/test_mdq_dry_run.py` | Preview reports planned counts with `side_effect_applied=False` |
| `scripts/mcp_servers/mdq/mdq_server.py` | Integration: handler pass-through through the dispatch preview branch | `uv run pytest tests/mcp_servers/mdq/test_mdq_dry_run.py tests/mcp_servers/mdq/test_mdq_routing.py` | A `dry_run=True` call is resolved as `preview` and never writes |
| `scripts/agent/tool_result_formatter.py` | Unit: MDQ preview branch, masked values, large path list | `uv run pytest tests/agent/test_tool_result_formatter.py tests/agent/test_tool_audit.py` | Display shows common root and representative paths; audit shape unchanged |
| `scripts/agent/tool_policy.py` | Unit: risk per mode, force escalation, protected path; the docstring enumeration is aligned by the amended row | `uv run pytest tests/agent/test_tool_approval_risk.py tests/agent/test_tool_policy.py` | Index and normal refresh `medium`, forced refresh and protected path `high` |
| Docs rows | Content policy, structure, cross-check | `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain mcp`, `uv run python tools/check_docs_consistency.py --domain agent` | Pass |
| Whole module | Lint, types, security, import contracts | `uv run python tools/run_validation_gates.py`, `uv run lint-imports` | Pass; 6 contracts kept |

## Risks
- **Risk**: the tier change moves MDQ writes from auto-approval to a prompt, which changes operator workflow for every MDQ write and blocks them in plan mode as before → **Mitigation**: the change is the intended behavior; the plan-mode block is already in place (`tests/agent/test_tool_approval_preflight.py`, `test_plan_mode_blocks_every_non_read_only_tool` at line 991, whose parametrize list names `index_paths` at line 987 but not `refresh_index`, so the block for `refresh_index` rests on the tier mapping alone), and the prompt path is the existing one, not a new mechanism.
- **Risk**: a preview that shares the decision logic could still mutate state if the writer is reached → **Mitigation**: the preview path never calls the writer; the no-op test asserts no `index_state` change, no row deletion, and no dedup acquisition.
- **Risk**: preview and execution counts can diverge when the filesystem changes between them → **Mitigation**: parity is asserted only under an unchanged filesystem and index state in the test, and the preview output names its counts as planned, not executed.
- **Risk**: the display formatter cannot import the mdq models (import-linter contract), so the common root must be derived from masked arguments, which may not reflect the server-side decision → **Mitigation**: the display shows the requested paths' common root and representative entries; the planned counts come from the tool result metadata, and the formatter does not claim server-side decision detail it cannot see.
- **Risk**: the issue's requirement to reorder the `NONE` short-circuit is not implemented, so tools that remain tier-`NONE` still never escalate → **Mitigation**: recorded as UNK-02 with the canonical policy doc named; the Plan satisfies the MDQ scope through the floor and does not change behavior for other tools without an owner decision.
- **Risk**: cross-plan target overlap — `docs/22_mcp/mcp_04_04_mdq.md` (mdqmcp001, mdqmcp002, mdqmcp003, mdqmcp004, mdqmcp005, mdqmcp006), `scripts/mcp_servers/mdq/mdq_models.py` (mdqmcp001, mdqmcp002, mdqmcp003, mdqmcp004), `scripts/mcp_servers/mdq/indexer.py` (mdqmcp003, mdqmcp004, mdqmcp005), `scripts/mcp_servers/mdq/mdq_service.py` (mdqmcp001, mdqmcp003, mdqmcp004), `scripts/mcp_servers/mdq/mdq_tools.py` (mdqmcp001, mdqmcp005), `scripts/mcp_servers/mdq/mdq_server.py` (mdqmcp001) — reported by `tools/check_plan_target_overlaps.py` → **Mitigation**: compatible ordering overlaps, not design conflicts. This Plan consumes the vocabularies those plans define rather than redefining them: the per-file statuses and counters from mdqmcp003, the transaction ownership from mdqmcp005, the error codes and per-tool availability from mdqmcp001, and the search models from mdqmcp002. The responsibilities are distinct per file — `mdq_tools.py` here changes only the tier and capability values, while mdqmcp001 changes `config_dependent` and mdqmcp005 changes the retry-policy reference; `mdq_server.py` here changes only the two handlers' argument pass-through, while mdqmcp001 changes the availability check and audit boundary. Execution order follows the dependency bullets; the judgement is recorded by the overlap check.
- **Risk**: the audit payload requirement in the issue conflicts with the canonical audit contract → **Mitigation**: the Plan changes only the display layer and records the audit-shape question as UNK-03 for the contract owner.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization tests first | In Progress | — | — | Tier pins, tier-`NONE` provenance set, and preview fallback pinned before behavior change |
| 2 | Phase 2: approval risk | In Progress | — | — | Tier declaration and per-mode risk tests |
| 3 | Phase 3: dry-run contract and preview path | In Progress | — | — | `dry_run` on models and schemas, handler pass-through, decision split, parity tests |
| 4 | Phase 4: preview display | In Progress | — | — | MDQ preview branch in the display formatter; audit path unchanged |
| 5 | Phase 5: documentation and full validation | In Progress | — | — | Docs alignment, endpoint preview-seam check, full validation sequence |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261128-043728_01_scripts_mcp_servers_mdq_mdq_tools.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-043728_02_scripts_mcp_servers_mdq_mdq_models.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-043728_03_scripts_mcp_servers_mdq_indexer.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-043728_04_scripts_mcp_servers_mdq_mdq_service.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-043728_05_scripts_mcp_servers_mdq_mdq_server.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-043728_06_scripts_agent_tool_result_formatter.py.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261128-043728_07_tests_mcp_servers_mdq_test_mdq_routing.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261128-043728_09_tests_mcp_servers_mdq_test_mdq_tool_layer_consistency.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261128-043728_10_tests_mcp_servers_mdq_test_mdq_dry_run.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261128-043728_11_tests_agent_test_tool_policy.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261128-043728_12_tests_agent_test_tool_approval_risk.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261128-043728_14_docs_22_mcp_mcp_01_tool_ownership_matrix.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261128-043728_15_docs_22_mcp_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261128-043728_16_docs_22_mcp_mcp_04_04_mdq.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261128-043728_17_docs_23_agent_agent_06_02_tool-execution-and-approval-approval.md.md` | 5 | Procedure | Pending | — | — |
| `implementations/20261128-043728_18_scripts_agent_tool_policy.py.md` | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-173835
- **Evidence revision**: 41b423e73a5c2d98ae017a67a6059fcb3c75fd81
- **Related target files**: `scripts/mcp_servers/mdq/mdq_tools.py`, `scripts/mcp_servers/mdq/mdq_models.py`, `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/agent/tool_result_formatter.py`, `tests/mcp_servers/mdq/test_mdq_routing.py`, `tests/mcp_servers/mdq/test_mdq_tool_schema.py`, `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`, `tests/mcp_servers/mdq/test_mdq_dry_run.py`, `tests/agent/test_tool_policy.py`, `tests/agent/test_tool_approval_risk.py`, `tests/agent/test_tool_result_formatter.py`, `docs/22_mcp/mcp_01_tool_ownership_matrix.md`, `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `docs/22_mcp/mcp_04_04_mdq.md`, `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`, `scripts/agent/tool_policy.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; set index and normal refresh to MEDIUM | `scripts/mcp_servers/mdq/mdq_tools.py` | Phase 2 | AC-1 | `tests/mcp_servers/mdq/test_mdq_routing.py` | Confirmed by repository evidence |
| REQ-001 | Problem; MDQ writes are automatically approved | `tests/mcp_servers/mdq/test_mdq_routing.py` | Phase 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Corrected claim; the tiers are tool metadata, not `config/agent.toml` settings | `tests/agent/test_tool_policy.py` | Phase 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-002 | Required Changes; forced refresh HIGH — reached through the existing `force` special case once the declared tier is no longer `NONE` | `scripts/mcp_servers/mdq/mdq_tools.py` | Phase 2 | AC-1 | `tests/agent/test_tool_approval_risk.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; evaluate force and protected paths before the NONE short-circuit — satisfied by the floor, order unchanged | `tests/agent/test_tool_policy.py` | Phase 2 | AC-1 | itself | Confirmed by repository evidence (UNK-02) |
| REQ-003 | Required Changes; add `dry_run` to MDQ write requests and public schemas | `scripts/mcp_servers/mdq/mdq_models.py` | Phase 3 | AC-5 | `tests/mcp_servers/mdq/test_mdq_tool_schema.py` | Confirmed by repository evidence |
| REQ-003 | Problem; the handlers ignore `dry_run` | `scripts/mcp_servers/mdq/mdq_server.py` | Phase 3 | AC-2 | `tests/mcp_servers/mdq/test_mdq_dry_run.py` | Confirmed by repository evidence |
| REQ-004 | Constraints; dry-run performs no database or state mutation | `scripts/mcp_servers/mdq/indexer.py` | Phase 3 | AC-2 | `tests/mcp_servers/mdq/test_mdq_dry_run.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; share scan, authorization, and decision logic | `scripts/mcp_servers/mdq/mdq_service.py` | Phase 3 | AC-2 | `tests/mcp_servers/mdq/test_mdq_dry_run.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; return planned add, update, delete, skip, warning, and failure counts | `scripts/mcp_servers/mdq/mdq_models.py` | Phase 3 | AC-3 | `tests/mcp_servers/mdq/test_mdq_dry_run.py` | Confirmed by repository evidence |
| REQ-005 | Acceptance Criteria; preview counts match subsequent execution decisions | `scripts/mcp_servers/mdq/indexer.py` | Phase 3 | AC-3 | `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; show common roots and representative paths, and keep the approval display separate from the persistent audit redaction path, which is not modified (`scripts/agent/tool_audit.py` is a reference file and `tests/agent/test_tool_audit.py` an unchanged guard) | `scripts/agent/tool_result_formatter.py` | Phase 4 | AC-4 | `tests/agent/test_tool_result_formatter.py`, `tests/agent/test_tool_audit.py` (guard) | Confirmed by repository evidence (UNK-03) |
| REQ-007 | Acceptance Criteria; existing automatic-approval tests are replaced — the actual pins are the tier pins | `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` | Phase 1 | AC-5 | itself | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; safety tiers, approval rules, preview fields, and caveats | `docs/22_mcp/mcp_01_tool_ownership_matrix.md` | Phase 5 | AC-1 | `uv run python tools/check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; the dry-run support list | `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Phase 5 | AC-5 | `uv run python tools/check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; the mdq per-server section | `docs/22_mcp/mcp_04_04_mdq.md` | Phase 5 | AC-2 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact; the shipped-tier examples in the canonical approval doc | `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` | Phase 5 | AC-1 | `uv run python tools/check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-002 | Amendment 2026-11-28: Align the `classify_risk()` docstring's tier-`NONE` tool enumeration, which names `index_paths` and `refresh_index` as tier-`NONE` examples and becomes a stale claim once the declared tier changes | `scripts/agent/tool_policy.py` | Phase 2 | AC-1 | `tests/agent/test_tool_policy.py` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261128-043728 -->