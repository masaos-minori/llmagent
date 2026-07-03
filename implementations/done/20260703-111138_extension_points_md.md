## Goal

Update `docs/05_agent_11_extension-points.md` to document the Option A command shadow rejection policy, update the log format line, Extension Rules item 2, `PluginLoadResult` field reference, and add a new "Command Shadow Policy" subsection.

## Scope

- In-Scope:
  - Update `PluginLoadResult` fields reference: `command_shadows` → `command_shadows_rejected`
  - Update startup log format line for command shadows to reflect rejection
  - Update "Built-in vs plugin priority" paragraph to add explicit rejection policy statement
  - Update Extension Rules item 2 to describe rejection behavior and strict-mode exception
  - Add new "Command Shadow Policy" subsection under the `@register_command` section
- Out-of-Scope:
  - Tool conflict policy documentation (already correct)
  - MCP server documentation
  - Pipeline stage documentation
  - Any file other than `docs/05_agent_11_extension-points.md`

## Assumptions

1. The log format change from `"[plugin] command shadow: ..."` to `"[plugin] command shadow rejected: ..."` in production code (Step 1) is complete before updating docs.
2. The doc section structure follows the existing heading hierarchy: `##` for top-level sections, `###` for subsections, `####` for sub-subsections.
3. The "Built-in vs plugin priority" paragraph is located under `## @register_command` (lines 67–69 of current file).
4. Extension Rules item 2 is at line 198: `"Plugin commands cannot use the same name as any built-in command"`.
5. The `PluginLoadResult` fields reference is at line 146: `'PluginLoadResult fields: loaded_count, failed, tool_conflicts_shadowed, tool_conflicts_allowed, command_shadows'`.

## Implementation

### Target file

`/home/masaos/llmagent/docs/05_agent_11_extension-points.md`

### Procedure

1. **Update startup log format line for command shadows** (line 33):
   - Current: `` `[plugin] command shadow: '<name>' in '<module>' shadows built-in` ``
   - New: `` `[plugin] command shadow rejected: '<name>' in '<module>' shadows built-in` ``

2. **Update "Built-in vs plugin priority" paragraph** (lines 67–69):
   - Current:
     ```
     Built-in commands in `_COMMANDS` list are matched first. If no built-in matches,
     `_dispatch_plugin()` is called. A plugin cannot override a built-in command name.
     ```
   - New (replace the paragraph):
     ```
     Built-in commands in `_COMMANDS` list are matched first. If no built-in matches,
     `_dispatch_plugin()` is called. Plugin commands that share a name with a built-in
     command are **rejected at load time** (removed from the plugin command registry).
     They will not appear in `iter_commands()` and cannot be dispatched. This is a
     startup-time enforcement, not a dispatch-time priority.
     ```

3. **Update Extension Rules item 2** (line 198):
   - Current: `2. Plugin commands cannot use the same name as any built-in command`
   - New:
     ```
     2. Plugin commands that share a name with a built-in command are **rejected** at
        load time and removed from the registry. A `PluginLoadError` is raised in strict mode.
     ```

4. **Update `PluginLoadResult` fields reference** (line 146):
   - Current: `command_shadows`
   - New: `command_shadows_rejected`
   - Full line: `PluginLoadResult fields: loaded_count, failed, tool_conflicts_shadowed, tool_conflicts_allowed, command_shadows_rejected`

5. **Add new "Command Shadow Policy" subsection** under `@register_command` section, after the existing "Built-in vs plugin priority" paragraph (after line 69, before the `---` separator at line 71):

```markdown
#### Command Shadow Policy

Plugin commands that share a name with a built-in command are subject to **Option A (reject)** policy:

- At load time, the shadowing command is **removed** from `_commands` and will not appear in `iter_commands()` or be dispatched.
- Log: `[plugin] command shadow rejected: '<name>' in '<module>' shadows built-in`
- When `plugin_strict = true`, a `PluginLoadError` is raised after all plugins are loaded, with a message containing `"Command builtin conflicts rejected: /help, /debug"` (comma-separated list of rejected command names).
- In non-strict mode (default), the rejection is silent beyond the log line — startup continues normally.
- `/plugin status` reports the count under `"Command shadows (rejected)"`.
```

### Method

- All changes are text replacements in a Markdown file; use the Edit tool with exact string matching.
- Preserve surrounding blank lines and heading levels.
- Do not reformat unrelated paragraphs.

### Details

- **Line 33** (startup log format for command shadow): update only this one line, not the tool conflict log format lines (29–30).
- **Line 69** (end of "Built-in vs plugin priority" paragraph): the paragraph ends at `A plugin cannot override a built-in command name.` — replace the entire paragraph.
- **Line 146** (`PluginLoadResult` fields reference): only `command_shadows` at the end of the line changes; all other field names remain.
- **Line 198** (Extension Rules item 2): replace only item 2; items 1, 3, 4, 5 are unchanged.
- **New subsection placement**: insert between the "Built-in vs plugin priority" paragraph and the `---` horizontal rule that ends the `@register_command` section.

## Validation plan

```bash
# Verify all changed strings are correct
grep -n 'command shadow' docs/05_agent_11_extension-points.md
# Expected: "command shadow rejected" (not bare "command shadow:")

grep -n 'command_shadows' docs/05_agent_11_extension-points.md
# Expected: only "command_shadows_rejected" (no bare "command_shadows" without "_rejected")

grep -n 'Command Shadow Policy' docs/05_agent_11_extension-points.md
# Expected: at least one match (new subsection heading)

grep -n 'rejected at load time' docs/05_agent_11_extension-points.md
# Expected: at least one match

# Verify Extension Rules item 2 is updated
grep -A2 '2\. Plugin commands' docs/05_agent_11_extension-points.md
```

Expected outcomes:
- No occurrence of bare `command_shadows` (without `_rejected`) in the file
- New subsection "Command Shadow Policy" present
- Log format line matches production code output
- Extension Rules item 2 describes rejection, not just prohibition
