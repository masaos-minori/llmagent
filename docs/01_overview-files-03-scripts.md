---
title: "Scripts File Structure: Agent Core & Memory (Part 1/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - [01_overview.md](01_overview.md)

# File Structure

Architecture Overview → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. File Structure

### Key Directories and Responsibilities

#### Agent REPL Package (`scripts/agent/`)

| Responsibility | Files |
|---|---|
| Entry point | `__main__.py`, `repl.py` |
| Startup sequence | `startup.py`, `context.py` |
| Configuration | `config_builders.py`, `config_dataclasses.py` |
| Session management | `session.py`, `session_message_repo.py` |
| Turn control | `orchestrator.py`, `llm_turn_runner.py` |
| Tool execution | `tool_runner.py`, `tool_scheduler.py`, `tool_policy.py`, `tool_approval.py` |
| Tool guard | `tool_loop_guard.py` |
| Tool auditing | `security_audit_config.py`, `tool_audit.py` |
| Write boundaries | `repository_gateway.py` |
| Output formatting | `output_tags.py`, `tool_output.py`, `tool_result_formatter.py` |
| Error handling | `llm_transport_errors.py`, `tool_exceptions.py`, `error_injection_service.py` |
| Lifecycle | `lifecycle.py`, `lifecycle_protocol.py`, `http_lifecycle.py`, `repl_health.py` |
| CLI | `cli_view.py` |
| Component construction | `factory.py` |
| Diagnostics | `diagnostic_store.py` |
| Mode classification | `mdq_rag_classifier.py`, `mode_classification.py` |
| Conversation history | `history.py`, `history_selection_policy.py` |
| Tool enums | `tool_enums.py` |
| Tool data models | `tool_models.py` |
| Tool argument validation | `tool_arg_validator.py` |
| Message schema | `message_schema.py` |
| Turn result | `turn_result.py` |

#### Memory Subpackage (`scripts/agent/memory/`)

| Responsibility | Files |
|---|---|
| Data model | `types.py`, `models.py`, `enums.py` |
| Storage | `store.py`, `jsonl_store.py` |
| Search | `retriever.py`, `fts_query.py` |
| Embedding | `embedding_client.py` |
| Ingestion | `ingestion.py` |
| Injection | `injection.py` |
| Mapping | `mapper.py` |
| Scoring | `scoring.py`, `rrf.py` |
| Operations | `count_ops.py`, `write_ops.py`, `pin_ops.py`, `import_ops.py`, `rebuild_ops.py` |
| Constants | `sql_constants.py` |

### Notes on Changes

- When changing session persistence schema, check both `store.py` and `sql_constants.py` together.
- When changing tool approval flow, check both `tool_approval.py` and `repository_gateway.py` together.
- When changing memory search algorithms, check both `retriever.py` and `scoring.py` together.

### Reference for Implementation Details

Refer to the repository implementation tree for the full list of files.

## Related Documents

- `01_overview-files-03-scripts.md`
- [01_overview.md](01_overview.md)

## Keywords

scripts
agent
mcp-server
file-structure
