# Context Loading Reference

Maps task type to files that must be loaded. Read this immediately after AGENTS.md.

## Task → skill mapping

Skills can be invoked as slash commands (e.g. `/python-implementation`) or via `Skill("python-implementation")`. The command reads `skills/*/SKILL.md` automatically.
`/skill <name> [args]` is the equivalent runtime-invocable form inside AgentREPL; `/skill` with no argument lists available skill names.

| Task type | Keywords | Load |
|---|---|---|
| Feature / bug fix / new module | add, implement, fix, create, modify | `skills/python-implementation/SKILL.md` |
| Debug / root cause | debug, error, exception, crash, trace, log, slow, hang | `skills/python-debug-root-cause/SKILL.md` |
| Lint / type errors / CI fix | lint, ruff, mypy, pyright, type error, CI, pre-commit | `skills/python-lint-typecheck/SKILL.md` |
| Test / pytest / flaky | test, pytest, flaky, coverage, assertion, regression | `skills/python-test-and-fix/SKILL.md` |
| Refactor / rename / CST | refactor, rename, restructure, split, move, import cycle | `skills/python-refactoring/SKILL.md` |
| Plan / design / ticket | plan, design, analyze, assess, spec, ticket | `skills/python-issue-to-plan/SKILL.md` + `skills/python-issue-to-plan/workflow.md` |
| Architecture / module design | architecture, module, interface, data model, component | `skills/python-design/SKILL.md` + `skills/python-design/workflow.md` |
| MCP server / new server | mcp server, new server, install server | `skills/mcp-server-add/SKILL.md` + `rules/env.md` + `docs/04_mcp_03_01_dispatch-and-routing.md` + `docs/04_mcp_06_02_configuration-file-inventory.md` |
| Deploy / production | deploy, /opt/llm, service restart, init.d | `skills/deploy/SKILL.md` + `rules/env.md` + `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` |
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
| RAG pipeline spec (overview, design, known issues) | `docs/03_rag_00_document-guide.md` + `docs/03_rag_01_system_overview-part1.md` |
| MDQ vs RAG boundary | `docs/04_mcp_05_01_access-control-and-allowlists.md` §MDQ vs RAG Boundary |
| DB layer spec (schema, ops, known issues) | `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md` + `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| Shared infra spec (config, logging, types, constants) | `docs/90_shared_00_document-guide.md` + `docs/90_shared_01_01_overview-purpose-and-scope.md` |

### Implementation reference

#### System overview

| Task scope | Reference docs |
|---|---|
| System-wide architecture overview | `docs/01_overview.md` (indexes `01_overview-arch-*.md`) |
| File / module layout | `docs/01_overview.md` (indexes `01_overview-files-*.md`) |
| `tools/` scripts overview (CI checks, doc formatting, historical doc migration) | `tools/01_overview.md` |
| Documentation set index / navigation | `docs/index.md` |
| Deployment / env setup | `docs/02_deployment-part1.md` + `rules/env.md` |

#### Agent

| Task scope | Reference docs |
|---|---|
| Memory layer (types / store / retriever / extract / jsonl_store / services.py) | `docs/05_agent_04_01_state-and-persistence-state-model-part1.md` + `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` + `docs/05_agent_12_03_memory-module-ref-core-and-store.md` + `docs/05_agent_12_04_memory-module-ref-retrieval-and-injection.md` |
| OTel observability (otel_tracer.py) | `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` + `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` |
| Agent REPL slash commands (`CommandRegistry`) | `docs/05_agent_07_01_cli-and-commands-cli-reference.md` |
| Agent startup / verification / troubleshooting | `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` |
| Agent features / slash commands / tool calling | `docs/05_agent_01_system-overview.md` + `docs/05_agent_07_01_cli-and-commands-cli-reference.md` |

| Agent REPL class structure | `docs/05_agent_02_runtime-architecture-part1.md` + `docs/05_agent_13_reference-api-part1.md` |
| Agent REPL flow / tool execution | `docs/05_agent_03_01_turn-processing-flow-overview.md` + `docs/05_agent_06_01_tool-execution-and-approval-execution.md` |
| AgentContext / DI hub | `docs/05_agent_02_runtime-architecture-part1.md` + `docs/05_agent_04_01_state-and-persistence-state-model-part1.md` |
| AgentConfig / config constants | `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` |
| Session / DB persistence | `docs/05_agent_09_01_data-layer-session-db.md` + `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| LLM client (streaming/retry) | `docs/05_agent_05_llm-and-streaming-part1.md` |
| CLI view / readline | `docs/05_agent_07_01_cli-and-commands-cli-reference.md` |

#### MCP

| Task scope | Reference docs |
|---|---|
| MCP server implementation | `docs/04_mcp_02_01_endpoints-and-transport.md` + `docs/04_mcp_03_01_dispatch-and-routing.md` |
| MCP transport / startup_mode / lifecycle | `docs/04_mcp_03_01_dispatch-and-routing.md` + `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` |
| ToolRouteResolver / route_resolver.py | `docs/04_mcp_03_01_dispatch-and-routing.md` + `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` |
| ServerLifecycleManager / lifecycle.py | `docs/04_mcp_03_01_dispatch-and-routing.md` + `docs/05_agent_02_runtime-architecture-part1.md` |
| ToolSpec / tool_spec.py (execution metadata DAG) | `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` |
| tool_cache.py (_CacheEntry LRU cache) | `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` |
| TransportType / StartupMode / HealthcheckMode enums (mcp_config.py) | `docs/04_mcp_03_01_dispatch-and-routing.md` + `docs/04_mcp_06_02_configuration-file-inventory.md` |
| MCP security model (allowlist / denylist / fail-closed) | `docs/04_mcp_05_01_access-control-and-allowlists.md` |
| Any MCP server (catalog only) | `docs/04_mcp_04_01_web-search-file-read-github.md` |
| mdq-mcp specifics | `docs/04_mcp_04_04_mdq.md` + `docs/04_mcp_90_inconsistencies_and_known_issues.md` |
| MCP known bugs / inconsistencies | `docs/04_mcp_90_inconsistencies_and_known_issues.md` |

#### RAG

| Task scope | Reference docs |
|---|---|
| RAG pipeline modification | `docs/03_rag_03_01_query_pipeline-overview.md` + `docs/03_rag_04_05_dto-types.md` + `docs/90_shared_02_01_types_and_protocols-core-types.md` |
| RAG types / repository / LLM utils | `docs/03_rag_04_05_dto-types.md` + `docs/90_shared_02_01_types_and_protocols-core-types.md` |
| Ingestion pipeline run (execute commands, file lifecycle) | `docs/03_rag_02_01_ingestion_pipeline-overview.md` + `docs/03_rag_05_1-configuration-reference.md` |
| crawler.py changes / API reference | `docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md` |
| chunk_splitter.py changes / API reference | `docs/03_rag_02_03_ingestion_pipeline-chunksplitter-part1.md` |
| ingester.py changes / API reference | `docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md` |
| RAG known bugs / inconsistencies | `docs/03_rag_90_inconsistencies_and_known_issues-part1.md` |
| RAG configuration parameters | `docs/03_rag_05_1-configuration-reference.md` |

#### DB / Shared

| Task scope | Reference docs |
|---|---|
| SQLite / DB connection / WAL / transactions | `docs/90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| Config / logger / formatters / rag_utils | `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` |
| Shared layer / DB layer known issues / inconsistencies | `docs/90_shared_90_inconsistencies_and_known_issues.md` |

#### Event Bus

| Task scope | Reference docs |
|---|---|
| Event Bus (overview) | `docs/06_eventbus_01_system-overview.md` |
| Event Bus (HTTP API) | `docs/06_eventbus_02_01_publish-replay.md` |
| Event Bus (persistence) | `docs/06_eventbus_03_persistence_schema_and_replay.md` |
| Event Bus (DLQ/offsets) | `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` |
| Event Bus (config/ops) | `docs/06_eventbus_05_01_config-env-and-fields.md` |
| Event Bus (API ref) | `docs/06_eventbus_06_01_reference-api-core-modules.md` |
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
