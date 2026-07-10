#!/usr/bin/env python3
"""Split oversized 90_shared_01/02/03/04/05 docs at H2 boundaries into <=8KB files.

Reads clean pre-split source text from ORIG_DIR (01/04/05, recovered from git
history at commit 7a3781e9^) and from docs/ (02/03, still present unsplit),
then writes normalized split-output files with Front Matter and tail sections.
"""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
ORIG_DIR = Path(
    "/tmp/claude-1000/-home-masaos-llmagent/b00aee41-8a47-47c2-b169-36bf16dfa55a/scratchpad/orig"
)

GUIDE = "90_shared_00_document-guide.md"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split("\n")


def front_matter(title: str, tags: list[str], related: list[str], source: str) -> str:
    tag_lines = "\n".join(f"  - {t}" for t in tags)
    related_lines = "\n".join(f"  - {r}" for r in related)
    return (
        "---\n"
        f'title: "{title}"\n'
        "category: shared\n"
        "tags:\n"
        f"{tag_lines}\n"
        "related:\n"
        f"{related_lines}\n"
        "source:\n"
        f"  - {source}\n"
        "---\n\n"
    )


def tail(related: list[str], keywords: list[str]) -> str:
    related_lines = "\n".join(f"- `{r}`" for r in related)
    keyword_lines = "\n".join(keywords)
    return f"\n\n## Related Documents\n\n{related_lines}\n\n## Keywords\n\n{keyword_lines}\n"


def write_part(
    filename: str,
    h1: str,
    breadcrumb: str,
    body: str,
    title: str,
    tags: list[str],
    related: list[str],
    source: str,
    keywords: list[str],
) -> None:
    content = (
        front_matter(title, tags, related, source)
        + f"{h1}\n\n{breadcrumb}\n\n"
        + body
        + tail(related, keywords)
    )
    path = DOCS_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"wrote {filename} ({len(content.encode('utf-8'))}B)")


def split_01() -> None:
    lines = read_lines(ORIG_DIR / "90_shared_01_overview.md")
    h1 = "# Shared and DB Layer Overview"
    breadcrumb = f"- Document guide → [{GUIDE}]({GUIDE})"

    purpose_scope = "\n".join(lines[4:40]).rstrip("\n")
    layer_resp = "\n".join(lines[40:127]).rstrip("\n")
    constraints_ref = "\n".join(lines[127:]).rstrip("\n")

    write_part(
        "90_shared_01_overview-purpose-and-scope.md",
        h1,
        breadcrumb,
        purpose_scope,
        "Shared and DB Layer Overview - Purpose and Scope",
        ["shared", "overview", "purpose", "scope", "out-of-scope"],
        [
            GUIDE,
            "90_shared_01_overview-layer-responsibilities.md",
            "90_shared_01_overview-constraints-and-reference.md",
        ],
        "90_shared_01_overview.md",
        ["shared", "purpose", "scope", "out of scope", "layer overview"],
    )
    write_part(
        "90_shared_01_overview-layer-responsibilities.md",
        h1,
        breadcrumb,
        layer_resp,
        "Shared and DB Layer Overview - Layer Responsibilities",
        ["shared", "db", "layer-structure", "responsibilities", "architecture"],
        [
            GUIDE,
            "90_shared_01_overview-purpose-and-scope.md",
            "90_shared_01_overview-constraints-and-reference.md",
        ],
        "90_shared_01_overview.md",
        ["shared", "db", "layer structure", "responsibilities", "architecture"],
    )
    write_part(
        "90_shared_01_overview-constraints-and-reference.md",
        h1,
        breadcrumb,
        constraints_ref,
        "Shared and DB Layer Overview - Constraints and Reference",
        [
            "shared",
            "db",
            "import-direction",
            "constraints",
            "executive-summary",
            "ai-reference",
        ],
        [
            GUIDE,
            "90_shared_01_overview-purpose-and-scope.md",
            "90_shared_01_overview-layer-responsibilities.md",
        ],
        "90_shared_01_overview.md",
        [
            "import direction",
            "constraints",
            "persistent data",
            "executive summary",
            "ai reference guide",
        ],
    )


def split_02() -> None:
    lines = read_lines(ORIG_DIR / "90_shared_02_types_and_protocols.md")
    h1 = "# Shared Types and Protocols"
    breadcrumb = "- Overview → [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md)"

    core_types = "\n".join(lines[4:134]).rstrip("\n")
    tool_dto = "\n".join(lines[134:345]).rstrip("\n")
    reference = "\n".join(lines[345:]).rstrip("\n")

    related = [
        GUIDE,
        "90_shared_02_types_and_protocols-core-types.md",
        "90_shared_02_types_and_protocols-tool-and-execution-dto.md",
        "90_shared_02_types_and_protocols-reference.md",
    ]
    write_part(
        "90_shared_02_types_and_protocols-core-types.md",
        h1,
        breadcrumb,
        core_types,
        "Shared Types and Protocols - Core Types",
        ["shared", "types", "protocols", "llmmessage", "ragconfig", "hit-types"],
        [r for r in related if not r.endswith("core-types.md")],
        "90_shared_02_types_and_protocols.md",
        [
            "types",
            "protocols",
            "LLMMessage",
            "RagConfig",
            "RawHit",
            "MergedHit",
            "RankedHit",
            "RagHit",
        ],
    )
    write_part(
        "90_shared_02_types_and_protocols-tool-and-execution-dto.md",
        h1,
        breadcrumb,
        tool_dto,
        "Shared Types and Protocols - Tool and Execution DTOs",
        [
            "shared",
            "types",
            "tool-dto",
            "action-result",
            "tool-spec",
            "cache",
            "events",
        ],
        [r for r in related if not r.endswith("tool-and-execution-dto.md")],
        "90_shared_02_types_and_protocols.md",
        [
            "ToolCallResult",
            "ActionResult",
            "ToolSpec",
            "CacheEntry",
            "PluginFailure",
            "ToolDefinition",
            "ArtifactEvent",
            "ShellPolicy",
            "DbConfig",
        ],
    )
    write_part(
        "90_shared_02_types_and_protocols-reference.md",
        h1,
        breadcrumb,
        reference,
        "Shared Types and Protocols - Reference",
        ["shared", "types", "tool-constants", "call-tool", "protocol-vs-dataclass"],
        [r for r in related if not r.endswith("-reference.md")],
        "90_shared_02_types_and_protocols.md",
        [
            "tool constants",
            "CallToolRequest",
            "CallToolResponse",
            "Protocol",
            "TypedDict",
            "dataclass",
            "DTO",
        ],
    )


def split_03() -> None:
    lines = read_lines(ORIG_DIR / "90_shared_03_runtime_and_execution.md")
    h1 = "# Shared Runtime and Execution Infrastructure"
    breadcrumb = "- Overview → [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md)"

    config_logging = "\n".join(lines[4:116]).rstrip("\n")
    plugin_tool = "\n".join(lines[116:251]).rstrip("\n")
    llm_mcp = "\n".join(lines[251:396]).rstrip("\n")
    caching_ref = "\n".join(lines[396:]).rstrip("\n")

    related = [
        GUIDE,
        "90_shared_03_runtime_and_execution-config-and-logging.md",
        "90_shared_03_runtime_and_execution-plugin-and-tool-runtime.md",
        "90_shared_03_runtime_and_execution-llm-and-mcp-clients.md",
        "90_shared_03_runtime_and_execution-caching-and-reference.md",
    ]
    write_part(
        "90_shared_03_runtime_and_execution-config-and-logging.md",
        h1,
        breadcrumb,
        config_logging,
        "Shared Runtime and Execution - Config and Logging",
        ["shared", "runtime", "config-loader", "config-isolation", "logger"],
        [r for r in related if not r.endswith("config-and-logging.md")],
        "90_shared_03_runtime_and_execution.md",
        ["ConfigLoader", "config isolation policy", "Logger", "runtime"],
    )
    write_part(
        "90_shared_03_runtime_and_execution-plugin-and-tool-runtime.md",
        h1,
        breadcrumb,
        plugin_tool,
        "Shared Runtime and Execution - Plugin and Tool Runtime",
        [
            "shared",
            "runtime",
            "plugin-registry",
            "token-counter",
            "otel-tracer",
            "git-helper",
            "tool-executor",
        ],
        [r for r in related if not r.endswith("plugin-and-tool-runtime.md")],
        "90_shared_03_runtime_and_execution.md",
        [
            "plugin_registry",
            "token_counter",
            "otel_tracer",
            "git_helper",
            "formatters",
            "ToolExecutor",
        ],
    )
    write_part(
        "90_shared_03_runtime_and_execution-llm-and-mcp-clients.md",
        h1,
        breadcrumb,
        llm_mcp,
        "Shared Runtime and Execution - LLM and MCP Clients",
        ["shared", "runtime", "llm-client", "mcp-server-config", "execution-flow"],
        [r for r in related if not r.endswith("llm-and-mcp-clients.md")],
        "90_shared_03_runtime_and_execution.md",
        [
            "LLMClient",
            "McpServerConfig",
            "McpServerHealthRegistry",
            "execution flow summary",
            "import boundaries",
        ],
    )
    write_part(
        "90_shared_03_runtime_and_execution-caching-and-reference.md",
        h1,
        breadcrumb,
        caching_ref,
        "Shared Runtime and Execution - Caching and Reference",
        [
            "shared",
            "runtime",
            "retry-handler",
            "tool-cache",
            "tool-spec",
            "plugin-invoker",
            "ai-reference",
        ],
        [r for r in related if not r.endswith("caching-and-reference.md")],
        "90_shared_03_runtime_and_execution.md",
        [
            "LlmRetryHandler",
            "ToolResultCache",
            "CacheEntry",
            "ToolSpec",
            "PluginToolInvoker",
            "McpServerHealthState",
            "LlmPayloadHandler",
            "LlmHotConfigHandler",
        ],
    )


def split_04() -> None:
    lines = read_lines(ORIG_DIR / "90_shared_04_db_architecture_and_schema.md")
    h1 = "# DB Architecture and Schema"
    breadcrumb = (
        "- Overview → [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md)\n"
        "- DB API → [90_shared_05_db_api_and_operations-module-boundaries-and-helper.md]"
        "(90_shared_05_db_api_and_operations-module-boundaries-and-helper.md)"
    )

    overview_config = "\n".join(lines[5:91]).rstrip("\n")
    schema_ref = "\n".join(lines[91:293]).rstrip("\n")
    migration_scaling = "\n".join(lines[293:]).rstrip("\n")

    related = [
        GUIDE,
        "90_shared_04_db_architecture_and_schema-overview-and-config.md",
        "90_shared_04_db_architecture_and_schema-schema-reference.md",
        "90_shared_04_db_architecture_and_schema-migration-and-scaling.md",
    ]
    write_part(
        "90_shared_04_db_architecture_and_schema-overview-and-config.md",
        h1,
        breadcrumb,
        overview_config,
        "DB Architecture and Schema - Overview and Config",
        ["shared", "db", "dbconfig", "sqlitehelper", "layer-structure"],
        [r for r in related if not r.endswith("overview-and-config.md")],
        "90_shared_04_db_architecture_and_schema.md",
        ["DbConfig", "SQLiteHelper", "DB layer structure", "DB file structure"],
    )
    write_part(
        "90_shared_04_db_architecture_and_schema-schema-reference.md",
        h1,
        breadcrumb,
        schema_ref,
        "DB Architecture and Schema - Schema Reference",
        [
            "shared",
            "db",
            "rag-sqlite",
            "session-sqlite",
            "workflow-sqlite",
            "timestamp-policy",
        ],
        [r for r in related if not r.endswith("schema-reference.md")],
        "90_shared_04_db_architecture_and_schema.md",
        [
            "rag.sqlite",
            "session.sqlite",
            "workflow.sqlite",
            "schema",
            "timestamp format policy",
        ],
    )
    write_part(
        "90_shared_04_db_architecture_and_schema-migration-and-scaling.md",
        h1,
        breadcrumb,
        migration_scaling,
        "DB Architecture and Schema - Migration and Scaling",
        ["shared", "db", "migration", "constraints", "scaling-limits", "ai-reference"],
        [r for r in related if not r.endswith("migration-and-scaling.md")],
        "90_shared_04_db_architecture_and_schema.md",
        [
            "schema generation",
            "migration approach",
            "constraint list",
            "source of truth",
            "scaling limits",
        ],
    )


def split_05() -> None:
    lines = read_lines(ORIG_DIR / "90_shared_05_db_api_and_operations.md")
    h1 = "# DB API and Operations"
    breadcrumb = (
        "- Schema → [90_shared_04_db_architecture_and_schema-overview-and-config.md]"
        "(90_shared_04_db_architecture_and_schema-overview-and-config.md)"
    )

    module_helper = "\n".join(lines[4:116]).rstrip("\n")
    protocol_backend = "\n".join(lines[116:242]).rstrip("\n")
    maintenance_rotation = "\n".join(lines[242:400]).rstrip("\n")
    recovery_ref = "\n".join(lines[400:]).rstrip("\n")

    related = [
        GUIDE,
        "90_shared_05_db_api_and_operations-module-boundaries-and-helper.md",
        "90_shared_05_db_api_and_operations-protocol-and-backend.md",
        "90_shared_05_db_api_and_operations-maintenance-and-rotation.md",
        "90_shared_05_db_api_and_operations-recovery-and-reference.md",
    ]
    write_part(
        "90_shared_05_db_api_and_operations-module-boundaries-and-helper.md",
        h1,
        breadcrumb,
        module_helper,
        "DB API and Operations - Module Boundaries and Helper",
        ["shared", "db", "sqlitehelper", "module-boundaries", "store-protocols"],
        [r for r in related if not r.endswith("module-boundaries-and-helper.md")],
        "90_shared_05_db_api_and_operations.md",
        ["DB store module boundaries", "SQLiteHelper", "db/helper.py"],
    )
    write_part(
        "90_shared_05_db_api_and_operations-protocol-and-backend.md",
        h1,
        breadcrumb,
        protocol_backend,
        "DB API and Operations - Protocol and Backend",
        ["shared", "db", "protocol-groups", "sqlite-backend", "memory-store"],
        [r for r in related if not r.endswith("protocol-and-backend.md")],
        "90_shared_05_db_api_and_operations.md",
        [
            "protocol groups",
            "db/store.py",
            "SQLite backend implementations",
            "MemoryStore",
        ],
    )
    write_part(
        "90_shared_05_db_api_and_operations-maintenance-and-rotation.md",
        h1,
        breadcrumb,
        maintenance_rotation,
        "DB API and Operations - Maintenance and Rotation",
        ["shared", "db", "maintenance", "rotation", "rag-consistency"],
        [r for r in related if not r.endswith("maintenance-and-rotation.md")],
        "90_shared_05_db_api_and_operations.md",
        [
            "maintenance functions",
            "db/maintenance.py",
            "db rotation",
            "RAG consistency checks",
        ],
    )
    write_part(
        "90_shared_05_db_api_and_operations-recovery-and-reference.md",
        h1,
        breadcrumb,
        recovery_ref,
        "DB API and Operations - Recovery and Reference",
        [
            "shared",
            "db",
            "corruption-recovery",
            "error-handling",
            "verification",
            "ai-reference",
        ],
        [r for r in related if not r.endswith("recovery-and-reference.md")],
        "90_shared_05_db_api_and_operations.md",
        [
            "corruption recovery",
            "error handling",
            "DB recreation procedure",
            "verification plan",
            "ai reference guide",
        ],
    )


def main() -> None:
    split_01()
    split_02()
    split_03()
    split_04()
    split_05()


if __name__ == "__main__":
    main()
