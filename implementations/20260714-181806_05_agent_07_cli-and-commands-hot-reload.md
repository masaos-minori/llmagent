# Implementation Procedure: Align Configuration Documentation with Consolidated config/agent.toml Layout (Hot Reload)

## Goal

Rewrite `/reload` documentation to remove "12 base config files" language and describe actual reload behavior: reloads `config/agent.toml`, applies to live services.

## Scope

- `docs/05_agent_07_cli-and-commands-hot-reload.md` only
- Text rewrite; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_03_require.md` is the canonical specification for this task.
2. Agent configuration is consolidated in `config/agent.toml`.
3. `/reload` applies reloaded config to live services without restarting the agent.
4. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/05_agent_07_cli-and-commands-hot-reload.md`

### Procedure

1. **Locate `/reload` description**: Find the section documenting the `/reload` command.
2. **Remove "12 base config files" language**: Delete any mention of reloading "12 base config files".
3. **Rewrite reload description**: Describe actual behavior — reloads `config/agent.toml` and applies changes to live services.

### Method

- Text replacement via file edit.
- Preserve surrounding context and formatting.

### Details

- The current `/reload` description likely mentions reloading multiple config files. Rewrite to clearly state that `/reload` reloads `config/agent.toml` and propagates the updated configuration to running services.
- Example rewrite: "/reload: Reloads the agent configuration from `config/agent.toml` and applies changes to live services without requiring an agent restart."

## Validation plan

1. Verify the rewritten `/reload` description accurately reflects the actual reload behavior.
2. Confirm no remaining references to "12 base config files" in the document.
3. Verify no broken cross-references from removed sections.
4. Run `pre-commit run --all-files` if markdown linting is configured.
