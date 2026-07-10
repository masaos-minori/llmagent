# Implementation: Update documentation for `allowed_repos_mode` removal (Phase A-4)

## Goal

Bring `docs/04_mcp_05_security_and_safety_model.md`, `docs/04_mcp_04_server_catalog.md`, `docs/04_mcp_06_configuration_and_operations.md`, and `docs/01_overview-files-shared.md` in line with the code changes from Phase A-1 through A-3: no configurable `allowed_repos_mode` remains; github-mcp is fail-closed only, identical in shape to git-mcp, cicd-mcp, and mdq-mcp's existing fail-closed descriptions.

## Scope

**In:**
- `docs/04_mcp_05_security_and_safety_model.md`: rewrite the github-mcp row in the "Access Control by Server" table (line 19) and the entire "`allowed_repos` / `allowed_repos_mode` (github-mcp)" subsection (lines 54-69, including the mode-comparison table and the production/local paragraph)
- `docs/04_mcp_04_server_catalog.md`: remove `allowed_repos_mode` from the "Config fields" line (94) and the "Security controls" bullet (97)
- `docs/04_mcp_06_configuration_and_operations.md`: remove or rewrite the `allowed_repos_mode = "fail_closed"` checklist item (line 874) in the Pre-Production Fail-Open Checklist
- `docs/01_overview-files-shared.md`: remove the `(allowed_repos_mode fail-fast 等)` parenthetical from the one-line description of `production_config_validator.py` (line 81)

**Out:**
- No other server's documentation (file-*, shell-mcp, cicd-mcp, git-mcp, mdq-mcp rows) — unaffected, they never had a mode concept

## Assumptions

1. All four doc locations were identified by `grep -rln "allowed_repos_mode" docs/` against the current (pre-Phase-A-1) codebase state — no other doc file references the field.
2. Since github-mcp becomes fail-closed-only, its documented behavior converges with the existing pattern already used for git-mcp, cicd-mcp, and mdq-mcp in the same "Access Control by Server" table — the rewritten row and subsection should mirror that established phrasing rather than invent new wording.

## Implementation

### Target file

1. `docs/04_mcp_05_security_and_safety_model.md`
2. `docs/04_mcp_04_server_catalog.md`
3. `docs/04_mcp_06_configuration_and_operations.md`
4. `docs/01_overview-files-shared.md`

### Procedure

1. In `docs/04_mcp_05_security_and_safety_model.md`, line 19, change:
   ```
   | github-mcp | `allowed_repos` + `allowed_repos_mode` | fail-closed (empty = deny all writes) |
   ```
   to:
   ```
   | github-mcp | `allowed_repos` | fail-closed (empty = deny all writes) |
   ```
2. In the same file, replace lines 54-69 (the full `### allowed_repos / allowed_repos_mode (github-mcp)` subsection) with:
   ```markdown
   ### `allowed_repos` (github-mcp)

   ```toml
   allowed_repos = ["org/myrepo", "org/otherrepo"]
   ```

   - Empty → all repo access denied (fail-closed)
   - Non-empty → only listed repos allowed
   ```
   (matching the phrasing style already used for `allowed_repo_paths` in the "Path Controls" section above it)
3. In `docs/04_mcp_04_server_catalog.md` line 94, remove `, allowed_repos_mode` from the "Config fields" list.
4. In the same file, line 97, change:
   ```
   - `allowed_repos` / `allowed_repos_mode` (fail-closed by default; empty list = deny all when mode is "fail_closed")
   ```
   to:
   ```
   - `allowed_repos` (fail-closed; empty list = deny all)
   ```
5. In `docs/04_mcp_06_configuration_and_operations.md`, remove the line:
   ```
   - [ ] `allowed_repos_mode = "fail_closed"` in `github_mcp_server.toml` (`"fail_open"` is rejected at production startup)
   ```
   from the Pre-Production Fail-Open Checklist (the surrounding `allowed_repos` non-empty checklist item on the preceding line stays, since it is still relevant).
6. In `docs/01_overview-files-shared.md` line 81, change:
   ```
   │       ├─ production_config_validator.py   # ProductionConfigValidator: 本番環境固有の設定検証 (allowed_repos_mode fail-fast 等)
   ```
   to:
   ```
   │       ├─ production_config_validator.py   # ProductionConfigValidator: 本番環境固有の設定検証
   ```
7. Run `grep -rn "allowed_repos_mode" docs/` — expect 0 matches.

### Method

Direct prose/table edits; no new documentation structure introduced. The rewritten github-mcp section is shortened to match the established one-line-per-control pattern already used elsewhere in the same file.

### Details

- The "Mode" comparison table (lines 61-65 in the original) is deleted entirely rather than reduced to one row, since a single-row "mode comparison" table reads oddly — prose (as used for `allowed_repo_paths`) is the better fit once there is only one behavior to describe.
- No cross-reference updates are needed elsewhere in `docs/04_mcp_*` — `04_mcp_00_document-guide.md` and `04_mcp_90_inconsistencies_and_known_issues.md` do not mention `allowed_repos_mode` (confirmed by grep).

## Validation plan

```bash
grep -rn "allowed_repos_mode" docs/   # expect no output
grep -rn "fail_open" docs/04_mcp_05_security_and_safety_model.md docs/04_mcp_04_server_catalog.md docs/04_mcp_06_configuration_and_operations.md   # expect no output
```

Expected outcome: zero remaining references to `allowed_repos_mode` or `fail_open` in `docs/`, and the github-mcp documentation reads consistently with the other fail-closed-only servers in the same tables.
