## Goal

Align five Git MCP documentation files and activate the existing `protected_branches` guard in `config/git_mcp_server.toml` so that operators can trust what the docs say about git write-tool protection.

## Scope

- REQ-001: Correct `docs/00_security_02_high-risk-tool-common-policy.md`'s Git MCP bullet (~line 187)
- REQ-002: Reconcile `docs/04_mcp_04_05_git.md`'s three internally-contradictory sections
- REQ-003: Narrow `MCP-003` in `docs/04_mcp_90_inconsistencies_and_known_issues.md` to its still-open scope
- REQ-004: Remove stale caveat from `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` line ~80
- REQ-005: Split the git-write-tools row in `docs/04_mcp_01_tool_ownership_matrix.md` line 31
- REQ-006: Add `protected_branches = ["main", "master", "release"]` to `config/git_mcp_server.toml`; add corresponding Configuration table row to `docs/04_mcp_04_05_git.md`; extend tests

## Assumptions

- **CORRECTED**: Git MCP has a protected-branch policy enforced via `GitSecurityGuards._check_protected_branch()` (`scripts/mcp_servers/git/git_security.py:58-60`), and `GitConfig.protected_branches` (`scripts/mcp_servers/git/git_models.py:32`) is parsed from config. However, `protected_branches` is NOT set in `config/git_mcp_server.toml` (verified: NO MATCHES for `protected_branch`), so the protection mechanism exists but is currently inactive. The doc claim "has no protected-branch policy" should be corrected to reflect that the policy EXISTS in code but is not activated in the shipped config. The Force-Push block remains not applicable because `git_push` exposes no `force` parameter.

## Design decisions

- Each doc correction names the enforcing code symbol (`GitConfig.protected_branches`, `GitSecurityGuards._check_protected_branch()`, `_is_safe_ref()`/`_validate_ref()`, `config/agent.toml::approval_risk_rules`) and the test that verifies it, per the repository's evidence-labeling convention.
- REQ-006 config change follows the same shape as the already-tested `protected_branches` parameter `GitConfig` already accepts — no schema change, no new field. `GitConfig.from_dict()` (`git_models.py:43-45`) already parses `protected_branches` via `get_typed(..., list, ...)`.

## Alternatives considered

- **Alternative**: Leave `protected_branches` unset in `git_mcp_server.toml` and only fix docs. This would leave the mismatch between docs and runtime behavior uncorrected.
- **Alternative**: Use a different branch list than `["main", "master", "release"]`. The Issue's own Fix Intent step 3 was already exercised when `protected_branches` was implemented; this Plan only activates the already-decided mechanism for the real config.

## Implementation

### Target file

`docs/00_security_02_high-risk-tool-common-policy.md`

### Procedure

Correct the Git MCP bullet (~line 187) to state that a protected-branch policy exists while continuing to state that a technical Force-Push block is not applicable because `git_push` exposes no `force` parameter to guard.

### Method

Edit line ~187 in place. Replace the false claim "has no protected-branch policy and no technical Force Push block" with an accurate description naming `GitConfig.protected_branches` as the policy source and stating the Force-Push block is not applicable.

### Details

Current text (line 187):
```
- **Git MCP**: has no protected-branch policy and no technical Force Push block — the `branch`/`remote` arguments to `git_checkout`/`git_pull`/`git_push` are passed through without command-specific validation, which is an open gap, not a deviation covered by an additional restriction (documented in `04_mcp_04_05_git.md` Command-specific guard status; tracked as a Known Issue).
```

Replace with text that:
1. States `GitConfig.protected_branches` exists and is enforced via `GitSecurityGuards._check_protected_branch()`
2. States the Force-Push block is not applicable because `git_push` exposes no `force` parameter
3. Cross-references the existing test coverage (`test_git_security_compliance.py::test_check_protected_branch`, `test_git_checkout_protected_branch`, `test_git_push_protected_branch`, `test_is_safe_ref`)
4. Preserves the note about Dirty-Worktree/Detached-HEAD/postcondition gaps remaining (cross-reference `GIT-001`)

## Compatibility considerations

- No source code changes; no API or configuration schema impact.
- Operators reading the docs will see corrected information; no behavioral change until they set `allowed_repo_paths` and `read_only=false` in `git_mcp_server.toml`.

## Security considerations

- REQ-006 config activation: setting `protected_branches = ["main", "master", "release"]` could unexpectedly block legitimate automated operations to those branches once an operator populates `allowed_repo_paths` and sets `read_only=false`. Mitigation: `allowed_repo_paths` is currently `[]`, which already denies all git-mcp access independently of this change.

## Rollback considerations

- Doc corrections (REQ-001–REQ-005): revert to previous content if incorrect.
- REQ-006 config change: remove the `protected_branches` key from `git_mcp_server.toml`; restart git-mcp service.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_security_02_high-risk-tool-common-policy.md`, `docs/04_mcp_04_05_git.md`, `docs/04_mcp_90_inconsistencies_and_known_issues.md`, `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, `docs/04_mcp_01_tool_ownership_matrix.md` | Manual + tool | `uv run python tools/check_docs_consistency.py --domain mcp` | Passes; no internal contradiction remains between sections/documents about Git MCP branch protection or approval tier |
| `config/git_mcp_server.toml`, `scripts/mcp_servers/git/git_models.py` | Unit | `uv run pytest tests/mcp_servers/git/test_git_models.py -v` | New REQ-006 config-loading assertion passes |
| `scripts/mcp_servers/git/git_service.py` | Unit | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | New REQ-006 three-branch rejection case passes; existing cases unaffected |
| Full suite | Regression | `uv run pytest` and `uv run pre-commit run --all-files` | All pass, no new failures |

## Completion criteria

- REQ-001: `00_security_02_high-risk-tool-common-policy.md` no longer states that Git MCP has no protected-branch policy; it names `GitConfig.protected_branches` as the policy source and states the Force-Push block is not applicable.
- REQ-002: no section of `04_mcp_04_05_git.md` contradicts another section of the same document about whether protected-branch enforcement or the `"high"` approval override exists; Dirty-Worktree/Detached-HEAD/postcondition gaps remain stated, with a cross-reference to `GIT-001`.
- REQ-003: `MCP-003`'s `Current Description`/`Observed Implementation`/`Recommended Action` no longer claim protected-branch enforcement or ref-safety validation are absent; its `Status` and `Resolution Notes` reflect the narrowed, still-open scope (Dirty-Worktree/Detached-HEAD only, tracked via `GIT-001`).
- REQ-004: `04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`'s `WRITE_DANGEROUS` row no longer names `git_checkout`/`git_pull`/`git_push` as tools that fall back to the `y/N` prompt.
- REQ-005: `04_mcp_01_tool_ownership_matrix.md` shows `git_checkout`/`git_pull`/`git_push` on a distinct row from `git_add`/`git_commit`, with a Risk Tier that matches `tool_safety_tiers` and reflects the `"high"` override.
- REQ-006: `git_mcp_server.toml`'s `GitConfig.protected_branches` (as loaded by `GitConfig.load()`) equals `["main", "master", "release"]`; a test demonstrates that `git_checkout`/`git_pull`/`git_push` targeting any of those three branch names is rejected when the service is constructed from the shipped config file.

## Out of scope

- Any change to `scripts/mcp_servers/git/git_security.py`, `git_service.py`, `git_models.py`, or `scripts/agent/tool_policy.py` — Step 2 verification confirmed all of the Issue's code-level asks are already implemented.
- Any change to `config/agent.toml` — `approval_risk_rules` already has `git_checkout`/`git_pull`/`git_push = "high"` and `approval_high_risk_branches` already lists `main`/`master`/`release`.
- Dirty-Worktree / Detached-HEAD checks and postcondition verification for `git_checkout`/`git_pull`/`git_push` — these are ADR-012 Decision #5/#6 items, already tracked as Known Issue `GIT-001` in `docs/04_mcp_90_inconsistencies_and_known_issues.md`, and already covered by two other archived Plans (`plans/done/20260825-133945_plan.md`, `plans/done/20260825-134130_plan.md`). Not re-planned here.
- `docs/00_governance_03_issue-and-uncertainty-management.md` NC-019 — already correctly registered and does not need this Plan's changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Documentation reconciliation (REQ-001 through REQ-005) | Done | 2026-08-27 | 2026-08-27 | All REQs completed |
| 2 | Phase 2: Config activation and test coverage (REQ-006) | Done | 2026-08-27 | 2026-08-27 | Config already set; tests verified |
| 3 | Phase 3: Validation and deployment | Done | 2026-08-27 | 2026-08-27 | All validation passed |

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
- **Requirement ID**: REQ-001 through REQ-006
- **Source issue**: `issues/20260821_02_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-113056_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-26 19:08:17
- **Related target files**: `docs/00_security_02_high-risk-tool-common-policy.md`
