# Implementation: Align /health Probe Examples with Server-Specific Fields

## Goal

Update `/health` probe examples in `04_mcp_06` to show base response + server-specific fields for each server type.

## Scope

**In:**
- `docs/04_mcp_06_configuration_and_operations.md` — update /health probe examples

**Out:** No changes to `/health` endpoints or response schema.

## Assumptions

1. Base response: `{"status": "ok", "version": "...", "server_key": "..."}`.
2. shell-mcp adds: `sandbox_backend`, `sandbox_ready`.
3. rag-pipeline-mcp adds: `pipeline_ready`, `model_loaded`.
4. Examples in `04_mcp_06` may be simplified and missing server-specific fields.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`

### Procedure

1. Read shell-mcp and rag-pipeline-mcp entries in `docs/04_mcp_04_server_catalog.md` to confirm their `/health` extra fields.
2. Read `docs/04_mcp_02_protocol_and_transport.md` to confirm the base `/health` response shape.
3. Read the probe/health examples section in `docs/04_mcp_06_configuration_and_operations.md`.
4. Update examples to show base + server-specific fields.

### Method

Read catalog and protocol docs → Edit patches in `04_mcp_06`.

### Details

**Updated probe examples:**

```markdown
## Health Probe Examples

### Base response (all servers)
```json
{"status": "ok", "version": "1.0.0", "server_key": "file_read"}
```

### shell-mcp additional fields
```json
{
  "status": "ok",
  "version": "1.0.0",
  "server_key": "shell_exec",
  "sandbox_backend": "firejail",
  "sandbox_ready": true
}
```

### rag-pipeline-mcp additional fields
```json
{
  "status": "ok",
  "version": "1.0.0",
  "server_key": "rag_pipeline",
  "pipeline_ready": true,
  "model_loaded": true,
  "index_doc_count": 1423
}
```
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Server-specific fields present | `grep -n "sandbox_backend\|pipeline_ready" docs/04_mcp_06_configuration_and_operations.md` | found |
| No code changes | `git diff scripts/` | empty |
