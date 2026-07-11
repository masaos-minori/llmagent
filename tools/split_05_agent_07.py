#!/usr/bin/env python3
"""Rebuild docs/05_agent_07_*.md (11 files) from the clean pre-split source.
The original split (commit d28e9fdc) scattered/duplicated/lost sections across
these 11 files (e.g. CLIView content appeared in two files, CommandRegistry in
two files, Migration Notes was empty and unrelated content duplicated into it,
Approval/Safety sections vanished). This rebuilds all 11 files cleanly.

07_01 (cli-reference) has no dedicated section in the original source — it is
synthesized here as a short chapter-local index pointing at the other 10 files,
since the original content for CLIView/CommandRegistry/Purpose/REPL I/O maps
1:1 onto files 02/03/04/05 instead.
"""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
ORIG_DIR = Path(
    "/tmp/claude-1000/-home-masaos-llmagent/b00aee41-8a47-47c2-b169-36bf16dfa55a/scratchpad/orig"
)

GUIDE = "05_agent_00_document-guide.md"
H1 = "# Agent CLI and Commands"
BREADCRUMB = "- System overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)"


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
    body: str,
    title: str,
    tags: list[str],
    related: list[str],
    source: str,
    keywords: list[str],
) -> None:
    content = (
        front_matter(title, tags, related, source)
        + f"{H1}\n\n{BREADCRUMB}\n\n"
        + body
        + tail(related, keywords)
    )
    path = DOCS_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"wrote {filename} ({len(content.encode('utf-8'))}B)")


def main() -> None:
    lines = read_lines(ORIG_DIR / "05_agent_07_cli-and-commands.md")

    purpose = "\n".join(lines[4:11]).rstrip("\n")
    repl_io = "\n".join(lines[11:22]).rstrip("\n")
    cliview = "\n".join(lines[22:55]).rstrip("\n")
    command_registry = "\n".join(lines[55:78]).rstrip("\n")
    slash_session_mcp = "\n".join(lines[78:116]).rstrip("\n")
    slash_context_db = "\n".join(lines[116:158]).rstrip("\n")
    slash_workflow_debug = "\n".join(lines[158:202]).rstrip("\n")
    slash_memory_other = "\n".join(lines[202:245]).rstrip("\n")
    hot_reload = "\n".join(lines[245:284]).rstrip("\n")
    migration_notes = "\n".join(lines[284:]).rstrip("\n")

    all_files = [
        "05_agent_07_01_cli-and-commands-cli-reference.md",
        "05_agent_07_02_cli-and-commands-cliview.md",
        "05_agent_07_03_cli-and-commands-command-registry.md",
        "05_agent_07_04_cli-and-commands-purpose.md",
        "05_agent_07_05_cli-and-commands-repl-io.md",
        "05_agent_07_06_cli-and-commands-hot-reload.md",
        "05_agent_07_07_cli-and-commands-migration-notes.md",
        "05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md",
        "05_agent_07_09_cli-and-commands-slash-commands-context-db.md",
        "05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md",
        "05_agent_07_11_cli-and-commands-slash-commands-memory-other.md",
    ]
    related_all = [GUIDE] + all_files

    def rel(exclude_suffix: str) -> list[str]:
        return [r for r in related_all if not r.endswith(exclude_suffix)]

    cli_reference_body = (
        "本章(07 CLI and Commands)のファイル索引:\n\n"
        "| ファイル | 内容 |\n"
        "|---|---|\n"
        "| [05_agent_07_04_cli-and-commands-purpose.md](05_agent_07_04_cli-and-commands-purpose.md) | 目的 |\n"
        "| [05_agent_07_05_cli-and-commands-repl-io.md](05_agent_07_05_cli-and-commands-repl-io.md) | REPL入出力モデル |\n"
        "| [05_agent_07_02_cli-and-commands-cliview.md](05_agent_07_02_cli-and-commands-cliview.md) | CLIView(`agent/cli_view.py`) |\n"
        "| [05_agent_07_03_cli-and-commands-command-registry.md](05_agent_07_03_cli-and-commands-command-registry.md) | CommandRegistry(`agent/commands/registry.py`) |\n"
        "| [05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md](05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md) | スラッシュコマンド: Session, MCP, Config/stats |\n"
        "| [05_agent_07_09_cli-and-commands-slash-commands-context-db.md](05_agent_07_09_cli-and-commands-slash-commands-context-db.md) | スラッシュコマンド: Context, DB, Plan |\n"
        "| [05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md](05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md) | スラッシュコマンド: Workflow, Debug/audit, RAG/Export |\n"
        "| [05_agent_07_11_cli-and-commands-slash-commands-memory-other.md](05_agent_07_11_cli-and-commands-slash-commands-memory-other.md) | スラッシュコマンド: Memory, MDQ, Plugin, Other |\n"
        "| [05_agent_07_06_cli-and-commands-hot-reload.md](05_agent_07_06_cli-and-commands-hot-reload.md) | ホットリロードの範囲(`/reload`) |\n"
        "| [05_agent_07_07_cli-and-commands-migration-notes.md](05_agent_07_07_cli-and-commands-migration-notes.md) | 移行に関する注記 |\n"
    )

    write_part(
        "05_agent_07_01_cli-and-commands-cli-reference.md",
        cli_reference_body,
        "Agent CLI and Commands - Chapter Index",
        ["agent", "cli", "commands", "index"],
        rel("cli-reference.md"),
        "05_agent_07_cli-and-commands.md",
        ["CLI reference index", "chapter 07 file index"],
    )
    write_part(
        "05_agent_07_02_cli-and-commands-cliview.md",
        cliview,
        "Agent CLI and Commands - CLIView",
        ["agent", "cli", "cliview", "callbacks"],
        rel("cliview.md"),
        "05_agent_07_cli-and-commands.md",
        ["CLIView", "callbacks", "key methods", "protocols for testing"],
    )
    write_part(
        "05_agent_07_03_cli-and-commands-command-registry.md",
        command_registry,
        "Agent CLI and Commands - CommandRegistry",
        ["agent", "cli", "command-registry", "module-ownership"],
        rel("command-registry.md"),
        "05_agent_07_cli-and-commands.md",
        ["CommandRegistry", "module ownership"],
    )
    write_part(
        "05_agent_07_04_cli-and-commands-purpose.md",
        purpose,
        "Agent CLI and Commands - Purpose",
        ["agent", "cli", "purpose"],
        rel("purpose.md"),
        "05_agent_07_cli-and-commands.md",
        ["purpose"],
    )
    write_part(
        "05_agent_07_05_cli-and-commands-repl-io.md",
        repl_io,
        "Agent CLI and Commands - REPL Input/Output Model",
        ["agent", "cli", "repl-io"],
        rel("repl-io.md"),
        "05_agent_07_cli-and-commands.md",
        ["REPL input/output model"],
    )
    write_part(
        "05_agent_07_06_cli-and-commands-hot-reload.md",
        hot_reload,
        "Agent CLI and Commands - Hot-Reload Scope",
        ["agent", "cli", "hot-reload", "reload-classification"],
        rel("hot-reload.md"),
        "05_agent_07_cli-and-commands.md",
        [
            "hot-reload scope",
            "/reload",
            "output format",
            "reload classification summary",
        ],
    )
    write_part(
        "05_agent_07_07_cli-and-commands-migration-notes.md",
        migration_notes,
        "Agent CLI and Commands - Migration Notes",
        ["agent", "cli", "migration-notes"],
        rel("migration-notes.md"),
        "05_agent_07_cli-and-commands.md",
        ["migration notes"],
    )
    write_part(
        "05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md",
        slash_session_mcp,
        "Agent CLI and Commands - Slash Commands: Session, MCP, Config/Stats",
        ["agent", "cli", "slash-commands", "session", "mcp", "config"],
        rel("session-mcp.md"),
        "05_agent_07_cli-and-commands.md",
        [
            "slash command reference",
            "session category",
            "MCP category",
            "config/stats category",
        ],
    )
    write_part(
        "05_agent_07_09_cli-and-commands-slash-commands-context-db.md",
        slash_context_db,
        "Agent CLI and Commands - Slash Commands: Context, DB, Plan",
        ["agent", "cli", "slash-commands", "context", "db", "plan"],
        rel("context-db.md"),
        "05_agent_07_cli-and-commands.md",
        [
            "context category",
            "DB category",
            "/db rag subcommands",
            "/db session subcommands",
            "plan category",
        ],
    )
    write_part(
        "05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md",
        slash_workflow_debug,
        "Agent CLI and Commands - Slash Commands: Workflow, Debug/Audit, RAG/Export",
        ["agent", "cli", "slash-commands", "workflow", "debug", "rag-export"],
        rel("workflow-debug.md"),
        "05_agent_07_cli-and-commands.md",
        [
            "workflow category",
            "startup recovery",
            "debug/audit category",
            "RAG/export category",
        ],
    )
    write_part(
        "05_agent_07_11_cli-and-commands-slash-commands-memory-other.md",
        slash_memory_other,
        "Agent CLI and Commands - Slash Commands: Memory, MDQ, Plugin, Other",
        ["agent", "cli", "slash-commands", "memory", "mdq", "plugin"],
        rel("memory-other.md"),
        "05_agent_07_cli-and-commands.md",
        ["memory category", "MDQ category", "plugin category", "other category"],
    )


if __name__ == "__main__":
    main()
