# Implementation Procedure: Normalize MCP Security Policy Documentation (Major Default Values)

## Goal

Update `04_mcp_06_major-default-values.md` to clearly separate default values from production recommendations for security-sensitive parameters.

## Scope

- `docs/04_mcp_06_04_major-default-values.md` only
- Clarify distinction between code defaults and production requirements

## Assumptions

1. The requirement `requires/20260714_11_require.md` is the canonical specification for this task.
2. Implementation inspection has confirmed the following actual values:
   - `tool_definitions_strict` default = **False** (in `scripts/agent/config_dataclasses.py:188`)
   - `shell_sandbox_backend` default = **"none"** (in `mcp_servers/shell/models.py:48`)
   - Empty `workflow_allowlist` produces **RuntimeError/CicdAuthorizationError** (fail-closed), NOT a warning
   - `allowed_repos_mode` does **NOT** exist in codebase (was removed previously)
   - No DB MCP server exists

## Implementation

### Target file

`docs/04_mcp_06_04_major-default-values.md`

### Procedure

1. **Add production recommendation column**: Add a new column to the existing table for production-recommended values.
2. **Mark security-sensitive defaults**: Clearly mark which defaults require production overrides.
3. **Remove stale references**: Remove any references to nonexistent `allowed_repos_mode`.

### Method

- Pattern-based search followed by targeted text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

#### Step 1: Add production recommendation column

Modify the existing table to include a "Production recommended" column:

```markdown
| パラメータ | デフォルト | Production推奨 | Configファイル |
|---|---|---|---|
| tool_definitions_strict | false | true | `config/agent.toml::tool_definitions_strict` |
| shell_sandbox_backend | none | firejail | `config/shell_mcp_server.toml` |
| ... | ... | ... | ... |
```

#### Step 2: Mark security-sensitive defaults

For rows where the default is insecure in production, add a note:

```markdown
| shell_sandbox_backend | none | **firejail** (none = sandbox disabled) | `config/shell_mcp_server.toml` |
```

#### Step 3: Remove stale allowed_repos_mode references

Search for and remove any references to `allowed_repos_mode` in the document. This field was removed from the codebase in a previous cleanup.

## Validation plan

1. Verify no references to `allowed_repos_mode` remain in the document.
2. Confirm the production recommendation column is present and accurate.
3. Verify security-sensitive defaults are clearly marked as requiring production overrides.
4. Verify no broken cross-references from updated sections.
5. Run `pre-commit run --all-files` if linting is configured.
