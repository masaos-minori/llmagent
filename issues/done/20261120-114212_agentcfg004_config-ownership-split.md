# Separate configuration ownership of Memory, RAG, Session, Workflow, and DB maintenance

## Priority
Medium

## Summary
Give each process and database domain one owner for its configuration: move the Memory embedding endpoint out of the misnamed Agent RAG section, keep RAG Pipeline MCP settings in its own file, and stop DB maintenance code from reading the whole Agent configuration implicitly.

## Background
Source: consolidated `agent.toml` reduction backlog (`memo-issue.md`, Issue 4).

Evidence (`Explicit in code`, by reading and `rg`): `RAGConfig` in `scripts/agent/config_dataclasses.py` (line 156) holds `embed_url` and is attached as `AgentConfig.rag` (line 398); `MemoryConfig` is a separate class (line 229) with its own `embed_url` validation; `scripts/db/config.py` (lines 86-91), `scripts/db/maintenance.py` (lines 96-97), and `scripts/db/rotation.py` (lines 17-18) load `agent.toml`; `config/agent.toml` (lines 7-11) holds `rag_db_path`, `sqlite_vec_so`, and `embed_url` while `config/rag_pipeline_mcp_server.toml` (lines 10-16) holds the same three keys. Which process reads which key, and whether the Agent should rotate every DB, are from the backlog and `Needs confirmation`.

## Problem
The Agent configuration also carries RAG, Session, and Workflow database paths and maintenance settings that `scripts/db/` reads directly, and the RAG Pipeline MCP keeps its own copies. The names and the owners do not match, which blocks moving any of these settings safely.

## Reason for Change
Unclear ownership of configuration and databases (the config-isolation decision of ADR-002 and the database separation of ADR-008 apply). It is independent of the tool-policy work and can proceed in parallel.

## Implementation Intent
Each setting has one owning process. The Agent owns Memory embedding settings in the Memory section; the RAG Pipeline MCP owns its endpoint, database path, and sqlite-vec path in its own file; Session and Workflow database settings stay with the Agent or move to a typed database manifest; maintenance settings (archive, quarantine, drill artifacts, retention, checkpoint) form one typed maintenance configuration that callers receive, instead of `scripts/db/` loading `agent.toml` itself. Values equal to the code default stay explicit in the file that owns them.

## Target Files or Areas
- `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`
- `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`
- `scripts/db/config.py`, `scripts/db/maintenance.py`, `scripts/db/recovery.py`, `scripts/db/rotation.py`
- `scripts/agent/services/db_maintenance_service.py`, the Memory implementation under `scripts/agent/memory/`, and the Memory reload service
- Deployment configuration mounts for the services (`Unknown`)

## Required Changes
- Move `RAGConfig.embed_url` to `MemoryConfig.memory_embed_url`, remove `AgentConfig.rag`, and require the URL only when Memory embedding is enabled.
- Validate Memory reload through a typed candidate.
- List the owner and readers of `rag_db_path`, `session_db_path`, and `workflow_db_path`; give the RAG database settings to the processes that open that database.
- Group archive, quarantine, drill, retention, and checkpoint settings into a typed maintenance configuration and inject it; remove the implicit full `agent.toml` load from `scripts/db/`.
- Decide whether the Agent should rotate RAG, Session, and Workflow together, and align each domain's recovery policy with its configuration owner.
- Reduce hand-written valid-key additions in the production validator.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change; do not write or simulate that approval.
- Follow the Current-Specification-Only policy: the old key locations are rejected, not read as aliases.
- Do not delete a TOML value only because it equals the code default.

## Acceptance Criteria
- [ ] No Agent configuration type named `RAGConfig` remains.
- [ ] The Memory embedding endpoint is a Memory setting.
- [ ] The RAG Pipeline MCP starts from its own file without reading `agent.toml`.
- [ ] `scripts/db/` reads no Agent setting it does not need.
- [ ] Each database path and maintenance policy has one owner.
- [ ] Explicit TOML values survive the move.

## Testing Expectations
- Memory embedding enabled and disabled validation; RAG Pipeline MCP standalone startup; Session and Workflow maintenance; rotation and recovery of the three databases; per-process config file access isolation.
- Run `tools/check_db_separation.py`, ruff, mypy, import-linter, and the affected tests.

## Documentation Impact
Yes. Configuration ownership per process and database; the moved keys.

## Out of Scope
- Tool policy, tool catalog, and approval metadata (`issues/20261120-114209_agentcfg001_tool-policy-mode.md`, `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`, `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`); changes to the database schema.

## Dependencies
- No prerequisite; can proceed in parallel with `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`. Blocks `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md` and `issues/20261120-114214_agentcfg006_reduction-integration-verification.md`.
- Related: `issues/20261119-145303_cliplc005_staged-reload-transaction.md` changes Memory reload validation; the Memory candidate validation here uses its typed model.

## Unresolved Questions
- `不明`: whether Session and Workflow settings stay in `agent.toml` or move to a database manifest.
- `不明`: how the service units and containers mount configuration files.

## AI Implementation Instruction
List owners and readers first and confirm them against source before moving a key. Keep database behavior unchanged. Do not write ADR approval statements. Stop and report if a process still needs an Agent setting after the move.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-114212
- **Related target files**: `config/agent.toml`, `config/rag_pipeline_mcp_server.toml`, `scripts/agent/config_dataclasses.py`, `scripts/agent/config_section_builders.py`, `scripts/db/config.py`, `scripts/db/maintenance.py`, `scripts/db/recovery.py`, `scripts/db/rotation.py`, `scripts/agent/services/db_maintenance_service.py`
