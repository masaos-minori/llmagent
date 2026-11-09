## Goal
Make the compatibility-leftover checker case-insensitive where the repository's own source uses capitalized forms, so phrases like the adapter's "Backward-compatible alias" block are caught by CI instead of silently passing — without flooding the docs scan with legitimate history prose.

## Priority
Medium

## Scope
- **In-Scope**:
  - `tools/check_compat_shims.py` — apply `re.IGNORECASE` to the `COMPAT_PATTERNS` search in `check_compat_patterns` (loop L628-634; the search is at L631), and add `\b` anchors to the `_MCP_TOOLS` pattern (L79); verify the whole repository passes after the change.
  - Follow-through findings: newly flagged active-source lines are fixed directly (no-compatibility policy; the COMPAT scan has no historical-context exemption to extend). The `workflow_engine_adapter.py` alias block is expected to be flagged and `wfaudit008`'s procedures delete it (landing order below); the remaining census findings are fixed in rows 3-9.
  - Tests: `tests/tools/` checker tests with capitalized-vs-lowercase fixture pairs.
- **Out-of-Scope**:
  - Adding new patterns (the pattern vocabulary is unchanged; only matching semantics plus the `_MCP_TOOLS` boundary anchors allowed by `REQ-003`).
  - The `_REMOVED_NAME_PATTERNS` path — its historical-context exemption case-folds each line (frozenset L345-363; `_is_historical_context()` L486-496, fold at L494, applied in `check_removed_name_reintroduction()` at L571/L599); the pattern dict itself stays case-sensitive; unchanged.
  - Docs history prose: the 2026-11-08 census (Notes) proves no active docs line matches any COMPAT pattern except one constraint sentence (`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` L50, row 9) — no exemption mechanism is added and no mass doc rewording occurs.
- **Dependencies**: After `wfaudit008` (its alias block, the main live source of capitalized leftovers, is deleted there; making the checker strict afterwards protects a clean tree). If 012 lands first, its Phase 2 must fix the adapter lines that 008 will delete — 008-first avoids editing code twice.

## Background
Live verification at HEAD (issue `## Adversarial Validation`): `COMPAT_PATTERNS` matches run through `re.search(pattern, stripped)` with no flags (`tools/check_compat_shims.py` `check_compat_patterns` loop L628-634, search at L631); the pattern `"backward-compatible keyword": r"backward-compatible"` (L95) does not match the capitalized "Backward-compatible public API" header (`scripts/agent/workflow_engine_adapter.py:106`) or the four "Backward-compatible alias for ..." docstrings (L121,128,135,144) — `re.search(r"backward-compatible", "Backward-compatible ...")` is False. A live run of `tools/check_compat_shims.py` (plain and with `--check-removed-names`) on both target files prints "All checks passed". CI wiring: `.github/workflows/backward-compat-check.yml:39` runs the checker with `--check-removed-names --check-doc-symbols` (the `check-compat-shims` pre-commit hook passes the same flags), and the checker file itself is a watched trigger path. The removed-names scan compensates for its case-sensitive `_REMOVED_NAME_PATTERNS` (L383-467) with explicit case-variant entries (`workflow_schema_version` L447, `WORKFLOW_SCHEMA_VERSION` L451) plus the case-folded historical-context exemption (L494); `LEGACY_MARKER_TABLES` is flagged by neither scan — no COMPAT pattern names `LEGACY_` identifiers, and the checker comment at L128-133 records the deliberate placement (2026-11-08 correction; see Notes). `_REMOVED_NAME_PATTERNS` does not use `re.IGNORECASE` — the checker's only `re.IGNORECASE` today is the `_NEGATED_SERVER_CONFIGS_RE` helper (L481).

## Problem
The no-compatibility policy is enforced by a scanner that misses exactly the capitalized forms the codebase actually writes — the check passes not because the code is clean but because the pattern is case-blind in the wrong direction.

## Reason for Change
The removed-names scan already demonstrates the intended tolerance boundary (case-folded historical-context exemption, with case-variant spellings handled by explicit pattern entries); COMPAT_PATTERNS diverging from it — case-sensitive patterns and no exemption at all — is an implementation gap, not a policy.

## Implementation Intent
One mechanism change in one loop: add `re.IGNORECASE` to the `check_compat_patterns` search so every COMPAT pattern matches case-insensitively (case-folding the matched line alone would break the uppercase-literal patterns — `_MCP_TOOLS` L79, "Workflow mode=disabled" L109 — see Notes 2026-11-08). Then run the full checker over the repository; newly flagged active-source lines are fixed per the policy (delete or collapse leftovers, reword inaccurate prose). The 2026-11-08 census already proved no docs-path exemption is needed, so none is added (repo rule: no speculative code).

## Requirements
- `REQ-001`: Every `COMPAT_PATTERNS` entry matches case-insensitively (fixture test: "Backward-compatible alias" and "backward compatibility Layer" both flagged in a code fixture).
- `REQ-002`: The full-repository run (`--check-removed-names --check-doc-symbols`, as CI invokes it) exits clean — the newly-flagged lines are fixed in this plan (rows 3-9) or by `wfaudit008` (adapter block); no exemption mechanism is added (the 2026-11-08 census proves docs prose needs none).
- `REQ-003`: No pattern added or removed (inventory: 84 keys/84 entries pinned by a count/list test so future edits are deliberate); the sole inventory-preserving pattern edit is adding `\b` anchors to the `_MCP_TOOLS` entry (L79), proven necessary by the census (7 identifier false positives on `_cmd_mcp_tools`-style names and test names; see Notes).
- `REQ-004`: CI workflow wiring (`backward-compat-check.yml`) passes unchanged (no workflow edits required).
- `REQ-005`: New checker tests pin case-insensitivity, the `_MCP_TOOLS` token-boundary behavior, and the pattern inventory (no exemption-path tests: the census proves no exemption path is added).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tools/check_compat_shims.py` | Modify | `re.IGNORECASE` on the COMPAT search (loop L628-634, search L631); `\b` anchors on the `_MCP_TOOLS` pattern (L79); registry row update in `tools/TOOL_DESCRIPTIONS.md` | `REQ-001`/`REQ-002`/`REQ-003`/`REQ-005` | Case gap verified by live repro (Step 2); 2026-11-08 case-insensitive census in Notes | `tests/tools/test_check_compat_shims.py` | `Verified` |
| `tests/tools/test_check_compat_shims.py` | Modify | Capitalized/lowercase/UPPERCASE fixture pairs; `_MCP_TOOLS` boundary fixtures; 84-entry pattern-inventory pin | `REQ-001`/`REQ-003`/`REQ-005` | Existing checker test file (verified 2026-11-08) | self | `Verified` |
| `scripts/agent/audit_event_emitter.py` | Modify | Delete the unused `_format_session_id` alias and its comment (L31-32) | `REQ-002` | Census finding L31 (`backward-compatible keyword`); no callers repo-wide (grep census) | grep gate + checker run | `Verified` |
| `scripts/agent/bg_task_monitor.py` | Modify | Collapse the `notify_bg_failure_threshold` wrapper pair (delete wrapper L147-152; rename `_notify_threshold_breach` L154 to the public name; update internal caller L138) | `REQ-002` | Census finding L150; docs name the public method (`agent_03_01` L90-91), so the public surface is kept | `tests/agent/` suite | `Verified` |
| `scripts/agent/conversation_state_manager.py` | Modify | Delete the unused `EPHEMERAL_KEYS` alias and its comment (L32-33) | `REQ-002` | Census finding L32; no callers repo-wide (grep census) | grep gate + checker run | `Verified` |
| `scripts/agent/llm_turn_executor.py` | Modify | Reword the L54 section header — the `call_on_llm_wait_*` helpers are live internal call sites (L98, L110), not aliases | `REQ-002` | Census finding L54 | grep gate + checker run | `Verified` |
| `scripts/mcp_servers/cicd/cicd_service.py` | Modify | Reword the L4 module docstring — the module is the current aggregation module imported by `cicd_server.py:38`, not a compatibility stub | `REQ-002` | Census finding L4 (`re-export stub phrase`) | checker run | `Verified` |
| `scripts/mcp_servers/github/github_models.py` | Modify | Reword the L4 module docstring — current aggregation module imported by nine live `scripts/mcp_servers/github/` modules | `REQ-002` | Census finding L4 (`re-export stub phrase`) | checker run | `Verified` |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Reword the L50 constraint sentence so it states the policy without the flagged phrase order | `REQ-002` | Census finding L50 (`direct-execution fallback phrase`) | docs checkers | `Verified` |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `tools/check_compat_shims.py` (`_HISTORICAL_CONTEXT_MARKERS` frozenset L345-363; `_is_historical_context()` L486-496 with the case fold at L494, applied in `check_removed_name_reintroduction()` at L571/L599) | Confirms the removed-names path stays untouched and how its case-variant handling differs from the COMPAT fix | `REQ-002` |
| `.github/workflows/backward-compat-check.yml` | Exact CI invocation to reproduce locally | `REQ-004` |
| `scripts/agent/workflow_engine_adapter.py` (alias block L106-146) | The known capitalized leftover — deleted by `wfaudit008`; confirms landing order | Dependencies |

## Acceptance Criteria
- `REQ-001`: Fixture test shows capitalized and lowercase forms both produce findings.
- `REQ-002`: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` (the CI command) exits 0 over the whole repository after fixes.
- `REQ-003`: Pattern-dict size/keys unchanged (84 entries pinned by test); only the `_MCP_TOOLS` regex gains `\b` anchors.
- `REQ-004`: CI workflow file byte-identical; local reproduction of its command green.
- `REQ-005`: Full `tests/tools/` green; new tests fail on HEAD (capitalized fixture passes the old checker).

## Tests
- Parametrized case fixtures (code content scan): lowercase, Capitalized, UPPERCASE forms of "backward compatibility layer", "backward-compatible", "compatibility layer".
- Repo-clean regression: a test running the checker over the repository (already CI's behavior) — kept green by fixing findings, not by loosening patterns.
- `_MCP_TOOLS` boundary fixtures: identifier substrings (`_cmd_mcp_tools`, `test_mcp_tools_validation`) are not flagged; token-form `_MCP_TOOLS` references are still flagged.
- Pattern-inventory pin: 84 keys/84 entries so future pattern edits are deliberate (`REQ-003`).
- No exemption-path test: the 2026-11-08 census proved no docs-path exemption mechanism is added (`REQ-005`).

## Documentation Impact
- `tools/TOOL_DESCRIPTIONS.md` has no case-semantics sentence for `check_compat_shims.py` today (verified 2026-11-08); procedure 01 adds the case-insensitivity/`_MCP_TOOLS`-boundary sentence to the checker's registry rows.
- Run `tools/` docs/tooling registration checks per `routing.md` Tools (AGENTS.md rule 9 applies because `tools/` is edited).

## Assumptions
- After `wfaudit008` lands, the adapter alias block (the largest known capitalized leftover) is gone; the 2026-11-08 census (Notes) records the remaining findings: 7, each covered by rows 3-9 — no speculation.
- Docs contain capitalized "Backward" prose (glossary/heading usages), but the census proved none matches any COMPAT pattern; the only docs match is the single constraint sentence at `agent_10_01` L50, so no exemption mechanism is needed for the COMPAT scan (the mechanism today would not exempt that line either — it carries no historical marker).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | exact count/location of newly flagged lines under case-insensitive matching (docs vs active source) | — resolved 2026-11-08 | Resolved by the ground-truth census in Notes: 19 findings, 7 suppressed by the `_MCP_TOOLS` anchors, 5 owned by `wfaudit008`, 7 resolved by rows 3-9; no new allowlist entries needed | `False` |
| `UNK-02` | whether adding an exemption to COMPAT_PATTERNS risks hiding future active-source leftovers | — resolved 2026-11-08 | Resolved: census shows no docs finding an exemption could legitimately exempt; no exemption is added | `False` |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tools/check_compat_shims.py` | Modify | CI gate behavior for every future commit | 13 | N/A | not applicable (not deployed; CI tool) |
| `tests/tools/` | Modify | tests only | N/A | N/A | not applicable |

## Design
**Match semantics, one loop.** Add `re.IGNORECASE` to the single `re.search` call in `check_compat_patterns` (L631): one edit covers all 84 patterns and leaves the reported line text intact; case-folding only the matched line was rejected because patterns containing uppercase literals (`_MCP_TOOLS` L79, "Workflow mode=disabled" L109) would then never match. The removed-names scan keeps its own already-working mechanism (case-variant entries + historical-context exemption).

**Strict-first, evidence-gated.** The 2026-11-08 census ran the strict semantics against the real checker before any permanent code change and listed the findings: 19 case-variant findings. 7 come from the unanchored `_MCP_TOOLS` pattern matching `_cmd_mcp_tools`-style names and test names and are resolved by adding `\b` anchors to that pattern (active-source review found nothing to change); 5 are the adapter block owned by `wfaudit008`; the remaining 7 are fixed by rows 3-9 (delete two unused aliases, collapse one wrapper pair, reword three comments/docstrings and one docs sentence). No docs-path exemption is warranted or added (repo rule: no speculative code).

**Landing order.** After `wfaudit008`: the biggest capitalized block disappears first, minimizing dual edits.

## Implementation steps
1. **Phase 1: Semantics flip + repo census (`REQ-001`).** Implement case-insensitive matching + the `_MCP_TOOLS` anchor fix; run the full CI command; reconcile the findings list against the 2026-11-08 census (`UNK-01`).
2. **Phase 2: Finding resolution (`REQ-002`).** Fix the flagged lines per rows 3-9 (census-pinned; `UNK-02` resolved: no exemption added); repo run exits 0.
3. **Phase 3: Tests + tool docs (`REQ-003`-`REQ-005`).** Checker tests (case fixtures, `_MCP_TOOLS` boundary, inventory pin); `TOOL_DESCRIPTIONS.md` case-semantics sentence.

### Release units
**Unit**: wfaudit012-full | **Phases**: 1, 2, 3 | **Reason**: a strictened CI gate must ship green — flipping semantics without resolving its findings would break every future CI run.

## Validation plan
- After Phase 1: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` full run; findings list recorded in the Execution Status notes.
- After Phase 2: same command exits 0; `uv run pytest tests/tools/ -q` green.
- Full `uv run pytest tests/ -q` before completion; lint/type gates per `rules/toolchain.md`.
- CI parity: local command identical to `.github/workflows/backward-compat-check.yml:39`.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Strict run floods findings (docs prose) | Ruled out by the 2026-11-08 census (1 docs finding) | Low | Census-pinned fixes in rows 3-9; no exemption mechanism added |
| Case-insensitive matching makes an identifier-shaped pattern match legitimate identifiers in code | Occurred in census: 7 false positives from the `_MCP_TOOLS` pattern | Low | Resolved by the `\b` anchors on that entry (row 1) and boundary fixtures (row 2); findings reviewed per line |
| Landing before `wfaudit008` forces edits to the adapter alias block that 008 deletes anyway | Medium | Low | Preferred order: 008 first; if unavoidable, exempt-by-deletion-timing note in the procedure doc |

## Execution Status
### Execution Status
| Step | Description | Status | Owner | Started | Completed | Notes |
|---|---|---|---|---|---|---|
| 1 | Phase 1: semantics flip + census | Completed | engineer | 2026-11-08 | 2026-11-09 | procedures 01-09 implemented, validated, archived batch 20261108-190836 |
| 2 | Phase 2: finding resolution | Completed | engineer | 2026-11-08 | 2026-11-09 | repo-clean census 0; all findings resolved |
| 3 | Phase 3: tests + tool docs | Completed | engineer | 2026-11-08 | 2026-11-09 | ruff/mypy/bandit/module-size clean; diff-cover 100% on changed lines |

### Blocker Log
| Date | Blocker | Status | Resolution |
|---|---|---|---|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261108-190836_01_tools_check_compat_shims.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261108-190836_02_tests_tools_test_check_compat_shims.py.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261108-190836_03_scripts_agent_audit_event_emitter.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-190836_04_scripts_agent_bg_task_monitor.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-190836_05_scripts_agent_conversation_state_manager.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-190836_06_scripts_agent_llm_turn_executor.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-190836_07_scripts_mcp_servers_cicd_cicd_service.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-190836_08_scripts_mcp_servers_github_github_models.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261108-190836_09_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md` | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: N/A: this document is the plan
- **Generated at**: 20261108-084013
- **Related target files**: see Implementation Target Files table

### Requirement Traceability
| Requirement | Source | Target File | Acceptance Criterion | Test |
|---|---|---|---|---|
| `REQ-001` | Issue Problem + live repro | `tools/check_compat_shims.py` | case-insensitive matches | fixture tests |
| `REQ-002` | Issue constraint (CI must stay green) | whole repo run | CI command exits 0 | repo run + CI parity |
| `REQ-003` | Plan Design (no pattern changes) | checker | inventory pinned | inventory test |
| `REQ-004` | Issue Evidence (CI wiring) | workflow file | unchanged | file byte-check |
| `REQ-005` | Issue Testing Expectations | `tests/tools/` | fail on HEAD | pytest |

## Notes
- Source verified against HEAD `926dbc109`; the issue's `LEGACY_MARKER_TABLES` mechanism description was corrected during validation (it lives in `_REMOVED_NAME_PATTERNS` deliberately — see the issue's `## Adversarial Validation`).
- Sequence: after `wfaudit008`.
- 2026-11-08 procedure-pass corrections (adversarial re-verification at HEAD `ad48bfa28`):
  - Loop/function fix: the COMPAT scan is `check_compat_patterns` (not "check_content"), loop L628-634, search at L631 (was "L630-633"). The sibling `check_adr_prohibited_patterns` loop (L648-654) is out of scope and stays case-sensitive.
  - `_REMOVED_NAME_PATTERNS` is case-sensitive (L383-467; explicit case variants `workflow_schema_version` L447 and `WORKFLOW_SCHEMA_VERSION` L451). The checker's only `re.IGNORECASE` today is `_NEGATED_SERVER_CONFIGS_RE` (L481). The historical-context exemption case-folds lines (`lines[i].lower()` L494). `LEGACY_MARKER_TABLES` is flagged by neither scan; placement rationale at L128-133.
  - Mechanism fix: `re.IGNORECASE` on the search replaces "case-fold `stripped`" — line-folding alone would break the uppercase-literal patterns (`_MCP_TOOLS` L79, "Workflow mode=disabled" L109). Pattern inventory: 84 keys / 84 distinct values (was "60+").
  - Census, ground truth (2026-11-08, supersedes the earlier simulated scan): the strict semantics were run against the real checker — `re.IGNORECASE` added to the COMPAT search in `tools/check_compat_shims.py` `check_compat_patterns` (L631) in the working tree, `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` executed, then the edit reverted with `git checkout -- tools/check_compat_shims.py`; the reverted tree re-verified clean ("All checks passed"). Result: 19 findings, exit code 1 — 7 identifier false positives from the unanchored `_MCP_TOOLS` pattern (`scripts/agent/commands/cmd_mcp.py:283`/`:287` — the live `_cmd_mcp_tools` call and definition; `tests/agent/commands/test_command_def_sync.py:22` — `"_cmd_mcp_tools",` in a tuple of command names; `tests/mcp_servers/file/test_mcp_tools_validation.py:1`, `tests/mcp_servers/git/test_tools_endpoint.py:8`, `tests/mcp_servers/test_tool_schema.py:9` — docstring cross-references to `tests/test_mcp_tools_validation.py`; `tests/mcp_servers/test_mcp_server_base.py:204` — test method name `test_empty_mcp_tools_attribute_missing_returns_empty_list`), 5 adapter findings owned by `wfaudit008` procedures `implementations/20261108-162804_01_*`/`_02_*` (`scripts/agent/workflow_engine_adapter.py` L106 header comment plus the L121/128/135/144 `Backward-compatible alias for ...` docstrings), 7 findings resolved by rows 3-9 (`audit_event_emitter.py:31`, `bg_task_monitor.py:150`, `conversation_state_manager.py:32`, `llm_turn_executor.py:54`, `cicd_service.py:4`, `github_models.py:4`, `agent_10_01_...md:50`).
    - False-positive disposition: `\b` anchors on the `_MCP_TOOLS` entry (pattern string `_MCP_TOOLS` → `\b_MCP_TOOLS\b`, L79) suppress all 7 lines and keep token-form matches (`_MCP_TOOLS = [`, `hasattr(m, "_MCP_TOOLS")`, `assert not hasattr(mod, "_MCP_TOOLS")`) — verified with `re.compile(r"\b_MCP_TOOLS\b")` against each line on 2026-11-08. No file is allowlisted or edited for those 7 lines: they name live identifiers (`_cmd_mcp_tools` is the current MCP-list command method in `scripts/agent/commands/cmd_mcp.py`) or test names, not retired mechanisms.
  - Pattern storage: `COMPAT_PATTERNS` maps name → raw pattern string (not a compiled object), so the anchor edit is a string edit at L79. 49 of the 84 entries already carry no `\b` anchor and several carry `\b` (for example `\ballow_startup_fallback\b` L103), so adding boundaries to one entry follows existing style rather than introducing a new convention.
  - Row 3 decomposition: the evidence-driven "Newly flagged active-source files" row was replaced by the 7 census-pinned file rows (3-9). `llm_turn_executor.py`'s `call_on_llm_wait_*` helpers are live internal call sites (used at L98/L110), not dead aliases — header reword, not deletion. `bg_task_monitor.py` keeps the public name documented in `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` L90-91 via wrapper collapse (mirrors `wfaudit008`'s `deactivate_workflow` collapse). `cicd_service.py`/`github_models.py` are live aggregation modules (imported by `cicd_server.py:38` and nine github modules) — docstring reword, not deletion.
  - `REQ-003` reworded: pattern text change is permitted only as the `_MCP_TOOLS` boundary anchors (inventory unchanged); the original "No pattern text changes" wording conflicted with the census evidence.
- Overlap check: `uv run python tools/check_plan_target_overlaps.py` reports no overlap with landed or pending plans (run 2026-11-08 after the row decomposition; the 7 census files appear in no other pending plan's target rows).

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-190836 -->
