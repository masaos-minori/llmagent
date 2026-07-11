#!/usr/bin/env python3
"""Rebuild docs/05_agent_03/04/06/08 split-output files from clean pre-split
sources. Like 09/10/11/12, these were also corrupted by the original
byte-offset split (commit d28e9fdc) — headings truncated mid-word, sections
missing entirely, and content duplicated/misplaced across output files.
This script discards those outputs and re-derives correct ones from the
recovered originals in ORIG_DIR, preserving the existing filenames.
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


def split_03() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_03_turn-processing-flow.md")
    h1 = "# Agent Turn Processing Flow"
    breadcrumb = "- Runtime architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)"

    overview = "\n".join(lines[4:86]).rstrip("\n")
    llm_tool_loop = "\n".join(lines[86:195]).rstrip("\n")
    workflow_engine = "\n".join(lines[195:]).rstrip("\n")

    related = [
        GUIDE,
        "05_agent_03_01_turn-processing-flow-overview.md",
        "05_agent_03_02_turn-processing-flow-llm-tool-loop.md",
        "05_agent_03_03_turn-processing-flow-workflow-engine.md",
    ]
    write_part(
        "05_agent_03_01_turn-processing-flow-overview.md",
        h1,
        breadcrumb,
        overview,
        "Agent Turn Processing Flow - Overview",
        ["agent", "turn", "processing", "flow", "orchestrator"],
        [r for r in related if not r.endswith("overview.md")],
        "05_agent_03_turn-processing-flow.md",
        [
            "one-turn processing flow",
            "memory injection detail",
            "history compression detail",
        ],
    )
    write_part(
        "05_agent_03_02_turn-processing-flow-llm-tool-loop.md",
        h1,
        breadcrumb,
        llm_tool_loop,
        "Agent Turn Processing Flow - LLM and Tool Loop",
        ["agent", "turn", "llm-invocation", "tool-loop", "error-handling"],
        [r for r in related if not r.endswith("llm-tool-loop.md")],
        "05_agent_03_turn-processing-flow.md",
        [
            "LLM invocation and tool loop",
            "TurnLoopState",
            "guard methods",
            "error handling",
        ],
    )
    write_part(
        "05_agent_03_03_turn-processing-flow-workflow-engine.md",
        h1,
        breadcrumb,
        workflow_engine,
        "Agent Turn Processing Flow - Workflow Engine Integration",
        ["agent", "turn", "workflow-engine", "partial-completion", "state-changes"],
        [r for r in related if not r.endswith("workflow-engine.md")],
        "05_agent_03_turn-processing-flow.md",
        [
            "partial-completion model",
            "workflowengine integration",
            "state changes per turn",
            "turn-state mutation reference",
        ],
    )


def split_04() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_04_state-and-persistence.md")
    h1 = "# Agent State and Persistence"
    breadcrumb = (
        "- Runtime architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)\n"
        "- Turn flow → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)\n"
        "- Data layer (schema) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)"
    )

    state_model = "\n".join(lines[6:155]).rstrip("\n")
    history_compression = "\n".join(lines[155:241]).rstrip("\n")
    platform_databases = "\n".join(lines[241:]).rstrip("\n")

    related = [
        GUIDE,
        "05_agent_04_01_state-and-persistence-state-model.md",
        "05_agent_04_02_state-and-persistence-history-compression.md",
        "05_agent_04_03_state-and-persistence-platform-databases.md",
    ]
    write_part(
        "05_agent_04_01_state-and-persistence-state-model.md",
        h1,
        breadcrumb,
        state_model,
        "Agent State and Persistence - State Model",
        ["agent", "state", "persistence", "agentcontext", "session"],
        [r for r in related if not r.endswith("state-model.md")],
        "05_agent_04_state-and-persistence.md",
        [
            "AgentContext state model",
            "ConversationState",
            "TurnState",
            "WorkflowState",
            "RuntimeStats",
            "session persistence",
        ],
    )
    write_part(
        "05_agent_04_02_state-and-persistence-history-compression.md",
        h1,
        breadcrumb,
        history_compression,
        "Agent State and Persistence - History Compression",
        ["agent", "state", "persistence", "history-compression", "data-classification"],
        [r for r in related if not r.endswith("history-compression.md")],
        "05_agent_04_state-and-persistence.md",
        [
            "HistoryManager compression",
            "compression trigger",
            "compression selection",
            "data classification",
        ],
    )
    write_part(
        "05_agent_04_03_state-and-persistence-platform-databases.md",
        h1,
        breadcrumb,
        platform_databases,
        "Agent State and Persistence - Platform Databases",
        ["agent", "state", "persistence", "platform-databases", "workflow-sqlite"],
        [r for r in related if not r.endswith("platform-databases.md")],
        "05_agent_04_state-and-persistence.md",
        [
            "platform databases",
            "StateStore methods",
            "task/attempt/approval/artifact operations",
            "session/RAG responsibility boundary",
        ],
    )


def split_06() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_06_tool-execution-and-approval.md")
    h1 = "# Agent Tool Execution and Approval"
    breadcrumb = (
        "- Turn flow → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)\n"
        "- MCP routing → [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md)"
    )

    execution = "\n".join(lines[5:124]).rstrip("\n")
    approval = "\n".join(lines[124:263]).rstrip("\n")
    concurrency_safety = "\n".join(lines[263:340]).rstrip("\n")
    canonical = "\n".join(lines[340:]).rstrip("\n")

    related = [
        GUIDE,
        "05_agent_06_01_tool-execution-and-approval-execution.md",
        "05_agent_06_02_tool-execution-and-approval-approval.md",
        "05_agent_06_03_tool-execution-and-approval-concurrency-safety.md",
        "05_agent_06_04_tool-execution-and-approval-canonical.md",
    ]
    write_part(
        "05_agent_06_01_tool-execution-and-approval-execution.md",
        h1,
        breadcrumb,
        execution,
        "Agent Tool Execution and Approval - Execution",
        [
            "agent",
            "tool-execution",
            "toolexecutor",
            "dag-scheduler",
            "parallel-execution",
        ],
        [r for r in related if not r.endswith("-execution.md")],
        "05_agent_06_tool-execution-and-approval.md",
        [
            "ToolExecutor",
            "parallel vs sequential execution",
            "DAG tool scheduler",
            "execute_one_tool_call",
        ],
    )
    write_part(
        "05_agent_06_02_tool-execution-and-approval-approval.md",
        h1,
        breadcrumb,
        approval,
        "Agent Tool Execution and Approval - Approval Flow",
        [
            "agent",
            "tool-execution",
            "approval-flow",
            "risk-classification",
            "plan-mode",
        ],
        [r for r in related if not r.endswith("-approval.md")],
        "05_agent_06_tool-execution-and-approval.md",
        [
            "approval flow",
            "pre-flight checks",
            "risk classification",
            "plan mode",
            "tool result cache",
        ],
    )
    write_part(
        "05_agent_06_03_tool-execution-and-approval-concurrency-safety.md",
        h1,
        breadcrumb,
        concurrency_safety,
        "Agent Tool Execution and Approval - Concurrency and Safety",
        [
            "agent",
            "tool-execution",
            "concurrency-limits",
            "fail-closed",
            "toolloopguard",
        ],
        [r for r in related if not r.endswith("concurrency-safety.md")],
        "05_agent_06_tool-execution-and-approval.md",
        [
            "safety controls summary",
            "ToolLoopGuard",
            "concurrency limits",
            "fail-closed execution policy",
            "workflow approval recovery",
        ],
    )
    write_part(
        "05_agent_06_04_tool-execution-and-approval-canonical.md",
        h1,
        breadcrumb,
        canonical,
        "Agent Tool Execution and Approval - Canonical Approval Model",
        [
            "agent",
            "tool-execution",
            "adr-001",
            "canonical-approval-model",
            "partial-completion",
        ],
        [r for r in related if not r.endswith("canonical.md")],
        "05_agent_06_tool-execution-and-approval.md",
        [
            "canonical approval model",
            "ADR-001",
            "boundary table",
            "architecture diagram",
            "partial completion persistence",
        ],
    )


def split_08() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_08_configuration.md")
    h1 = "# Agent Configuration"
    breadcrumb = "- Operations → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)"

    loading_agent_config = "\n".join(lines[4:153]).rstrip("\n")
    llm_rag = "\n".join(lines[153:201]).rstrip("\n")
    tools_memory = "\n".join(lines[201:277]).rstrip("\n")
    mcp_approval_obs = "\n".join(lines[277:]).rstrip("\n")

    related = [
        GUIDE,
        "05_agent_08_01_configuration-loading-agent-config.md",
        "05_agent_08_02_configuration-llm-rag.md",
        "05_agent_08_03_configuration-tools-memory.md",
        "05_agent_08_04_configuration-mcp-approval-obs.md",
    ]
    write_part(
        "05_agent_08_01_configuration-loading-agent-config.md",
        h1,
        breadcrumb,
        loading_agent_config,
        "Agent Configuration - Loading and AgentConfig Structure",
        ["agent", "configuration", "config-loading", "agentconfig", "hot-reload"],
        [r for r in related if not r.endswith("loading-agent-config.md")],
        "05_agent_08_configuration.md",
        [
            "configuration loading",
            "config file ownership",
            "hot-reload eligibility",
            "reload execution pipeline",
            "AgentConfig structure",
        ],
    )
    write_part(
        "05_agent_08_02_configuration-llm-rag.md",
        h1,
        breadcrumb,
        llm_rag,
        "Agent Configuration - LLMConfig and RAGConfig",
        ["agent", "configuration", "llmconfig", "ragconfig"],
        [r for r in related if not r.endswith("llm-rag.md")],
        "05_agent_08_configuration.md",
        ["LLMConfig", "RAGConfig"],
    )
    write_part(
        "05_agent_08_03_configuration-tools-memory.md",
        h1,
        breadcrumb,
        tools_memory,
        "Agent Configuration - ToolConfig and MemoryConfig",
        ["agent", "configuration", "toolconfig", "memoryconfig"],
        [r for r in related if not r.endswith("tools-memory.md")],
        "05_agent_08_configuration.md",
        ["ToolConfig", "MemoryConfig"],
    )
    write_part(
        "05_agent_08_04_configuration-mcp-approval-obs.md",
        h1,
        breadcrumb,
        mcp_approval_obs,
        "Agent Configuration - MCPConfig, ApprovalConfig, ObservabilityConfig",
        [
            "agent",
            "configuration",
            "mcpconfig",
            "approvalconfig",
            "observabilityconfig",
        ],
        [r for r in related if not r.endswith("mcp-approval-obs.md")],
        "05_agent_08_configuration.md",
        ["MCPConfig", "ApprovalConfig", "ObservabilityConfig"],
    )


def main() -> None:
    split_03()
    split_04()
    split_06()
    split_08()


if __name__ == "__main__":
    main()
