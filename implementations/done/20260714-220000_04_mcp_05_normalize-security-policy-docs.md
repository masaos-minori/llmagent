# Implementation Procedure: Normalize MCP Security Policy Documentation

## Goal

Eliminate ambiguities across fail-open/fail-closed settings, production recommendations, and known issue status in MCP security documentation. Ensure defaults and production requirements are never conflated.

## Scope

### In-Scope
- Document `tool_definitions_strict` default vs production recommendation separately
- Document `shell_sandbox_backend` default vs production requirement separately
- Confirm and document CI/CD `workflow_allowlist` empty-list behavior (warning vs RuntimeError)
- Document GitHub `allowed_repos_mode` fail-open/fail-closed semantics
- Resolve stale `db_allowlist` references (remove if no DB MCP server exists)
- Update pre-production checklist to reflect current implemented controls

### Out-of-Scope
- Changing any actual security policy or enforcement logic
- Adding new security features

## Assumptions

1. The requirement `requires/20260714_10_require.md` is the canonical specification.
2. This is a documentation-only task; no source code changes are required unless implementation inspection reveals that documentation contradicts actual behavior.
3. The existing MCP catalog docs (`04_mcp_04_*`) already contain some of the needed information but may need cross-referencing updates.

## Unknowns (to be resolved during inspection)

1. What is the actual default value of `tool_definitions_strict`? Needs inspection of `shared/tool_constants.py` and agent config dataclasses.
2. Does an empty `workflow_allowlist` produce a RuntimeError or just a warning? Needs inspection of `mcp/cicd/service.py`.
3. Is `allowed_repos_mode` actually implemented for github-mcp? Needs inspection of `mcp/github/models_config.py` and `mcp/github/service_security.py`.
4. Does a DB MCP server exist? Check `config/*db*_mcp_server.toml`.

## Affected areas

- MCP security model documentation
- MCP server catalog documentation
- Pre-production checklist
- Known issues/inconsistencies documentation

## Implementation

### Procedure

#### Step 1: Inspect implementation defaults and behaviors

Inspect the following files to determine actual values and behaviors:

1. **`tool_definitions_strict`**:
   - `shared/tool_constants.py` — find default value
   - `agent/config_dataclasses.py` — find AgentConfig field definition
   - Determine if production validation is enforced

2. **`shell_sandbox_backend`**:
   - `mcp/shell/models_config.py` — find default value
   - `agent/security_audit_config.py` — find production validation behavior
   - Confirm `"none"` rejection at startup when `security_profile="production"`

3. **CI/CD `workflow_allowlist`**:
   - `mcp/cicd/models_config.py` — find default value
   - `mcp/cicd/service.py` — find startup behavior (RuntimeError vs warning)
   - Confirm `trigger_workflow` denial for empty allowlist

4. **GitHub `allowed_repos_mode`**:
   - `mcp/github/models_config.py` — find if `allowed_repos_mode` field exists
   - `mcp/github/service_security.py` — find fail-open/fail-closed behavior
   - Find startup audit or production validation behavior

5. **DB MCP server existence**:
   - `config/*db*_mcp_server.toml` — check if any DB MCP server config exists
   - If none exists, `db_allowlist` references should be removed

#### Step 2: Update target documents based on findings

Based on inspection results, update the following documents:

1. **`04_mcp_04_server_catalog.md`** (and individual server catalog files):
   - Separate default values from production recommendations in each server section
   - Add `allowed_repos_mode` documentation if found in github-mcp

2. **`04_mcp_05_security_and_safety_model.md`**:
   - Clarify fail-open/fail-closed summaries for all servers
   - Remove or add `allowed_repos_mode` to fail-open/fail-closed table
   - Remove stale `db_allowlist` references if no DB MCP server exists

3. **`04_mcp_06_major-default-values.md`**:
   - Separate "default" column from "production recommended" column
   - Ensure `tool_definitions_strict` and `shell_sandbox_backend` rows clearly distinguish defaults from production requirements

4. **`04_mcp_06_pre-production-fail-open-checklist.md`**:
   - Update checklist items to reflect current implemented controls
   - Ensure each item matches actual enforcement behavior

5. **`04_mcp_90_inconsistencies_and_known_issues.md`**:
   - Resolve the `workflow_allowlist` RuntimeError vs warning inconsistency
   - Update any stale entries related to `db_allowlist`

6. **`04_mcp_00_document-guide.md`**:
   - Update any high-level summaries that conflate defaults with production requirements

#### Step 3: Cross-document consistency verification

After updates, verify:
- No document says `shell_sandbox_backend = "none"` is acceptable in production
- No document conflates `tool_definitions_strict` default with production recommendation
- All fail-open/fail-closed descriptions reference the correct mode per server
- `db_allowlist` is either fully documented (if DB MCP exists) or fully removed

## Method

- Pattern-based search followed by targeted text replacement via file edit.
- Preserve surrounding context and formatting.
- Use consistent terminology across all documents.

## Validation plan

- Manual review of each updated document against the acceptance criteria
- Search for remaining instances of conflated defaults/production recommendations using grep patterns like `sandbox_backend.*none.*production` or `tool_definitions_strict.*false.*production`
- Verify no stale `db_allowlist` references remain if no DB MCP server exists

## Risks

- Finding that some documentation contradictions require source code fixes rather than doc-only changes (unlikely given the scope of this task)
- Missing one of the many overlapping documents that needs updating
