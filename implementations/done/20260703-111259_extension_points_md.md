## Goal

Update `docs/05_agent_11_extension-points.md` to explicitly state that the runtime validation in `ToolExecutor.execute()` enforces **exactly** two elements (`len == 2`), rejecting tuples with more or fewer elements.

## Scope

- In-Scope:
  - Add a runtime validation note under the `## @register_tool` section, after the existing "Return-type validation (fail-fast)" paragraph
- Out-of-Scope:
  - Changing any other section of the document
  - Changing any source code file
  - Adding migration notes (the commit message covers breaking change communication)

## Assumptions

1. The section to update is in `docs/05_agent_11_extension-points.md` starting around line 85 under the `@register_tool` heading.
2. The insertion point is after the existing "Why fail-fast instead of warn?" block (approximately line 98-99) and before the `- Access:` bullet on line 100.
3. No other doc file references the `< 2` length check that would also need updating.

## Implementation

### Target file

`/home/masaos/llmagent/docs/05_agent_11_extension-points.md`

### Procedure

1. Read lines 85-105 of `docs/05_agent_11_extension-points.md` to confirm the exact insertion point.
2. After the "Why fail-fast instead of warn?" paragraph (the line ending `...causing unexpected behavior at call time. Failing at registration makes the error unmissable.`) and before the `- Access:` bullet, insert the following block:

```markdown
**Runtime return value validation:** `ToolExecutor.execute()` validates the actual return value at call time. It checks that the return is a `tuple` with **exactly 2 elements** (`len == 2`), that `result[0]` is `str`, and that `result[1]` is `bool`. A tuple with more or fewer than 2 elements raises `ValueError`. A non-`str` first element raises `TypeError`. A non-`bool` second element raises `TypeError`.
```

3. Verify that the new paragraph is logically adjacent to the registration-time validation description and reads as a continuation of the "fail-fast" contract section.

### Method

- Use `Edit` tool with `old_string` set to the exact text of the "Why fail-fast" paragraph end + the `- Access:` bullet start, inserting the new paragraph between them.
- Keep the paragraph concise (one block, no sub-bullets) to match the existing doc style.

### Details

Exact `old_string` anchor to use for the Edit:
```
**Why fail-fast instead of warn?** Silent warnings were missed in production, causing
unexpected behavior at call time. Failing at registration makes the error unmissable.

- Access: `plugin_registry.get_tool(name)` → `Callable | None`
```

`new_string` (insert new paragraph between the two):
```
**Why fail-fast instead of warn?** Silent warnings were missed in production, causing
unexpected behavior at call time. Failing at registration makes the error unmissable.

**Runtime return value validation:** `ToolExecutor.execute()` validates the actual return value at call time. It checks that the return is a `tuple` with **exactly 2 elements** (`len == 2`), that `result[0]` is `str`, and that `result[1]` is `bool`. A tuple with more or fewer than 2 elements raises `ValueError`. A non-`str` first element raises `TypeError`. A non-`bool` second element raises `TypeError`.

- Access: `plugin_registry.get_tool(name)` → `Callable | None`
```

## Validation plan

1. Read the modified section of the file after editing to confirm the paragraph appears in the correct location and the surrounding text is intact.
2. Run a grep to confirm the word "exactly" now appears in the doc:
   ```
   grep -n "exactly" docs/05_agent_11_extension-points.md
   ```
   Expected: one or more matches in the `@register_tool` section.
3. No automated tests apply to doc files; visual inspection is sufficient.
