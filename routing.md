# Context Loading Reference

Maps task type to files that must be loaded. Read this immediately after AGENTS.md.

## Task → skill mapping

Skills can be invoked as slash commands (e.g. `/python-implementation`) or via `Skill("python-implementation")`. The command reads `skills/*/SKILL.md` automatically.

| Task type | Keywords | Load |
|---|---|---|
| Feature / bug fix / new module | add, implement, fix, create, modify | `skills/python-implementation/SKILL.md` |
| Debug / root cause | debug, error, exception, crash, trace, log, slow, hang | `skills/python-debug-root-cause/SKILL.md` |
| Lint / type errors / CI fix | lint, ruff, mypy, pyright, type error, CI, pre-commit | `skills/python-lint-typecheck/SKILL.md` |
| Test / pytest / flaky | test, pytest, flaky, coverage, assertion, regression | `skills/python-test-and-fix/SKILL.md` |
| Refactor / rename / CST | refactor, rename, restructure, split, move, import cycle | `skills/python-refactoring/SKILL.md` |
| Plan / design / ticket | plan, design, analyze, assess, spec, ticket | `skills/python-issue-to-plan/SKILL.md` + `skills/python-issue-to-plan/workflow.md` |
| Architecture / module design | architecture, module, interface, data model, component | `skills/python-design/SKILL.md` + `skills/python-design/workflow.md` |
| MCP server / new server | mcp server, new server, install server | `skills/mcp-server-add/SKILL.md` + `rules/env.md` + `docs/04_mcp_03_routing_lifecycle_and_execution.md` + `docs/04_mcp_06_configuration_and_operations.md` |
| Deploy / production | deploy, /opt/llm, service restart, init.d | `skills/deploy/SKILL.md` + `rules/env.md` + `docs/05_agent_10_operations-and-observability.md` |
| Event Bus implementation / debug | eventbus, event bus, dlq, sse subscribe, replay | `skills/python-implementation/SKILL.md` + `rules/env.md` |
| Documentation / docs | document, doc, write docs, readme, changelog | `skills/python-documentation/SKILL.md` |
| Git commit / sync | commit, stage, push, pull, git sync, conflict, git workflow | `skills/git-commit-and-sync/SKILL.md` |

## Workflow files

Invoke directly by filename. Not triggered by routing.

| Workflow | File |
|---|---|
| Plan (requirement → work plan) | `01_plan.md` |
| Design (work plan → implementation docs) | `02_design.md` |
| Implementation (implementation doc → code) | `03_implementation.md` |

## Docs → task mapping

Load only the docs relevant to the specific task. Do NOT load all `docs/*.md`.

### Domain specs

| Task scope | Reference docs |
|---|---|
| Agent spec (overview, design, known issues) | `docs/05_agent_00_document-guide.md` + `docs/05_agent_01_system-overview.md` |
| Agent known issues / inconsistencies | `docs/05_agent_90_inconsistencies_and_known_issues.md` |
| MCP server spec (overview, design, known issues) | `docs/04_mcp_00_document-guide.md` + `docs/04_mcp_01_system_overview.md` |
| RAG pipeline spec (overview, design, known issues) | `docs/03_rag_00_document-guide.md` + `docs/03_rag_01_system_overview.md` |
| MDQ vs RAG boundary | `docs/04_mcp_05_security_and_safety_model.md` §MDQ vs RAG Boundary |
| DB layer spec (schema, ops, known issues) | `docs/90_shared_04_db_architecture_and_schema.md` + `docs/90_shared_05_db_api_and_operations.md` |
| Shared infra spec (config, logging, types, constants) | `docs/90_shared_00_document-guide.md` + `docs/90_shared_01_overview.md` |

### Implementation reference

#### System overview

| Task scope | Reference docs |
|---|---|
| System-wide architecture overview | `docs/01_overview.md` + `docs/01_overview-arch.md` |
| File / module layout | `docs/01_overview-files.md` |
| Documentation set index / navigation | `docs/00_llm-implementation-guide.md` |
| Deployment / env setup | `docs/02_deployment.md` + `rules/env.md` |

#### Agent

| Task scope | Reference docs |
|---|---|
| Memory layer (types / store / retriever / extract / jsonl_store / services.py) | `docs/05_agent_04_state-and-persistence.md` + `docs/05_agent_08_configuration.md` + `docs/05_agent_12_memory.md` |
| OTel observability (otel_tracer.py) | `docs/05_agent_10_operations-and-observability.md` + `docs/05_agent_08_configuration.md` |
| Agent REPL slash commands (`CommandRegistry`) | `docs/05_agent_07_cli-and-commands.md` |
| Agent startup / verification / troubleshooting | `docs/05_agent_10_operations-and-observability.md` |
| Agent features / slash commands / tool calling | `docs/05_agent_01_system-overview.md` + `docs/05_agent_07_cli-and-commands.md` |
| Plugin tool handler / @register_tool | `docs/05_agent_11_extension-points.md` + `docs/90_shared_03_runtime_and_execution.md` |
| Agent REPL class structure | `docs/05_agent_02_runtime-architecture.md` + `docs/05_agent_12_reference-api.md` |
| Agent REPL flow / tool execution | `docs/05_agent_03_turn-processing-flow.md` + `docs/05_agent_06_tool-execution-and-approval.md` |
| AgentContext / DI hub | `docs/05_agent_02_runtime-architecture.md` + `docs/05_agent_04_state-and-persistence.md` |
| AgentConfig / config constants | `docs/05_agent_08_configuration.md` |
| Session / DB persistence | `docs/05_agent_09_data-layer.md` + `docs/90_shared_05_db_api_and_operations.md` |
| LLM client (streaming/retry) | `docs/05_agent_05_llm-and-streaming.md` |
| CLI view / readline | `docs/05_agent_07_cli-and-commands.md` |

#### MCP

| Task scope | Reference docs |
|---|---|
| MCP server implementation | `docs/04_mcp_02_protocol_and_transport.md` + `docs/04_mcp_03_routing_lifecycle_and_execution.md` |
| MCP transport / startup_mode / lifecycle | `docs/04_mcp_03_routing_lifecycle_and_execution.md` + `docs/05_agent_08_configuration.md` |
| ToolRouteResolver / route_resolver.py | `docs/04_mcp_03_routing_lifecycle_and_execution.md` + `docs/05_agent_08_configuration.md` |
| ServerLifecycleManager / lifecycle.py | `docs/04_mcp_03_routing_lifecycle_and_execution.md` + `docs/05_agent_02_runtime-architecture.md` |
| ToolSpec / tool_spec.py (execution metadata DAG) | `docs/05_agent_08_configuration.md` |
| tool_cache.py (_CacheEntry LRU cache) | `docs/05_agent_08_configuration.md` |
| TransportType / StartupMode / HealthcheckMode enums (mcp_config.py) | `docs/04_mcp_03_routing_lifecycle_and_execution.md` + `docs/04_mcp_06_configuration_and_operations.md` |
| MCP security model (allowlist / denylist / fail-closed) | `docs/04_mcp_05_security_and_safety_model.md` |
| Any MCP server (catalog only) | `docs/04_mcp_04_server_catalog.md` |
| mdq-mcp specifics | `docs/04_mcp_04_server_catalog.md` + `docs/04_mcp_90_inconsistencies_and_known_issues.md` |
| MCP known bugs / inconsistencies | `docs/04_mcp_90_inconsistencies_and_known_issues.md` |

#### RAG

| Task scope | Reference docs |
|---|---|
| RAG pipeline modification | `docs/03_rag_03_query_pipeline.md` + `docs/03_rag_04_data_model_and_interfaces.md` + `docs/90_shared_02_types_and_protocols.md` |
| RAG types / repository / LLM utils | `docs/03_rag_04_data_model_and_interfaces.md` + `docs/90_shared_02_types_and_protocols.md` |
| Ingestion pipeline run (execute commands, file lifecycle) | `docs/03_rag_02_ingestion_pipeline.md` + `docs/03_rag_05_configuration_and_operations.md` |
| crawler.py changes / API reference | `docs/03_rag_02_ingestion_pipeline.md` |
| chunk_splitter.py changes / API reference | `docs/03_rag_02_ingestion_pipeline.md` |
| ingester.py changes / API reference | `docs/03_rag_02_ingestion_pipeline.md` |
| RAG known bugs / inconsistencies | `docs/03_rag_90_inconsistencies_and_known_issues.md` |
| RAG configuration parameters | `docs/03_rag_05_configuration_and_operations.md` |

#### DB / Shared

| Task scope | Reference docs |
|---|---|
| SQLite / DB connection / WAL / transactions | `docs/90_shared_05_db_api_and_operations.md` |
| Config / logger / formatters / rag_utils | `docs/90_shared_03_runtime_and_execution.md` |
| Shared layer / DB layer known issues / inconsistencies | `docs/90_shared_90_inconsistencies_and_known_issues.md` |

#### Event Bus

| Task scope | Reference docs |
|---|---|
| Event Bus (overview) | `docs/06_eventbus_01_system-overview.md` |
| Event Bus (HTTP API) | `docs/06_eventbus_02_http_api_and_runtime.md` |
| Event Bus (persistence) | `docs/06_eventbus_03_persistence_schema_and_replay.md` |
| Event Bus (DLQ/offsets) | `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` |
| Event Bus (config/ops) | `docs/06_eventbus_05_configuration_deploy_and_operations.md` |
| Event Bus (API ref) | `docs/06_eventbus_06_reference_api.md` |
| Event Bus (issues) | `docs/06_eventbus_90_inconsistencies_and_known_issues.md` |

## Always load alongside the skill

- `rules/coding.md` — coding conventions and prohibited patterns
- `rules/toolchain.md` — validation sequence (format → lint → type → arch → security → test → coverage)

## Conditional load

Load in addition to the skill when the task involves:

- `skills/DESIGN.md` — any task that touches module boundaries, interfaces, or data models
- `rules/env.md` — service ports, DB schema, config files, or deployment

## Multiple task types

If a task spans multiple types, load the union of all required skills and docs.
