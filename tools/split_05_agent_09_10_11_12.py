#!/usr/bin/env python3
"""Rebuild docs/05_agent_09/10/11/12 split-output files from clean pre-split
sources. The previous split (commit d28e9fdc) cut files at arbitrary byte
offsets instead of heading boundaries, corrupting headings and paragraph
starts across most output files. This script discards those outputs and
re-derives correct ones from the recovered originals in ORIG_DIR.
"""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
ORIG_DIR = Path(
    "/tmp/claude-1000/-home-masaos-llmagent/b00aee41-8a47-47c2-b169-36bf16dfa55a/scratchpad/orig"
)

GUIDE = "05_agent_00_document-guide.md"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split("\n")


def front_matter(title: str, tags: list[str], related: list[str], source: str) -> str:
    tag_lines = "\n".join(f"  - {t}" for t in tags)
    related_lines = "\n".join(f"  - {r}" for r in related)
    return (
        "---\n"
        f'title: "{title}"\n'
        "category: agent\n"
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


def split_09() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_09_data-layer.md")
    h1 = "# Agent Data Layer"
    breadcrumb = "- State and persistence → [05_agent_04_state-and-persistence-state-model.md](05_agent_04_state-and-persistence-state-model.md)"

    session_db = "\n".join(lines[4:95]).rstrip("\n")
    access_patterns = "\n".join(lines[95:186]).rstrip("\n")
    indexing_boundaries = "\n".join(lines[186:]).rstrip("\n")

    related = [
        GUIDE,
        "05_agent_09_data-layer-session-db.md",
        "05_agent_09_data-layer-access-patterns.md",
        "05_agent_09_data-layer-indexing-boundaries.md",
    ]
    write_part(
        "05_agent_09_data-layer-session-db.md",
        h1,
        breadcrumb,
        session_db,
        "Agent Data Layer - Session DB",
        ["agent", "data-layer", "session-sqlite", "rag-sqlite", "sqlite-databases"],
        [r for r in related if not r.endswith("session-db.md")],
        "05_agent_09_data-layer.md",
        [
            "session.sqlite",
            "sessions table",
            "messages table",
            "session_diagnostics",
            "rag.sqlite",
        ],
    )
    write_part(
        "05_agent_09_data-layer-access-patterns.md",
        h1,
        breadcrumb,
        access_patterns,
        "Agent Data Layer - Access Patterns",
        ["agent", "data-layer", "rag-mcp", "document-access", "memory-tables"],
        [r for r in related if not r.endswith("access-patterns.md")],
        "05_agent_09_data-layer.md",
        [
            "RAG MCP internal path",
            "document access patterns",
            "memory tables",
            "context manager pattern",
        ],
    )
    write_part(
        "05_agent_09_data-layer-indexing-boundaries.md",
        h1,
        breadcrumb,
        indexing_boundaries,
        "Agent Data Layer - Indexing and Boundaries",
        ["agent", "data-layer", "fts5", "workflow-sqlite", "persistence-boundaries"],
        [r for r in related if not r.endswith("indexing-boundaries.md")],
        "05_agent_09_data-layer.md",
        [
            "FTS5 index",
            "chunks_fts",
            "workflow.sqlite",
            "non-message persistence boundaries",
        ],
    )


def split_10() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_10_operations-and-observability.md")
    h1 = "# Agent Operations and Observability"
    breadcrumb = "- Configuration → [05_agent_08_configuration-mcp-approval-obs.md](05_agent_08_configuration-mcp-approval-obs.md)"

    startup_and_health = "\n".join(lines[4:149]).rstrip("\n")
    audit_and_otel = "\n".join(lines[149:268]).rstrip("\n")
    workflow_observability = "\n".join(lines[268:396]).rstrip("\n")
    validation_and_troubleshooting = "\n".join(lines[396:495]).rstrip("\n")
    monitoring = "\n".join(lines[495:590]).rstrip("\n")
    rag_diagnostics_and_memory = "\n".join(lines[590:]).rstrip("\n")

    related = [
        GUIDE,
        "05_agent_10_operations-and-observability-startup-and-health.md",
        "05_agent_10_operations-and-observability-audit-and-otel.md",
        "05_agent_10_operations-and-observability-workflow-observability.md",
        "05_agent_10_operations-and-observability-validation-and-troubleshooting.md",
        "05_agent_10_operations-and-observability-monitoring.md",
        "05_agent_10_operations-and-observability-rag-diagnostics-and-memory.md",
    ]
    write_part(
        "05_agent_10_operations-and-observability-startup-and-health.md",
        h1,
        breadcrumb,
        startup_and_health,
        "Agent Operations and Observability - Startup and Health",
        ["agent", "operations", "startup", "health-probes", "operational-verification"],
        [r for r in related if not r.endswith("startup-and-health.md")],
        "05_agent_10_operations-and-observability.md",
        [
            "startup procedure",
            "operational verification",
            "health probes",
            "minimal agent db initialization",
        ],
    )
    write_part(
        "05_agent_10_operations-and-observability-audit-and-otel.md",
        h1,
        breadcrumb,
        audit_and_otel,
        "Agent Operations and Observability - Audit Log and OTel",
        ["agent", "operations", "audit-log", "otel", "observability"],
        [r for r in related if not r.endswith("audit-and-otel.md")],
        "05_agent_10_operations-and-observability.md",
        [
            "audit log",
            "reading audit logs",
            "audit event dtos",
            "audit writers",
            "OpenTelemetry",
        ],
    )
    write_part(
        "05_agent_10_operations-and-observability-workflow-observability.md",
        h1,
        breadcrumb,
        workflow_observability,
        "Agent Operations and Observability - Workflow Observability",
        ["agent", "operations", "workflow", "otel-spans", "session-diagnostics"],
        [r for r in related if not r.endswith("workflow-observability.md")],
        "05_agent_10_operations-and-observability.md",
        ["OTel spans", "workflow identifiers", "audit events", "session diagnostics"],
    )
    write_part(
        "05_agent_10_operations-and-observability-validation-and-troubleshooting.md",
        h1,
        breadcrumb,
        validation_and_troubleshooting,
        "Agent Operations and Observability - Validation and Troubleshooting",
        ["agent", "operations", "startup-validation", "mcp-reload", "troubleshooting"],
        [r for r in related if not r.endswith("validation-and-troubleshooting.md")],
        "05_agent_10_operations-and-observability.md",
        [
            "workflow startup validation",
            "MCP server reload",
            "/context",
            "/stats",
            "partial completion",
            "troubleshooting",
        ],
    )
    write_part(
        "05_agent_10_operations-and-observability-monitoring.md",
        h1,
        breadcrumb,
        monitoring,
        "Agent Operations and Observability - Runtime Diagnostics",
        ["agent", "operations", "runtime-diagnostics", "session-end-summary"],
        [r for r in related if not r.endswith("-monitoring.md")],
        "05_agent_10_operations-and-observability.md",
        ["runtime diagnostics", "session-end summary", "diagnostic events"],
    )
    write_part(
        "05_agent_10_operations-and-observability-rag-diagnostics-and-memory.md",
        h1,
        breadcrumb,
        rag_diagnostics_and_memory,
        "Agent Operations and Observability - RAG Diagnostics and Memory",
        [
            "agent",
            "operations",
            "rag-diagnostics",
            "memory-status",
            "graceful-shutdown",
        ],
        [r for r in related if not r.endswith("rag-diagnostics-and-memory.md")],
        "05_agent_10_operations-and-observability.md",
        [
            "RAG pipeline diagnostics",
            "stage result interpretation",
            "memory status",
            "graceful shutdown",
        ],
    )


def split_11() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_11_extension-points.md")
    h1 = "# Agent Extension Points"
    breadcrumb = "- Runtime architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)"

    plugin_command = "\n".join(lines[4:84]).rstrip("\n")
    tool_registration = "\n".join(lines[84:207]).rstrip("\n")
    registry_rules = "\n".join(lines[207:]).rstrip("\n")

    related = [
        GUIDE,
        "05_agent_11_extension-points-plugin-command.md",
        "05_agent_11_extension-points-tool-registration.md",
        "05_agent_11_extension-points-registry-rules.md",
    ]
    write_part(
        "05_agent_11_extension-points-plugin-command.md",
        h1,
        breadcrumb,
        plugin_command,
        "Agent Extension Points - Plugin Architecture and Commands",
        ["agent", "extension-points", "plugin-architecture", "register-command"],
        [r for r in related if not r.endswith("plugin-command.md")],
        "05_agent_11_extension-points.md",
        ["plugin architecture", "@register_command", "command shadow policy"],
    )
    write_part(
        "05_agent_11_extension-points-tool-registration.md",
        h1,
        breadcrumb,
        tool_registration,
        "Agent Extension Points - Tool Registration",
        ["agent", "extension-points", "register-tool", "pipeline-stage"],
        [r for r in related if not r.endswith("tool-registration.md")],
        "05_agent_11_extension-points.md",
        [
            "@register_tool",
            "plugin tool precedence",
            "conflict detection",
            "safety tier enforcement",
            "@register_pipeline_stage",
        ],
    )
    write_part(
        "05_agent_11_extension-points-registry-rules.md",
        h1,
        breadcrumb,
        registry_rules,
        "Agent Extension Points - Registry API and Rules",
        [
            "agent",
            "extension-points",
            "plugin-registry",
            "extension-rules",
            "mcp-server",
        ],
        [r for r in related if not r.endswith("registry-rules.md")],
        "05_agent_11_extension-points.md",
        [
            "Registry API",
            "test isolation",
            "extension rules",
            "hook failure behavior",
            "adding a new MCP server",
        ],
    )


def split_12() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_12_memory.md")
    h1 = "# Memory Layer — Module Reference"
    breadcrumb = (
        "- Operations and observability → [05_agent_10_operations-and-observability-startup-and-health.md]"
        "(05_agent_10_operations-and-observability-startup-and-health.md)\n"
        "- Configuration → [05_agent_08_configuration-tools-memory.md](05_agent_08_configuration-tools-memory.md)"
    )

    overview_and_modes = "\n".join(lines[5:160]).rstrip("\n")
    gate_data_model_search = (
        "\n".join(lines[160:284]).rstrip("\n")
        + "\n\n"
        + "\n".join(lines[612:623]).rstrip("\n")
    )
    core_and_store = "\n".join(lines[286:369]).rstrip("\n")
    retrieval_and_injection = "\n".join(lines[369:466]).rstrip("\n")
    extraction_and_facade = "\n".join(lines[466:531]).rstrip("\n")
    ops_and_scoring = "\n".join(lines[531:612]).rstrip("\n")

    related = [
        GUIDE,
        "05_agent_12_memory-overview-and-modes.md",
        "05_agent_12_memory-gate-data-model-search.md",
        "05_agent_12_memory-module-ref-core-and-store.md",
        "05_agent_12_memory-module-ref-retrieval-and-injection.md",
        "05_agent_12_memory-module-ref-extraction-and-facade.md",
        "05_agent_12_memory-module-ref-ops-and-scoring.md",
    ]
    write_part(
        "05_agent_12_memory-overview-and-modes.md",
        h1,
        breadcrumb,
        overview_and_modes,
        "Memory Layer - Overview and Modes",
        ["agent", "memory", "overview", "memory-modes", "production-checklist"],
        [r for r in related if not r.endswith("overview-and-modes.md")],
        "05_agent_12_memory.md",
        [
            "persistent semantic memory",
            "production checklist",
            "purpose",
            "memory modes",
        ],
    )
    write_part(
        "05_agent_12_memory-gate-data-model-search.md",
        h1,
        breadcrumb,
        gate_data_model_search,
        "Memory Layer - Activation Gate, Data Model, and Search",
        [
            "agent",
            "memory",
            "activation-gate",
            "data-model",
            "search-strategies",
            "disabled-behavior",
        ],
        [r for r in related if not r.endswith("gate-data-model-search.md")],
        "05_agent_12_memory.md",
        [
            "activation gate",
            "disabled behavior by module",
            "MemoryEntry",
            "MemorySnippet",
            "JSONL format",
            "FTS5",
            "KNN",
            "hybrid RRF",
            "disabled behavior",
        ],
    )
    write_part(
        "05_agent_12_memory-module-ref-core-and-store.md",
        h1,
        breadcrumb,
        core_and_store,
        "Memory Layer - Module Reference: Core and Store",
        ["agent", "memory", "module-reference", "types", "store"],
        [r for r in related if not r.endswith("core-and-store.md")],
        "05_agent_12_memory.md",
        [
            "__init__.py",
            "types.py",
            "enums.py",
            "exceptions.py",
            "models.py",
            "store.py",
        ],
    )
    write_part(
        "05_agent_12_memory-module-ref-retrieval-and-injection.md",
        h1,
        breadcrumb,
        retrieval_and_injection,
        "Memory Layer - Module Reference: Retrieval and Injection",
        ["agent", "memory", "module-reference", "retriever", "injection", "ingestion"],
        [r for r in related if not r.endswith("retrieval-and-injection.md")],
        "05_agent_12_memory.md",
        ["retriever.py", "injection.py", "ingestion.py"],
    )
    write_part(
        "05_agent_12_memory-module-ref-extraction-and-facade.md",
        h1,
        breadcrumb,
        extraction_and_facade,
        "Memory Layer - Module Reference: Extraction and Facade",
        [
            "agent",
            "memory",
            "module-reference",
            "extract",
            "jsonl-store",
            "embedding-client",
            "services",
        ],
        [r for r in related if not r.endswith("extraction-and-facade.md")],
        "05_agent_12_memory.md",
        ["extract.py", "jsonl_store.py", "embedding_client.py", "services.py"],
    )
    write_part(
        "05_agent_12_memory-module-ref-ops-and-scoring.md",
        h1,
        breadcrumb,
        ops_and_scoring,
        "Memory Layer - Module Reference: Ops and Scoring",
        ["agent", "memory", "module-reference", "write-ops", "scoring", "rrf"],
        [r for r in related if not r.endswith("ops-and-scoring.md")],
        "05_agent_12_memory.md",
        [
            "mapper.py",
            "write_ops.py",
            "pin_ops.py",
            "count_ops.py",
            "rebuild_ops.py",
            "import_ops.py",
            "scoring.py",
            "rrf.py",
            "fts_query.py",
            "sql_constants.py",
        ],
    )


def main() -> None:
    split_09()
    split_10()
    split_11()
    split_12()


if __name__ == "__main__":
    main()
