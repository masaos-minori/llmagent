# Implementation: Update docs/05_agent_11_extension-points.md (req 24 — Step 4)

## Goal

Document the hook error isolation behavior, `hook_strict` parameter, and log visibility in `docs/05_agent_11_extension-points.md`.

## Scope

- `docs/05_agent_11_extension-points.md` — update Extension Rules item 4 and add Hook Failure Behavior section

## Assumptions

1. The existing Extension Rules section lists numbered rules for `@register_pipeline_stage`.
2. The update adds clarification that exceptions are caught in normal mode and re-raised in strict mode.
3. The `hook_strict` parameter is mentioned for testing/debugging purposes.

## Implementation

### Target file

`docs/05_agent_11_extension-points.md`

### Procedure

1. Locate the `@register_pipeline_stage` section and its Extension Rules.
2. Update or add item 4 to clarify exception handling.
3. Add a "Hook Failure Behavior" subsection after the Extension Rules.

### Method

Edit tool.

### Details

Find the Extension Rules section in the `@register_pipeline_stage` block and add/update:

```markdown
#### Hook Failure Behavior

In normal mode (default), exceptions raised by post-rerank hooks are:
- Caught by `run_pipeline_stages()` in `shared/plugin_registry.py`
- Logged as warnings with the hook name, error type, and query context
- Skipped: the pipeline continues with the hits as they were before that hook ran

This means a broken hook never breaks the RAG pipeline for the user.

In strict mode (`hook_strict=True` on `RagPipeline.run()`), the first hook failure
raises the original exception to the caller. Use this mode in tests to verify hook behavior.

Log format (both modes): `Plugin hook "<name>" failed on query "<query>": <ErrorType>: <message>`
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Grep | `grep -n "hook_strict\|Hook Failure" docs/05_agent_11_extension-points.md` | lines present |
