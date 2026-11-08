## Goal
Make the COMPAT stage of the compatibility-leftover checker match case-insensitively — one `re.IGNORECASE` flag on the single search call in `check_compat_patterns` — and anchor the one pattern whose case-insensitive form collides with live identifiers, so capitalized leftovers such as the adapter's "Backward-compatible alias" block are caught by CI (`REQ-001`/`REQ-002`/`REQ-003`).

## Scope
**Release unit**: wfaudit012-full

- Covers Plan `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md` row 1 only: `tools/check_compat_shims.py`.
- Companion file in this procedure (same row's Change Responsibility): `tools/TOOL_DESCRIPTIONS.md` rows 83 and 174, which describe the checker's matching semantics.

## Assumptions
- `wfaudit008` (`implementations/20261108-162804_01_scripts_agent_workflow_engine_adapter.py.md`, `implementations/20261108-162804_02_tests_agent_test_orchestrator.py.md`) lands before this procedure. If 012 lands first, the five adapter findings (`scripts/agent/workflow_engine_adapter.py` L106, L121, L128, L135, L144) stay red until 008 deletes that block, and the green-run gate below cannot pass.
- Procedures 03-09 of the same plan land in the same change unit: `tests/tools/test_check_compat_shims.py::TestProductionCategoryZero::test_real_repo_manifest_passes` runs the checker against the live repository and asserts exit code 0 (verified failing with 19 findings when only `re.IGNORECASE` is applied, 2026-11-08). The strict flip cannot land alone.
- `COMPAT_PATTERNS` maps pattern name to a raw pattern string, not a compiled object, so `re.IGNORECASE` must be passed at the call site and the `_MCP_TOOLS` edit is a string edit.

## Design decisions
- Flag at the call site (`re.search(pattern, stripped, re.IGNORECASE)` at L631) instead of compiling with flags or case-folding the line: one edit covers all 84 patterns, the reported line text stays byte-identical, and folding the line would break the uppercase-literal patterns (`_MCP_TOOLS` L79, "Workflow mode=disabled" log L109).
- The sibling ADR stage keeps its own case-sensitive call (`re.search(pattern, stripped)` at L650 in `check_adr_prohibited_patterns`) — out of scope, unchanged. A global search-and-replace on that call text would change two loops; the edit must target the `for pattern_name, pattern in COMPAT_PATTERNS.items():` block at L630-634 only.
- Anchor only the colliding entry: `_MCP_TOOLS` (L79) becomes `\b_MCP_TOOLS\b`. 49 of the 84 entries already lack `\b` and several already use it (`\ballow_startup_fallback\b` L103), so this follows existing style. No other entry needs anchoring: the ground-truth census produced identifier collisions only for `_MCP_TOOLS`.
- No new `[[compatibility_exceptions]]` entry in `tools/compat_exceptions.toml` and no change to `[checker_self_reference]`: the census shows no finding that an exemption could legitimately cover.

## Alternatives considered
- Case-fold `stripped` before matching: rejected — breaks uppercase-literal patterns (Plan Notes 2026-11-08).
- Compile every pattern with `re.IGNORECASE` at import time: rejected — larger diff (84 entries or a comprehension rewrite) for the same semantics, and it would also change how `check_removed_name_reintroduction` and the doc-symbol stage read the same dicts.
- Allowlist the seven identifier-collision files: rejected — they name live identifiers (`_cmd_mcp_tools` is the current MCP-list command method, `scripts/agent/commands/cmd_mcp.py:287`) or test names, not retired mechanisms; an exemption entry would misrepresent them and add manifest debt.

## Implementation
### Target file
`tools/check_compat_shims.py`

### Procedure
Two edits in one file: anchor the `_MCP_TOOLS` pattern string (L79), then add `re.IGNORECASE` to the COMPAT search call (L631). Then update the two companion description rows in `tools/TOOL_DESCRIPTIONS.md`.

### Method
- L79: `"_MCP_TOOLS": r"_MCP_TOOLS",` becomes `"_MCP_TOOLS": r"\b_MCP_TOOLS\b",`. Key name and dict order unchanged.
- L631 (inside `check_compat_patterns`, loop L628-634): `if re.search(pattern, stripped):` becomes `if re.search(pattern, stripped, re.IGNORECASE):`. The finding message text (L632-634) and the allowlist short-circuit (L624-625) are untouched.
- Companion rows in `tools/TOOL_DESCRIPTIONS.md`: row 83 (Consistency checker) and row 174 (full description) state that the COMPAT patterns match case-insensitively, and that identifier-shaped entries carry word-boundary anchors so a retired name is not matched inside a longer live identifier. Post-change wording describes the new semantics only; no history sentence.

### Details
- Everything else stays byte-identical: `_REMOVED_NAME_PATTERNS` (L383-467) and its historical-context exemption (`_is_historical_context` L486-496, fold at L494, applied at L571/L599), `_NEGATED_SERVER_CONFIGS_RE` (L481), the AST rules (`check_mcp_health_reexport_import` L510, `check_gateless_discovery_construction` L531), `check_doc_symbols`, CLI flags, exit-code behavior, and manifest validation.
- Expected census after both edits (verified 2026-11-08 by applying both edits in the working tree, running the CI command, then reverting): 12 findings — 5 adapter findings owned by `wfaudit008` plus the 7 findings procedures 03-09 fix (`audit_event_emitter.py:31`, `bg_task_monitor.py:150`, `conversation_state_manager.py:32`, `llm_turn_executor.py:54`, `cicd_service.py:4`, `github_models.py:4`, `agent_10_01_operations-and-observability-startup-and-health.md:50`). The 7 `_MCP_TOOLS` identifier findings that appear without the anchors (`scripts/agent/commands/cmd_mcp.py:283`/`:287`, `tests/agent/commands/test_command_def_sync.py:22`, `tests/mcp_servers/file/test_mcp_tools_validation.py:1`, `tests/mcp_servers/git/test_tools_endpoint.py:8`, `tests/mcp_servers/test_tool_schema.py:9`, `tests/mcp_servers/test_mcp_server_base.py:204`) are gone.

## Compatibility considerations
- Strictening a CI gate is a repo-wide compatibility event: every finding the new semantics reveal must be closed in the same change unit (procedures 03-09 plus `wfaudit008`) or `TestProductionCategoryZero::test_real_repo_manifest_passes` and the `check-compat-shims` pre-commit hook block the commit.
- CI wiring is unchanged (`REQ-004`): `.github/workflows/backward-compat-check.yml:39` and the `check-compat-shims` hook already pass `--check-removed-names --check-doc-symbols`, and both already trigger on this file.
- Patterns matching case-insensitively can also match prose in scanned `docs/*.md`; the census bounds the effect at the one docs line procedure 09 rewords.

## Security considerations
- No new input surface, no subprocess, no path handling change; the checker stays read-only.
- Broadening matching reduces the chance that a stale compatibility shim slips through review unflagged.

## Rollback considerations
- Revert the commit: two-line revert in `tools/check_compat_shims.py` plus the two `tools/TOOL_DESCRIPTIONS.md` rows. No data or manifest state to unwind; `tools/compat_exceptions.toml` is untouched by this procedure, so no entry has to be re-added or removed.
- Rollback is only safe together with the fix procedures: reverting 01 alone leaves procedures 03-09 as harmless prose/alias cleanups, so partial rollback needs no special order.

## Validation plan
- Targeted: `uv run pytest tests/tools/test_check_compat_shims.py -q` — all tests except the repo-clean gate must stay green; `TestProductionCategoryZero::test_real_repo_manifest_passes` goes green only after procedures 03-09 and `wfaudit008` land (record that state in the Execution Status notes if this procedure lands first).
- Census gate: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` — compare the findings list against the 12-finding expectation above; after the fix procedures land it must print "All checks passed" with exit 0.
- `uv run python tools/check_tool_descriptions_sync.py` after the `tools/TOOL_DESCRIPTIONS.md` edit.
- Token-form spot check: `re.search(r"\b_MCP_TOOLS\b", ...)` still matches `_MCP_TOOLS = [`, `hasattr(m, "_MCP_TOOLS")` and `assert not hasattr(mod, "_MCP_TOOLS")` (verified 2026-11-08); tests in procedure 02 pin it.
- `uv run ruff check tools/check_compat_shims.py`, `uv run ty check tools/check_compat_shims.py`, then `uv run pytest tests/ -q` per `rules/toolchain.md`.

## Completion criteria
- `check_compat_patterns` matches every `COMPAT_PATTERNS` entry case-insensitively; `_MCP_TOOLS` is boundary-anchored; the inventory is still 84 entries; the companion rows state the new semantics; no other stage or file changed.

## Out of Scope
- The ADR prohibited-pattern stage (L648-654) and the removed-names stage semantics.
- New patterns, new exemption entries, and any docs-path exemption mechanism (`REQ-003`).
- Fixing the 12 census findings themselves (procedures 03-09, and `wfaudit008` for the adapter block).
- CI workflow and pre-commit hook edits (`REQ-004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | two edits: L79 anchor, L631 `re.IGNORECASE` |
| 2 | Add or update tests per Validation plan | Pending | — | — | tests are procedure 02's target file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | repo-clean gate depends on procedures 03-09 and `wfaudit008` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `tools/TOOL_DESCRIPTIONS.md` rows 83 and 174 in this procedure |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-005`
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-190836
- **Related target files**: `tools/check_compat_shims.py`; companion `tools/TOOL_DESCRIPTIONS.md`; consumers `tests/tools/test_check_compat_shims.py` (procedure 02), `scripts/agent/audit_event_emitter.py` (procedure 03), `scripts/agent/bg_task_monitor.py` (procedure 04), `scripts/agent/conversation_state_manager.py` (procedure 05), `scripts/agent/llm_turn_executor.py` (procedure 06), `scripts/mcp_servers/cicd/cicd_service.py` (procedure 07), `scripts/mcp_servers/github/github_models.py` (procedure 08), `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` (procedure 09)
