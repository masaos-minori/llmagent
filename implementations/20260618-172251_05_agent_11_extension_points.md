# Implementation: Document new plugin diagnostics

## Goal

`docs/05_agent_11_extension-points.md` accurately reflects the new command-shadowing warnings, return-type validation, and per-failure startup logging.

## Scope

**In scope:**
- `docs/05_agent_11_extension-points.md` — update Loading section, add shadowing and type validation subsections

**Out of scope:**
- `docs/05_agent_08_configuration.md` (env-var override deferred per plan)

## Assumptions

1. The code changes described in sibling implementation docs are applied first. This doc reflects the post-change behavior.

## Implementation

### Target file

`docs/05_agent_11_extension-points.md`

### Procedure

Two edits to the existing document.

---

### Edit 1: Update Plugin Loading section (lines 16-21)

**Current text:**
```
**Loading:**
1. `AgentREPL._init_plugin_registry()` calls `plugin_registry.load_plugins(plugin_dir)` at startup
2. Each `*.py` file is imported in alphabetical order
3. `@register_*` decorators run at import time and register handlers globally
4. Errors during load are logged and skipped (fail-open)
5. Directory not found → 0 plugins loaded (no error)
```

**Replace with:**
```
**Loading:**
1. `AgentREPL._init_plugin_registry()` calls `plugin_registry.load_plugins(plugin_dir)` at startup
2. Each `*.py` file is imported in alphabetical order
3. `@register_*` decorators run at import time and register handlers globally
4. Errors during load are logged individually with file name and error reason (fail-open by default)
5. When `plugin_strict=true` in config, the first import failure aborts startup
6. After loading, plugin command names are checked against built-in commands; shadowing is logged as a warning
7. Directory not found → 0 plugins loaded (no error)

Startup log format (individual failure):
`Plugin load failure: <filename> — <ErrorType>: <message>`

Startup log format (command shadowing warning):
`Plugin command "/name" shadows built-in command. The built-in command will take precedence.`
```

---

### Edit 2: Add return-type validation note to `@register_tool` section (around line 62)

**Find the `@register_tool` section.** After the line "Return value: `(result_text: str, is_error: bool)`" (current line 71), add:

```
**Return-type validation:** At registration time, `@register_tool` inspects the
function's return annotation. If the annotation is present and is not
`tuple[str, bool]`, a warning is logged. This check is non-blocking — the tool
is still registered regardless of the annotation.
```

---

### Validation Plan

| Check | Method | Target |
|---|---|---|
| Accuracy | Compare doc with implemented behavior of plugin_registry.py and factory.py | All descriptions match |
| Consistency | Cross-reference error message formats | Log format in doc matches code |
| Markdown | Manual review | No broken links or formatting issues |
