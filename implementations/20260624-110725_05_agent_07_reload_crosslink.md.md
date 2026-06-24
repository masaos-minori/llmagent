# Implementation: Cross-Link /reload with Config Doc

## Goal

Add hot-reload annotation table to `05_agent_08` config entries. Add cross-reference in `05_agent_07` `/reload` section.

## Scope

**In:**
- `docs/05_agent_08_configuration_and_settings.md` — add hot-reload flag to config table
- `docs/05_agent_07_command_system.md` — add cross-reference in `/reload` section

**Out:** No changes to reload behavior.

## Assumptions

1. Some config keys take effect immediately on `/reload`; others require restart.
2. `05_agent_08` is the canonical config reference.
3. Current `05_agent_07` `/reload` section does not indicate which settings hot-reload.

## Implementation

### Target file

`docs/05_agent_08_configuration_and_settings.md`, `docs/05_agent_07_command_system.md`

### Procedure

1. Read reload implementation to identify hot-reloadable keys:
   ```bash
   grep -rn "reload\|hot_reload\|on_reload\|_after_reload" agent/ --include="*.py" | head -20
   ```
2. Read `docs/05_agent_08_configuration_and_settings.md` config table.
3. Add "Hot-reload?" column to config table.
4. Read `docs/05_agent_07_command_system.md` `/reload` section.
5. Add cross-reference and brief note about hot-reload vs restart requirements.

### Method

Bash grep → Read docs → Edit patches.

### Details

**Hot-reload annotation for `05_agent_08` config table (example rows):**

```markdown
| Setting | Default | Hot-reload? | Notes |
|---|---|---|---|
| `log_level` | `INFO` | Yes | Takes effect immediately |
| `max_turns` | `10` | Yes | Applied to next turn |
| `mcp_timeout` | `30` | Yes | Applied to next request |
| `db_path` | `./data/agent.sqlite` | **No** | Requires restart |
| `embedding_model` | `...` | **No** | Requires restart |
| `use_tool_dag` | `false` | Yes | Applied to next turn |
```

**Cross-reference in `05_agent_07` `/reload` section:**

```markdown
### /reload

Reloads agent configuration from disk without restarting the agent.

**Hot-reloadable settings:** log_level, max_turns, mcp_timeout, use_tool_dag, and others.
**Requires restart:** db_path, embedding_model, any transport configuration.

For the complete hot-reload / restart matrix, see `05_agent_08` §Configuration Reference.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Hot-reload column in 05_agent_08 | `grep -n "Hot-reload\|hot.reload" docs/05_agent_08_configuration_and_settings.md` | found |
| Cross-reference in 05_agent_07 | `grep -n "05_agent_08" docs/05_agent_07_command_system.md` | found |
| No code changes | `git diff agent/` | empty |
