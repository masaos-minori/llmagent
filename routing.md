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
| Deploy / production | deploy, /opt/llm, service restart, init.d | `skills/deploy/SKILL.md` + `rules/env.md` + `docs/05_agent-ops.md` |

## Docs → task mapping (minimal loading)

Load only the docs relevant to the specific task. Do NOT load all docs/*.md.

| Task scope | Reference docs |
|---|---|
| Memory layer (memory_store.py / memory_layer.py) | `docs/06_ref-agent-context.md` + `docs/06_ref-agent-config.md` |
| OTel observability (otel_tracer.py) | `docs/05_agent-ops.md` + `docs/06_ref-agent-config.md` |
| System-wide architecture overview | `docs/01_overview-arch.md` |
| File / module layout | `docs/01_overview-files.md` |
| MCP server implementation | `docs/04_mcp-protocol.md` + `docs/06_ref-mcp.md` |
| MCP transport / startup_mode / lifecycle | `docs/04_mcp-protocol.md` + `docs/06_ref-agent-config.md` |
| ToolRouteResolver / route_resolver.py | `docs/06_ref-agent-config.md` + `docs/04_mcp-protocol.md` |
| ServerLifecycleManager / lifecycle.py | `docs/04_mcp-protocol.md` + `docs/06_ref-agent-context.md` |
| web-search-mcp specifics | `docs/04_mcp-web-search.md` |
| file-mcp specifics | `docs/04_mcp-file.md` |
| github-mcp specifics | `docs/04_mcp-github.md` |
| RAG pipeline modification | `docs/06_ref-rag.md` + `docs/06_common.md` |
| rag-pipeline-mcp specifics | `docs/04_mcp-rag.md` |
| Agent startup / verification / troubleshooting | `docs/05_agent-ops.md` |
| Agent features / slash commands / tool calling | `docs/05_agent.md` + `docs/06_ref-agent-commands.md` |
| Plugin tool handler / @register_tool | `docs/06_ref-agent-repl.md` + `docs/06_common.md` |
| Agent REPL class structure | `docs/05_agent-impl-class.md` + `docs/06_ref-agent-repl.md` |
| Agent REPL flow / tool execution | `docs/05_agent-impl-flow.md` + `docs/06_ref-agent-history.md` |
| AgentContext / DI hub | `docs/06_ref-agent-context.md` |
| AgentConfig / config constants | `docs/06_ref-agent-config.md` |
| Session / DB persistence | `docs/06_ref-agent-session.md` + `docs/06_ref-sqlite.md` |
| LLM client (streaming/retry) | `docs/06_ref-agent-llm.md` |
| CLI view / readline | `docs/06_ref-agent-view.md` |
| RAG types / repository / LLM utils | `docs/06_ref-rag.md` + `docs/06_common.md` |
| SQLite / DB connection / WAL / transactions | `docs/06_ref-sqlite.md` |
| Config / logger / formatters / rag_utils | `docs/06_ref-infra.md` |
| Ingestion pipeline run (execute commands, file lifecycle) | `docs/03_ingestion-run.md` |
| web_crawler.py changes / API reference | `docs/03_ref-crawler.md` |
| chunk_splitter.py changes / API reference | `docs/03_ref-splitter.md` |
| rag_ingester.py changes / API reference | `docs/03_ref-ingester.md` |
| Ingestion shared implementation notes | `docs/03_ref-ingestion.md` |
| Deployment / env setup | `docs/02_deployment.md` + `rules/env.md` |

## Always load alongside the skill

- `rules/coding.md` — shared coding conventions and prohibited behavior
- `rules/toolchain.md` — shared validation sequence

## Load rules/env.md only when task involves

- service ports, DB schema, config files, OpenRC services, or deployment

## Multiple task types

If a task spans multiple types, load the union of required files.
