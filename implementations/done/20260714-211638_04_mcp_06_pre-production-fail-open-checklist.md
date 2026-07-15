# Implementation Procedure: Normalize MCP Security Policy Documentation (Pre-Production Fail-Open Checklist)

## Goal

Update `04_mcp_06_pre-production-fail-open-checklist.md` to reflect actual fail-closed behavior and remove references to nonexistent fields.

## Scope

- `docs/04_mcp_06_16_pre-production-fail-open-checklist.md` only
- Text updates and clarifications; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_11_require.md` is the canonical specification for this task.
2. Implementation inspection has confirmed the following actual behaviors:
   - `tool_definitions_strict` default = **False** (not true as implied by checklist)
   - Empty `workflow_allowlist` produces **RuntimeError/CicdAuthorizationError** (fail-closed), NOT a warning
   - `allowed_repos_mode` does **NOT** exist in codebase (was removed previously)
   - No DB MCP server exists

## Implementation

### Target file

`docs/04_mcp_06_16_pre-production-fail-open-checklist.md`

### Procedure

1. **Correct `tool_definitions_strict` checkbox**: Change from unchecked default to explicit production requirement.
2. **Clarify `workflow_allowlist` fail-closed behavior**: Replace vague "explicitly set" language with specific fail-closed description.
3. **Remove stale `allowed_repos_mode` reference**: Remove the reference in `05_agent_08_04_configuration-mcp-approval-obs.md`.
4. **Verify all checklist items match actual enforcement behavior**.

### Method

- Pattern-based search followed by targeted text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

#### Step 1: Correct tool_definitions_strict checkbox

Current line:
```
- [ ] `tool_definitions_strict = true`(スキーマ不整合時に致命的エラーとする)
```

This is correct as-is — it requires manual setting to `true` in production. However, the description should clarify that the **default is `false`**, so this is an active production override.

Change to:
```
- [ ] `tool_definitions_strict = true` (デフォルトは `false`; スキーマ不整合時に致命的エラーとするには本番で明示的に有効化)
```

#### Step 2: Clarify workflow_allowlist fail-closed behavior

Current line:
```
- [ ] `cicd-mcp`: `workflow_allowlist`が明示的に設定されている(空 = fail-closed: すべて拒否)
```

This is already correct — empty `workflow_allowlist` is fail-closed. However, the actual behavior is stricter than described: it raises **RuntimeError/CicdAuthorizationError at startup**, not just runtime denial.

Change to:
```
- [ ] `cicd-mcp`: `workflow_allowlist`が明示的に設定されている(空 = startup時に RuntimeError/CicdAuthorizationError で起動失敗する。fail-closed動作)
```

#### Step 3: Remove stale allowed_repos_mode reference

In `docs/05_agent_08_04_configuration-mcp-approval-obs.md`, line 47:
```
- GitHub `allowed_repos` / `allowed_repos_mode`
```

Change to:
```
- GitHub `allowed_repos`
```

#### Step 4: Verify all checklist items

Cross-reference each checklist item against actual implementation:
- `routing_drift_strict = true` — verify in code
- `plugin_strict = true` — verify in code
- `serial_tool_calls = false` — already documented correctly
- `allowed_tools` — verify empty-list behavior
- `tool_safety_tiers` — verify unknown-key handling
- `shell_sandbox_backend = "firejail"` — confirm production requirement
- `security_profile = "production"` — verify startup validation
- API keys — verify env var pattern

## Validation plan

1. Verify `tool_definitions_strict` description mentions default is `false`.
2. Verify `workflow_allowlist` description mentions RuntimeError/CicdAuthorizationError.
3. Verify no references to `allowed_repos_mode` remain.
4. Verify all checklist items match actual enforcement behavior.
5. Verify no broken cross-references from updated sections.
6. Run `pre-commit run --all-files` if linting is configured.
