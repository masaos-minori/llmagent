## Goal

Add a "Test Isolation" subsection to `docs/05_agent_11_extension-points.md` under the "Registry API" section that documents the `_reset_for_testing()` restriction and autouse fixture pattern.

## Scope

- In-Scope:
  - Insert a `### Test Isolation` markdown subsection immediately after the Registry API table (after the `| \`_reset_for_testing()\` | Clear all registries (test-only) |` row and its closing `---` separator).
  - The subsection must cover all four required documentation points from the plan.
- Out-of-Scope:
  - Changes to any other section of this document.
  - Any Python source file.

## Assumptions

1. The Registry API table ends at approximately line 190 of the document, followed by a `---` separator before the "Extension Rules" section at line 194. The new subsection belongs between that `---` and `## Extension Rules`.
2. The four required points from the plan requirement are: (a) tests calling `load_plugins()` or `@register_*` must use `_reset_for_testing()` in an autouse fixture; (b) production code must never call `_reset_for_testing()`; (c) direct mutation of private registries (`_commands`, `_tools`, `_pipeline_post`) is forbidden; (d) the example fixture pattern is shown.
3. The existing `---` separator between Registry API and Extension Rules is the correct insertion point — the new subsection fits logically as elaboration on the registry API table row for `_reset_for_testing()`.

## Implementation

### Target file

`/home/masaos/llmagent/docs/05_agent_11_extension-points.md`

### Procedure

1. Read lines 188-200 of the file to identify the exact text around the `---` separator between Registry API and Extension Rules.
2. Insert the following markdown block between the `---` separator after the Registry API table and the `## Extension Rules` heading:

   ````markdown
   ### Test Isolation

   `_reset_for_testing()` is the **only** supported way to clear global registry state.

   Rules:
   - Tests that call `load_plugins()` or any `@register_*` decorator **must** call
     `_reset_for_testing()` in a `pytest.fixture(autouse=True)` before (and optionally after)
     each test function.
   - Production code (non-test modules) must **never** call `_reset_for_testing()`.
   - Direct mutation of `_commands`, `_tools`, or `_pipeline_post` is also forbidden in tests;
     use `_reset_for_testing()` + public decorators instead.

   Example:
   ```python
   import pytest
   import shared.plugin_registry as plugin_registry

   @pytest.fixture(autouse=True)
   def reset_registry():
       plugin_registry._reset_for_testing()
       yield
       plugin_registry._reset_for_testing()
   ```

   ````

3. Verify the four required points are covered in the inserted text.
4. Check that surrounding sections are unaffected by reading lines 185-205 after the edit.

### Method

- Use the Edit tool with `old_string` matching the `---` separator line immediately preceding `## Extension Rules`, and `new_string` prepending the new subsection before that separator.
- Alternatively, match the exact text `---\n\n## Extension Rules` and replace with `---\n\n### Test Isolation\n...\n\n---\n\n## Extension Rules`.

### Details

- The insertion point in the current file: after line `| \`_reset_for_testing()\` | Clear all registries (test-only) |` and the following `---` separator.
- Existing text to match for the Edit: `---\n\n## Extension Rules` (the separator line and subsequent heading).
- The example fixture in the subsection uses `reset_registry` as the fixture name (matches the actual fixture name in `tests/test_plugin_registry.py` line 20).

## Validation plan

```bash
# Confirm section is present
grep -n 'Test Isolation' /home/masaos/llmagent/docs/05_agent_11_extension-points.md

# Confirm all four required phrases
grep -c 'autouse' /home/masaos/llmagent/docs/05_agent_11_extension-points.md
grep -c 'production code' /home/masaos/llmagent/docs/05_agent_11_extension-points.md
grep -c 'forbidden' /home/masaos/llmagent/docs/05_agent_11_extension-points.md
```

Expected: `Test Isolation` appears once; `autouse`, `production code`, and `forbidden` each appear at least once.
