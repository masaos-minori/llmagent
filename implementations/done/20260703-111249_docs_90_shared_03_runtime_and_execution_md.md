## Goal

Add a "Test isolation" note to section 4 (`plugin_registry`) of `docs/90_shared_03_runtime_and_execution.md` clarifying that `_reset_for_testing()` must not be called from non-test code and must be called in a fixture in any test file that touches the registry.

## Scope

- In-Scope:
  - Insert a single bold-text paragraph after the `get_last_load_result()` note (currently ending at line 159) and before the `---` separator at line 164.
- Out-of-Scope:
  - Changes to any other section of the document.
  - Changes to any Python source file.
  - Modifying the existing content of section 4 beyond the insertion.

## Assumptions

1. The insertion point is the blank line between the `- \`PluginFailure.error\` contains the full exception message...` bullet (line 160) and the `---` separator (line 164). Adding a blank line and the new paragraph there keeps the section coherent.
2. The required content from the plan Step 6: a bold-text sentence stating `_reset_for_testing()` clears all registries, must be called in `pytest.fixture(autouse=True)` in any test file that registers commands/tools/pipeline stages, and non-test code must never call it.
3. No surrounding content in the document changes.

## Implementation

### Target file

`/home/masaos/llmagent/docs/90_shared_03_runtime_and_execution.md`

### Procedure

1. Read lines 155-165 of the file to confirm the exact text around the insertion point.
2. After `- \`PluginFailure.error\` contains the full exception message from the failed plugin.` (line 160) and before the `---` separator, insert the following block:

   ```markdown

   **Test isolation:** `_reset_for_testing()` clears all registries and must be called
   in a `pytest.fixture(autouse=True)` in any test file that registers commands, tools,
   or pipeline stages. Non-test code must never call this function.
   ```

3. Verify the surrounding context is unchanged by reading lines 155-168 after the edit.

### Method

- Use the Edit tool. Match `old_string` to the exact line sequence:
  ```
  - `PluginFailure.error` contains the full exception message from the failed plugin.\n\n\n\n---
  ```
  and replace with the same content plus the new paragraph inserted between the bullet and the `---` separator.
- Alternatively match the two consecutive blank lines before `---` and insert the paragraph there.

### Details

- Exact current text at lines 159-164 (from Read output):
  ```
  - `get_last_load_result()` returns the most recent `PluginLoadResult`, or `None` before first load.
  - `PluginLoadError` is raised only when `strict_mode=True` and there are failures or MCP conflicts.
  - `PluginFailure.error` contains the full exception message from the failed plugin.



  ---
  ```
- Insert after the last bullet and before the blank lines preceding `---`.
- Resulting text must have the new paragraph followed by at least one blank line before `---`.

## Validation plan

```bash
# Confirm the new text is present
grep -n 'Test isolation' /home/masaos/llmagent/docs/90_shared_03_runtime_and_execution.md

# Confirm _reset_for_testing now appears in section 4
grep -n '_reset_for_testing' /home/masaos/llmagent/docs/90_shared_03_runtime_and_execution.md
```

Expected: `Test isolation:` appears in the document; `_reset_for_testing` appears in the section 4 context (not just in code blocks under other sections).
