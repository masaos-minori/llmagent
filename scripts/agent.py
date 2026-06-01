#!/usr/bin/env python3
"""agent.py
Interactive CLI agent — REPL interface for LLM + RAG + MCP tool calling.
Can be started from any directory; sys.path is adjusted at startup.

== Usage ==
  python agent.py       Start interactive REPL

== Slash commands (REPL) ==
  /help                          Show usage and available tools
  /mcp                           Show MCP server status, tool list, and connectivity check
  /mcp install <name>            Scaffold a new MCP server template files (wizard)
  /config                        Show current configuration and source file paths
  /stats                         Show session statistics (turns, tool calls, RAG hits)
  /context                       Show runtime context state and compression info
  /compact                       Force immediate compression of conversation history
  /clear [new]                   Reset conversation history; [new] also starts a new DB session
  /session list [n]              List past sessions (default: 20)
  /session load <id>             Restore a past session's conversation history
  /session rename <title>        Rename the current session
  /session delete <id>           Delete a session and all its messages
  /db stats                      Show document/chunk/session/message counts
  /db urls [--lang ja|en] [--limit N]  List registered document URLs
  /db clean <url>                Delete a document and its chunks from the DB
  /db rebuild-fts                Rebuild the FTS5 chunks_fts index
  /ingest <url|path> [lang]      Crawl and ingest a URL or local file into the RAG DB
  /debug                         Toggle RAG pipeline debug output ON/OFF
  /rag                           Show current RAG step status
  /rag on|off                    Enable/disable RAG search entirely
  /rag mqe on|off                Enable/disable Multi-Query Expansion
  /rag rerank on|off             Enable/disable Cross-Encoder reranking
  /rag search <query>            Dry-run RAG pipeline and display chunks (no LLM call)
  /undo                          Roll back the last user+assistant turn
  /history [n]                   Show last N user/assistant messages (default: 5)
  /system [name]                 Switch system prompt preset
  /set temperature <f>           Change LLM generation temperature at runtime
  /set max_tokens <n>            Change LLM max tokens at runtime
  /reload                        Reload config/agent.toml and apply runtime parameters
  /note add <text>               Add a persistent cross-session note
  /note list                     List all notes
  /note delete <id>              Delete a note by ID
  /tool list                     List stored tool results (current session)
  /tool show <idx>               Show full text of a stored tool result
  /export [md|json] [file]       Export conversation history (default: Markdown to stdout)
  /exit                          Exit the REPL (Ctrl-D also works)

== Data flow ==
  [1] User types a question at the prompt
  [2] RAG search: MQE -> embed -> KNN+BM25 -> RRF -> rerank -> top-K context chunks
  [3] Agent augments the user message with retrieved context
  [4] LLM request with augmented input + tool definitions
  [5] If model returns tool_calls, execute via MCP HTTP endpoints
  [6] Tool results appended to history and re-sent to LLM
  [7] Steps 5-6 repeat until no more tool calls (or MAX_TOOL_TURNS reached)
  [8] Final answer printed; conversation history preserved for the next turn

== Transport ==
  MCP servers are accessed via HTTP (ports 8004-8006 must already be running).

== Config files ==
  config/common.toml  : DB path, sqlite-vec extension path
  config/agent.toml   : LLM URLs, tool definitions, system prompts,
                        RAG flags, max turns
"""

import asyncio
import signal
import sys
from pathlib import Path

# Ensure imports resolve regardless of the working directory from which this
# script is invoked (not only from /opt/llm/scripts/).
sys.path.insert(0, str(Path(__file__).parent))

from agent.repl import AgentREPL


def _request_shutdown(_signum: int, _frame: object) -> None:
    # Propagate SIGTERM as a clean exit; the finally block in run() closes resources.
    raise SystemExit(0)


# Register SIGTERM handler before starting the event loop so that graceful
# shutdown works when the process is stopped by the OS or a service manager.
signal.signal(signal.SIGTERM, _request_shutdown)


if __name__ == "__main__":
    # Entry point: launch the interactive REPL and block until the user exits.
    # AgentREPL.run() is an async coroutine; asyncio.run() manages the event loop.
    asyncio.run(AgentREPL().run())
