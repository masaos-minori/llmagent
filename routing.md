# routing.md

Maps task type to files that must be loaded. Read this immediately after CLAUDE.md.

## Task → file mapping

Skills in the Load column can be invoked as slash commands (e.g. `/python-implementation`) or via `Skill("python-implementation")`. The command reads `skills/*/SKILL.md` automatically.

| Task type | Keywords | Load |
|---|---|---|
| Feature / bug fix / new module | add, implement, fix, create, modify | `skills/python-implementation/SKILL.md` |
| Debug / root cause | debug, error, exception, crash, trace, log, slow, hang | `skills/python-debug-root-cause/SKILL.md` |
| Lint / type errors / CI fix | lint, ruff, mypy, pyright, type error, CI, pre-commit | `skills/python-lint-typecheck/SKILL.md` |
| Test / pytest / flaky | test, pytest, flaky, coverage, assertion, regression | `skills/python-test-and-fix/SKILL.md` |
| Refactor / rename / CST | refactor, rename, restructure, split, move, import cycle | `skills/python-refactoring/SKILL.md` |
| Plan / design / ticket | plan, design, analyze, assess, spec, ticket | `skills/python-issue-to-plan/SKILL.md` |
| MCP server / new server | mcp server, new server, install server | `skills/mcp-server-add/SKILL.md` + `rules/env.md` + `docs/04_mcp-protocol.md` + `docs/06_ref-mcp.md` |
| Deploy / production | deploy, /opt/llm, service restart, init.d | `skills/deploy/SKILL.md` + `rules/env.md` + `docs/05_agent_10_operations-and-observability.md` |

## Docs → task mapping (minimal loading)

Load only the docs relevant to the specific task. Do NOT load all docs/*.md.

### ドメイン仕様書（新構造 — 13 章形式）

| Task scope | Reference docs |
|---|---|
| エージェント仕様（全体・設計・未解決事項） | `docs/05_spec_agent.md` |
| MCP サーバー仕様（全体・設計・未解決事項） | `docs/04_spec_mcp.md` |
| RAG パイプライン仕様（全体・設計・未解決事項） | `docs/03_rag_00_document-guide.md` + `docs/03_rag_01_system_overview.md` |
| DB 層仕様（スキーマ・保守・未解決事項） | `docs/07_spec_db.md` |
| 共有インフラ仕様（設定・ログ・型・定数） | `docs/06_spec_shared.md` |

### 詳細リファレンス（実装レベルの参照用）

| Task scope | Reference docs |
|---|---|
| Memory layer (types / store / retriever / extract / jsonl_store / layer) | `docs/05_agent_04_state-and-persistence.md` + `docs/05_agent_08_configuration.md` |
| OTel observability (otel_tracer.py) | `docs/05_agent_10_operations-and-observability.md` + `docs/05_agent_08_configuration.md` |
| System-wide architecture overview | `docs/01_overview-arch.md` |
| File / module layout | `docs/01_overview-files.md` |
| MCP server implementation | `docs/04_mcp-protocol.md` + `docs/06_ref-mcp.md` |
| MCP transport / startup_mode / lifecycle | `docs/04_mcp-protocol.md` + `docs/05_agent_08_configuration.md` |
| ToolRouteResolver / route_resolver.py | `docs/05_agent_08_configuration.md` + `docs/04_mcp-protocol.md` |
| ServerLifecycleManager / lifecycle.py | `docs/04_mcp-protocol.md` + `docs/05_agent_02_runtime-architecture.md` |
| ToolSpec / tool_spec.py (execution metadata DAG) | `docs/06_ref-agent-config.md` |
| tool_cache.py (_CacheEntry LRU cache) | `docs/06_ref-agent-config.md` |
| TransportType / StartupMode / HealthcheckMode enums (mcp_config.py) | `docs/04_mcp-protocol.md` + `docs/06_ref-agent-config.md` |
| ServerLifecycleManager / lifecycle.py | `docs/04_mcp-protocol.md` + `docs/06_ref-agent-context.md` |
| web-search-mcp specifics | `docs/04_mcp-web-search.md` |
| file-mcp specifics | `docs/04_mcp-file.md` |
| github-mcp specifics | `docs/04_mcp-github.md` |
| RAG pipeline modification | `docs/03_rag_03_query_pipeline.md` + `docs/03_rag_04_data_model_and_interfaces.md` + `docs/06_shared.md` |
| rag-pipeline-mcp specifics | `docs/04_mcp-rag.md` |
| sqlite-mcp specifics | `docs/04_mcp-sqlite.md` + `docs/07_ref-sqlite.md` |
| shell-mcp specifics | `docs/04_mcp-shell.md` |
| mdq-mcp specifics | `docs/04_mcp-mdq.md` |
| cicd-mcp specifics | `docs/04_mcp-cicd.md` |
| git-mcp specifics | `docs/04_mcp-git.md` |
| Agent REPL slash commands (`CommandRegistry`) | `docs/05_agent_07_cli-and-commands.md` |
| Agent startup / verification / troubleshooting | `docs/05_agent_10_operations-and-observability.md` |
| Agent features / slash commands / tool calling | `docs/05_agent_01_system-overview.md` + `docs/05_agent_07_cli-and-commands.md` |
| Plugin tool handler / @register_tool | `docs/05_agent_11_extension-points.md` + `docs/06_shared.md` |
| Agent REPL class structure | `docs/05_agent_02_runtime-architecture.md` + `docs/05_agent_12_reference-api.md` |
| Agent REPL flow / tool execution | `docs/05_agent_03_turn-processing-flow.md` + `docs/05_agent_06_tool-execution-and-approval.md` |
| AgentContext / DI hub | `docs/05_agent_02_runtime-architecture.md` + `docs/05_agent_04_state-and-persistence.md` |
| AgentConfig / config constants | `docs/05_agent_08_configuration.md` |
| Session / DB persistence | `docs/05_agent_09_data-layer.md` + `docs/07_ref-sqlite.md` |
| LLM client (streaming/retry) | `docs/05_agent_05_llm-and-streaming.md` |
| CLI view / readline | `docs/05_agent_07_cli-and-commands.md` |
| エージェント仕様（全体・設計・未解決事項） | `docs/05_agent_00_document-guide.md` + `docs/05_agent_01_system-overview.md` |
| RAG types / repository / LLM utils | `docs/03_rag_04_data_model_and_interfaces.md` + `docs/06_shared.md` |
| SQLite / DB connection / WAL / transactions | `docs/07_ref-sqlite.md` |
| Config / logger / formatters / rag_utils | `docs/06_ref-infra.md` |
| Ingestion pipeline run (execute commands, file lifecycle) | `docs/03_rag_02_ingestion_pipeline.md` + `docs/03_rag_05_configuration_and_operations.md` |
| crawler.py changes / API reference | `docs/03_rag_02_ingestion_pipeline.md` |
| chunk_splitter.py changes / API reference | `docs/03_rag_02_ingestion_pipeline.md` |
| ingester.py changes / API reference | `docs/03_rag_02_ingestion_pipeline.md` |
| RAG known bugs / inconsistencies | `docs/03_rag_90_inconsistencies_and_known_issues.md` |
| RAG configuration parameters | `docs/03_rag_05_configuration_and_operations.md` |
| Deployment / env setup | `docs/02_deployment.md` + `rules/env.md` |

## Always load alongside the skill

- `rules/coding.md` — coding conventions and prohibited patterns
- `rules/toolchain.md` — validation sequence (format → lint → type → arch → security → test → coverage)

## Load rules/env.md only when task involves

- service ports, DB schema, config files, OpenRC services, or deployment

## Multiple task types

If a task spans multiple types, load the union of required files.
