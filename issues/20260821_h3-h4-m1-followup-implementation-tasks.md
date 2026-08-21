# Follow-up Implementation Tasks: DB Recovery, Git Write Protection, MCP Tool Availability

Generated from the documentation update addressing H-3 (database corruption recovery), H-4 (Git MCP write protection), and M-1 (MCP tool availability metadata). No source code was changed while producing this list; each task below is independently actionable. See `docs/99_documentation_sync_report.md` for the full change report and `docs/adr/ADR-011-*.md`/`ADR-012-*.md`/`ADR-013-*.md` for the design decisions these tasks implement.

---

## High priority

### H-1: Catch and classify `sqlite3.DatabaseError` in `_run_integrity_check()`

- **Reason**: physical page corruption currently raises an uncaught exception instead of being classified and handled by recovery policy (Known Issue SHARED-001, ADR-011 INV-01).
- **Current behavior**: `_run_integrity_check()` catches only `sqlite3.OperationalError`, `ValueError`, `RuntimeError`; `sqlite3.DatabaseError` propagates out of `recover_corruption()`'s public boundary.
- **Target behavior**: `sqlite3.DatabaseError` is caught, classified as confirmed/likely corruption, and handled through the normal recovery decision path instead of raising.
- **Affected symbols**: `db/recovery.py::_run_integrity_check()`, `recover_corruption()`.
- **Required tests**: regression test reproducing a physically corrupted SQLite file and asserting `recover_corruption()` returns a structured result instead of raising.
- **Acceptance criteria**: no test or manual reproduction of physical corruption results in an uncaught `sqlite3.DatabaseError` from `recover_corruption()`.

### H-2: Validate backup integrity and make restoration atomic

- **Reason**: an unvalidated or partially-written backup can be restored over the target database, and a mid-copy failure can leave the target partially written (Known Issue SHARED-002, ADR-011 INV-02/INV-03).
- **Current behavior**: `_restore_from_backup()` checks only `Path.exists()` on the backup, then `shutil.copy2()`s it directly onto the live target path with no temporary-file staging or post-restore re-verification.
- **Target behavior**: the backup is integrity-checked independently before use; restoration copies to a temporary file, verifies it, then atomically replaces the target; the restored database is reopened and re-verified before `success=True` is returned.
- **Affected symbols**: `db/recovery.py::_restore_from_backup()`.
- **Required tests**: test that a corrupted backup is rejected rather than restored; test that a simulated mid-copy failure leaves the original target file intact; test that restoration is followed by a passing integrity check before success is reported.
- **Acceptance criteria**: ADR-011 INV-02/INV-03 hold under test; no restoration path writes directly to the live target path without a preceding validated temporary copy.

### H-3: Define and implement a recovery policy for `workflow.sqlite` and `eventbus.sqlite`

- **Reason**: these two persistence domains have no corruption-recovery path at all today; an operator facing corruption in either has no documented or implemented procedure (Known Issue SHARED-003, ADR-011 Decision Details #6).
- **Current behavior**: `recover_corruption()` only supports `target='rag'`/`'session'`; `rotate_all_dbs()` excludes `workflow`/`eventbus`; the only observed startup behavior for a broken store in this class is a fatal `RuntimeError`.
- **Target behavior**: either (a) an explicit, implemented recovery path for these domains, or (b) an explicit, documented decision that they are unrecoverable by design, with a stated manual operator procedure — not silent absence.
- **Affected symbols**: `db/recovery.py::recover_corruption()`, `db/rotation.py::rotate_all_dbs()`, `agent/startup.py::_recover_pending_approvals()`.
- **Required tests**: once a policy is chosen, a test exercising that policy's success and failure paths for both `workflow.sqlite` and `eventbus.sqlite`.
- **Acceptance criteria**: `recover_corruption()` rejects unsupported `target` values explicitly instead of silently mislabeling the display path; the chosen policy for `workflow`/`eventbus` is implemented and documented in `90_shared_05_04_db_api_and_operations-recovery-and-reference.md` §9.7.

### H-4: Validate `branch`/`remote` in Git MCP write tools; reject option-injection-shaped values

- **Reason**: `branch`/`remote` are forwarded to GitPython unvalidated; a value such as `"--force"` is interpreted as a `git` CLI option, confirmed in a sandboxed reproduction to cause an unwarned forced checkout (discarding uncommitted changes) and a forced push (overwriting a diverged remote branch) — Known Issue MCP-003, ADR-012 INV-01.
- **Current behavior**: `format_checkout()`/`format_pull()`/`format_push()` pass `branch`/`remote` straight to `repo.git.*()` with no pattern or prefix validation; `tool_validators.py` only checks non-emptiness for `git_push`'s `remote` and nothing for `git_checkout`.
- **Target behavior**: `branch`/`remote` values are validated against a safe ref/remote-name pattern; values that would be interpreted as CLI options (e.g., leading `-`) are rejected before reaching GitPython.
- **Affected symbols**: `scripts/mcp_servers/git/format_output.py::format_checkout()`, `format_pull()`, `format_push()`; `scripts/mcp_servers/git/tool_validators.py`.
- **Required tests**: regression tests asserting `git_checkout`/`git_pull`/`git_push` reject `branch`/`remote` values shaped like CLI options, in addition to the existing sandboxed reproduction being converted into a permanent regression test.
- **Acceptance criteria**: the previously-reproduced forced-checkout/forced-push-via-injection scenario no longer succeeds; existing legitimate ref names continue to work.

### H-5: Add a protected-branch guard and a technical Force-Push block to Git MCP

- **Reason**: Git MCP has no protected-branch policy and no guard preventing a forced update through the normal `git_push` path, unlike what project documentation previously (incorrectly) claimed — Known Issue MCP-003, ADR-012 Decision Details #3/#4, INV-02/INV-03.
- **Current behavior**: `git_checkout`/`git_push` treat all branches identically; no configuration key equivalent to GitHub MCP's `protected_branches` exists for Git MCP.
- **Target behavior**: a configured protected-branch list rejects direct `git_checkout`/`git_push` against protected branches unless a separately approved policy allows it; Force Push is rejected by the normal `git_push` path (any future Force-Push capability is a separate, more strongly authorized tool, not a mode of this one).
- **Affected symbols**: `scripts/mcp_servers/git/git_service.py`, `git_security.py`, `git_models.py::GitConfig`.
- **Required tests**: test that push/checkout against a configured protected branch is rejected; test that a forced update cannot be achieved through the normal `git_push` path once H-4 above is also fixed.
- **Acceptance criteria**: ADR-012 INV-02/INV-03 hold under test; `04_mcp_04_05_git.md` §Protected branch authority is updated from "no policy source" to describing the implemented policy.

---

## Medium priority

### M-1: Wire `enabled`/`disabled_reason` for `rag_pipeline`, `cicd`, `mdq`, and `shell`

- **Reason**: `git`, `file_read`/`file_write`/`file_delete`, `github`, and `web_search` already compute per-tool availability metadata; `rag_pipeline`/`cicd`/`mdq`/`shell` do not, so their tools cannot be statically disabled or surfaced as disabled even when a config-derived reason would apply (Known Issue MCP-002).
- **Current behavior**: these servers route `TOOL_LIST` directly to `build_tools_response()` with no per-tool `enabled`/`disabled_reason` computation.
- **Target behavior**: each server computes `enabled`/`disabled_reason` following the pattern already used by `git`/`file_read`/`file_write`/`file_delete`/`github`/`web_search`.
- **Affected symbols**: `scripts/mcp_servers/{rag_pipeline,cicd,mdq,shell}/server.py`.
- **Required tests**: per-server test asserting a config-gated tool (e.g., empty `command_allowlist` for shell, empty `workflow_allowlist` for cicd) reports `enabled=false` with a matching `disabled_reason`.
- **Acceptance criteria**: every MCP server category reports `enabled`/`disabled_reason` consistently; Known Issue MCP-002 can be closed.

### M-2: Wire `include_disabled` and `disabled_code` through `list_tools()` handlers

- **Reason**: `build_tools_response()` already accepts both parameters, but no route handler passes them or declares a matching query parameter, so `/v1/tools` cannot filter or return a machine-readable disabled category today (Known Issue MCP-001).
- **Current behavior**: `/v1/tools` accepts no query parameters and always returns every tool.
- **Target behavior**: `GET /v1/tools?include_disabled=false` omits disabled tools; a `disabled_code` enum value accompanies `disabled_reason` per the candidate mapping in `04_mcp_03_06_tool-runtime-availability-metadata.md` §2.
- **Affected symbols**: all `scripts/mcp_servers/*/server.py::list_tools()` handlers; `mcp_servers/server.py::build_tools_response()` (no signature change expected — only call-site wiring).
- **Required tests**: test that `include_disabled=false` omits a known-disabled tool from the response; test that `disabled_code` appears alongside `disabled_reason` for each documented category.
- **Acceptance criteria**: Known Issue MCP-001 can be closed without changing `build_tools_response()`'s existing parameters.

### M-3: Resolve the Git write-tool approval-tier mismatch

- **Reason**: the risk-tier table documents `git_checkout`/`git_pull`/`git_push` as requiring full-word `yes` approval, but they currently resolve to `MEDIUM` (`y/N`) because no `approval_risk_rules` override exists for them (Known Issue MCP-004).
- **Current behavior**: `_TIER_TO_RISK["WRITE_DANGEROUS"] = RiskLevel.MEDIUM`; no override raises these three tools to `HIGH`.
- **Target behavior**: a deliberate decision — either add `"high"` overrides in `approval_risk_rules` for these three tools, or correct the documentation to describe `MEDIUM` as the intended target (not merely the current state).
- **Affected symbols**: `config/agent.toml::approval_risk_rules`; `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`.
- **Required tests**: test asserting the chosen approval level is actually presented for each of the three tools.
- **Acceptance criteria**: the risk-tier table and the actual approval prompt agree for all three tools, and this reflects an owner decision rather than an accidental gap.

### M-4: Fix (or confirm) the Git MCP audit `target` field

- **Reason**: the audit call site reads `req.args.get("repo", "")`, but Git MCP's schema key is `repo_path`; this likely makes every git-mcp audit record's `target` field empty (Known Issue MCP-005, flagged Needs Confirmation).
- **Current behavior**: unconfirmed by a live log capture; confirmed by code reading.
- **Target behavior**: audit records for Git MCP calls carry the actual repository path.
- **Affected symbols**: `scripts/mcp_servers/git/git_server.py::call_tool()`.
- **Required tests**: a test or manual capture asserting a git-mcp call's audit log line contains the repository path, not an empty string.
- **Acceptance criteria**: confirmed and fixed, or confirmed and explained if `"repo"` turns out to be populated by some mechanism not found during investigation.

### M-5: Remove or repurpose the unused `degraded_servers` and `RuntimeTool.requires_approval` fields

- **Reason**: `McpToolDiscoveryService`'s `degraded_servers` exclusion tier is never populated, and `RuntimeTool.requires_approval` is written but never read — both are dead capabilities that could mislead future readers into assuming they are active (ADR-013 context).
- **Current behavior**: both fields exist and are set/constructed but have no effect on runtime behavior.
- **Target behavior**: either wire them to real behavior (e.g., a genuine soft-degradation tier distinct from full exclusion; a real approval-required visibility signal) or remove them to avoid implying unimplemented behavior.
- **Affected symbols**: `shared/runtime_tool.py`, `runtime_tool_registry.py`, `agent/services/mcp_tool_discovery.py`.
- **Required tests**: if wired, tests for the new behavior; if removed, existing tests should be unaffected (confirming they were indeed unread/unused).
- **Acceptance criteria**: no field exists that looks load-bearing but silently does nothing.

---

## Low priority

### L-1: Clean up `LLMTurnRunner._filter_disabled_tool_definitions()`

- **Reason**: this function is a self-referential no-op (its `visible_names` set is built from the same call it filters against); it reads as an active filtering stage but is not one, which is exactly the kind of drift this documentation update was meant to catch.
- **Current behavior**: the function exists, runs, and changes nothing.
- **Target behavior**: either remove the function (Stage-1 filtering in `RuntimeToolRegistry.llm_tool_definitions()` is already sufficient) or replace it with a genuine second check if one is intentionally desired.
- **Affected symbols**: `scripts/agent/llm_turn_runner.py::_filter_disabled_tool_definitions()`.
- **Required tests**: existing tests should continue to pass after removal, confirming the function was not load-bearing.
- **Acceptance criteria**: `04_mcp_03_01_dispatch-and-routing.md`'s corrected description matches the code exactly (no-op removed, or replaced and re-documented).

### L-2: Correct ADR-001's stale forward-referenced ADR numbers

- **Reason**: ADR-001 lists "ADR-011" and "ADR-012" as future workflow-schema/monitoring ADRs; those numbers were assigned to this update's DB-recovery and Git MCP ADRs instead, per the ADR index's next-available-number rule.
- **Current behavior**: ADR-001 body still references the old, now-conflicting numbers.
- **Target behavior**: ADR-001 updated to reference the correct future numbers once the workflow-schema/monitoring ADRs are actually written (ADR-005+).
- **Affected symbols**: `docs/adr/ADR-001-workflow-engine-mandatory.md` §Related Documents.
- **Required tests**: none (documentation-only).
- **Acceptance criteria**: no ADR document references a number that belongs to a different, already-registered decision.

### L-3: Define a retention/cleanup policy for preserved damaged-database archives

- **Reason**: `_restore_from_backup()` preserves the damaged database as a timestamped archive before restoring, but no policy governs how long these archives are kept or when they are cleaned up.
- **Current behavior**: archives accumulate indefinitely with no rotation.
- **Target behavior**: an explicit retention policy (time-based or count-based) consistent with the "preserve for diagnostics" intent in ADR-011.
- **Affected symbols**: `db/recovery.py::_restore_from_backup()`, `db/rotation.py`.
- **Required tests**: test that archives older than the retention policy are cleaned up (once implemented).
- **Acceptance criteria**: archive accumulation is bounded and documented.
