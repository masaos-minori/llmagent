# Implementation Procedure: Update MCP Known Issues Stale Status

## Goal

Re-verify MCP-003, MCP-004, and MCP-005 entries in `docs/04_mcp_90_inconsistencies_and_known_issues.md` against current source and tests, and update Status, Resolution Notes, and Severity fields to match the verified current state.

## Scope

- Update MCP-003 entry: Status → `resolved`, Resolution Notes cite GIT-001/GIT-002 resolution and verifying tests
- Update MCP-004 entry: remove stale "(1) config floor check" item from Resolution Notes since `_check_approval_risk_floor()` already implements it; confirm items (2) and (3) are resolved per Phase 1 findings
- Update MCP-005 entry: Status → `resolved`, Resolution Notes cite `test_audit_record_includes_repo_identity` and the corrected `repo_path` usage
- Run `uv run python tools/check_docs_quality.py docs/04_mcp_90_inconsistencies_and_known_issues.md` to confirm no new issues

## Assumptions

- The default convention for MCP-003 (a "parent" issue) is to flip it to `resolved` once its narrowed sub-issues (GIT-001/GIT-002) are both resolved
- MCP-004 items (2) and (3) require independent verification before being marked resolved — they were not confirmed during the ADR-012 evaluation
- The Known Issues document format allows updating individual entries without restructuring the entire document
- MCP-004 item (2): end-to-end test exercising shipped config/agent.toml through approval-risk pipeline exists and passes
- MCP-004 item (3): git-specific approval-screen preview in `build_preview()` exists and does not fall through to generic JSON-dump

## Design decisions

- MCP-003: Mark as `resolved` rather than leaving as a historical umbrella entry — its full described scope (protected-branch/Force-Push guard, option-injection rejection) is implemented and tested
- MCP-004: Remove the stale "(1) config floor check" item from Resolution Notes — `_check_approval_risk_floor()` explicitly checks `git_checkout`/`git_pull`/`git_push` against a HIGH-risk floor
- MCP-005: Change Status from `fixed` to `resolved` — the bug was identified and fixed, and a dedicated test verifies the fix

## Alternatives considered

- MCP-003: Leave as a historical umbrella entry vs. flipping to `resolved` — chose `resolved` with note pointing to GIT-001/GIT-002 unless told otherwise
- MCP-005: Keep Status as `fixed` vs. `resolved` — chose `resolved` since the root cause was identified and the fix is verified by test

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

1. **Phase 1: Preparation / Verification**
   - Re-run `uv run pytest tests/mcp_servers/git/ -q` to confirm all tests pass
   - Independently verify MCP-004 items (2) and (3) against current code/tests:
     - Item (2): Check `tests/agent/test_tool_policy_comprehensive.py::test_real_config_resolves_git_tools_to_high_risk` exists and passes
     - Item (3): Check `scripts/agent/tool_result_formatter.py::build_preview` has git-specific handling (`tool_name.startswith("git_")`) and does not fall through to `_json_dumps`

2. **Phase 2: Core Logic Implementation**
   - Update MCP-003 entry: Status → `resolved`, Resolution Notes cite GIT-001/GIT-002 resolution and verifying tests
   - Update MCP-004 entry: remove stale "(1) config floor check" item from Resolution Notes; confirm items (2)/(3) are resolved based on Phase 1 findings
   - Update MCP-005 entry: Status → `resolved`, Resolution Notes cite `test_audit_record_includes_repo_identity` and `repo_path` usage

3. **Phase 3: Deployment & Verification**
   - Run `uv run python tools/check_docs_quality.py docs/04_mcp_90_inconsistencies_and_known_issues.md` to confirm no new issues

### Method

Direct edit of the Known Issues document entries. Each entry is self-contained with its own section header, so edits do not affect other entries.

### Details

#### MCP-003 update

Current line numbers (to be re-confirmed before editing):
- Line 74: `- **Status**: open` → `- **Status**: resolved`
- Line 88: Resolution Notes currently say "Narrowed from original scope: protected-branch enforcement and `branch`/`remote` option-injection rejection are implemented (see REQ-006). The remaining Dirty-Worktree/Detached-HEAD gap is tracked as `GIT-001` and the postcondition-verification gap as `GIT-002`."
- Updated Resolution Notes: "Resolved. Protected-branch enforcement and `branch`/`remote` option-injection rejection are implemented (REQ-006). Remaining Dirty-Worktree/Detached-HEAD gap tracked as `GIT-001` and postcondition-verification gap as `GIT-002` — both separately resolved. Verified by `tests/mcp_servers/git/test_git_security_compliance.py::test_check_protected_branch` and `tests/mcp_servers/git/test_git_security_compliance.py::test_is_safe_ref`."

#### MCP-004 update

Current line numbers (to be re-confirmed before editing):
- Line 96: `- **Status**: resolved` (unchanged)
- Line 110: Resolution Notes currently list "(1) config floor check preventing effective risk below HIGH for git tools via ProductionConfigValidator" as a remaining open item
- Updated Resolution Notes: "Core mismatch resolved. Policy owner decided to raise these three tools to the full-word-`yes` tier. `config/agent.toml::approval_risk_rules` now sets `git_checkout`/`git_pull`/`git_push = "high"`, matching the `04_mcp_05_03` table's documented intent (Verified by test, `tests/agent/test_tool_policy_comprehensive.py`). Remaining open items: (2) end-to-end test exercising the shipped config/agent.toml through the actual approval-risk pipeline, (3) git-specific approval-screen preview in build_preview() instead of generic JSON-dump fallback. Both items (2) and (3) are now implemented: item (2) verified by `tests/agent/test_tool_policy_comprehensive.py::test_real_config_resolves_git_tools_to_high_risk`; item (3) verified by `scripts/agent/tool_result_formatter.py::build_preview` having `git_` prefix branch at lines 79-88."

#### MCP-005 update

Current line numbers (to be re-confirmed before editing):
- Line 118: `- **Status**: fixed` → `- **Status**: resolved`
- Line 132: Resolution Notes currently say "Root cause was key mismatch (`"repo"` vs `"repo_path"`). Row 1 fixes the key name and consumes resolved canonical path from Row 2's `(ok, err, resolved)` return value. Audit records will now contain canonical repository identity."
- Updated Resolution Notes: "Resolved. Root cause was key mismatch (`"repo"` vs `"repo_path"`). Fix applied: audit call site uses `req.args.get("repo_path", "")` and passes `target=resolved` to `_audit_log()` (verified by code inspection of `scripts/mcp_servers/git/git_server.py::call_tool`). Verified by `tests/mcp_servers/git/test_repository_state.py::TestAuditLogVerification::test_audit_record_includes_repo_identity`."

## Compatibility considerations

- This change only updates status fields and Resolution Notes text within existing entries — no structural changes to the document
- Downstream documents that reference MCP-003/MCP-004/MCP-005 (e.g., ADR-012) may need their Known Deviations sections updated if they cite stale status values — this should be handled in a separate follow-up if needed
- The Known Issues document is a living document; future entries should use consistent terminology for resolved states

## Security considerations

- No security impact — this is a documentation-only change
- The MCP Known Issues document itself references security-related issues but updating its status fields does not alter any security behavior

## Rollback considerations

- Simple revert: restore previous Status values and Resolution Notes text from git history
- No data loss or behavioral change — purely textual

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| MCP-003 entry | Manual review of Status/Resolution Notes | Diff against original | Status=resolved, notes cite GIT-001/GIT-002 |
| MCP-004 entry | Manual review of Status/Resolution Notes | Diff against original | Status=resolved, stale "(1)" item removed |
| MCP-005 entry | Manual review of Status/Resolution Notes | Diff against original | Status=resolved, notes cite `test_audit_record_includes_repo_identity` |
| All entries | Docs quality check | `uv run python tools/check_docs_quality.py docs/04_mcp_90_inconsistencies_and_known_issues.md` | No new issues reported |

## Completion criteria

- MCP-003 Status field changed from `open` to `resolved` with accurate Resolution Notes citing resolving evidence
- MCP-004 Resolution Notes no longer list "(1) config floor check" as a remaining open item; items (2) and (3) confirmed resolved or left as-is if still valid
- MCP-005 Status field changed from `fixed` to `resolved` with accurate Resolution Notes citing `test_audit_record_includes_repo_identity`
- `uv run python tools/check_docs_quality.py docs/04_mcp_90_inconsistencies_and_known_issues.md` reports no new issues

## Out of scope

- Any other MCP-xxx or GIT-xxx entry in the Known Issues document
- `CI-002`'s separate stale-reference problem (production/local recovery distinction citing a now-merged ADR-011)
- Modifying `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` (already updated on 2026-08-31)
- Adding new entries to the Known Issues document
- Restructuring the Known Issues document format

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-03T09:xx:xx | 2026-09-03T09:xx:xx | Updated MCP-003/MCP-004/MCP-005 entries |
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903-000000 | 20260903-000000 | |
| 2 | Add or update tests per Validation plan | Completed | 20260903-000000 | 20260903-000000 | N/A: doc-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903-000000 | 20260903-000000 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903-000000 | 20260903-000000 | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Verification Results

### Adversarial Verification (Step 3)

#### MCP-003 Claim Verification
- **Claim**: Status → `resolved`, Resolution Notes cite GIT-001/GIT-002 resolution and verifying tests
- **Verification**:
  - MCP-003 Status was `open` — confirmed stale (GIT-001 and GIT-002 sub-issues both resolved)
  - MCP-003 Current Description still references unresolved gaps — now superseded by resolved sub-issues
  - Verified by: `tests/mcp_servers/git/test_git_security_compliance.py::test_check_protected_branch`, `tests/mcp_servers/git/test_git_security_compliance.py::test_is_safe_ref`
- **Result**: PASS — claim valid, edit applied

#### MCP-004 Claim Verification
- **Claim**: Remove stale "(1) config floor check" item from Resolution Notes; confirm items (2) and (3) resolved
- **Verification**:
  - MCP-004 Status was `resolved` — but Resolution Notes still listed stale item (1)
  - Item (1): `_check_approval_risk_floor()` exists at `scripts/shared/production_config_validator.py:71` — already implements config floor check
  - Item (2): `tests/agent/test_tool_policy_comprehensive.py::test_real_config_resolves_git_tools_to_high_risk` exists — verified
  - Item (3): `scripts/agent/tool_result_formatter.py::build_preview` has git_ prefix branch at lines 79-88 — verified
- **Result**: PASS — claim valid, edits applied

#### MCP-005 Claim Verification
- **Claim**: Status → `resolved`, Resolution Notes cite `test_audit_record_includes_repo_identity` and corrected `repo_path` usage
- **Verification**:
  - MCP-005 Status was `fixed` — not yet fully resolved
  - Fix verified: `req.args.get("repo_path", "")` used at `scripts/mcp_servers/git/git_server.py::call_tool`
  - Test verified: `tests/mcp_servers/git/test_repository_state.py::TestAuditLogVerification::test_audit_record_includes_repo_identity`
- **Result**: PASS — claim valid, edit applied

### Post-Validation (Step 4)
- `tools/check_docs_quality.py docs/04_mcp_90_inconsistencies_and_known_issues.md`: PASSED (0 errors, 1 pre-existing warning about Migration Notes)

### All MCP Entries Verified Against Source
| Entry | Original Status | New Status | Verification Method |
|-------|----------------|------------|-------------------|
| MCP-003 | open | resolved | test + code inspection |
| MCP-004 | resolved | resolved | test + code inspection |
| MCP-005 | fixed | resolved | test + code inspection |
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/20260831-185650_adr012_02_mcp_known_issues_stale_status.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-223706_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-02T21:36:55Z
- **Related target files**: `docs/04_mcp_90_inconsistencies_and_known_issues.md`
