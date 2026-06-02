#!/usr/bin/env python3
"""cmd_context.py
Context, history, and database mixin for CommandRegistry.

Extracted from agent_commands.py.  Provides _ContextMixin with:
  _cmd_context   — /context: runtime state and budget breakdown
  _cmd_clear     — /clear: reset history and session stats
  _cmd_undo      — /undo: roll back the last turn
  _cmd_history   — /history: show recent messages
  _cmd_system    — /system: switch system prompt preset
  _cmd_db        — /db dispatcher
  _db_stats      — DB record counts
  _db_list_urls  — list document URLs with filters
  _db_rebuild_fts — rebuild the FTS5 index

Also defines _budget_breakdown (re-exported by agent_commands.py).
"""

import logging
from typing import TYPE_CHECKING

import orjson
from shared.git_helper import get_repo_info
from shared.types import LLMMessage

from db.helper import SQLiteHelper
from db.maintenance import (
    RetentionConfig,
    checkpoint_wal,
    purge_old_sessions,
    recover_corruption,
    vacuum_db,
)

if TYPE_CHECKING:
    from agent.context import AgentContext

logger = logging.getLogger(__name__)


def _parse_flag_int(tokens: list[str], flag: str) -> int | None:
    """Return the integer value that follows flag in tokens, or None."""
    for i, t in enumerate(tokens):
        if t == flag and i + 1 < len(tokens):
            try:
                return int(tokens[i + 1])
            except ValueError:
                pass
    return None


def _parse_flag_str(tokens: list[str], flag: str) -> str | None:
    """Return the string value that follows flag in tokens, or None."""
    for i, t in enumerate(tokens):
        if t == flag and i + 1 < len(tokens):
            return tokens[i + 1]
    return None


def _budget_breakdown(messages: list[LLMMessage]) -> dict[str, int]:
    """Compute per-category character counts for the given message list.

    Categories: system, rag, history, tool_results.
    RAG context is identified by '[Reference documents]' / '[Additional context]'
    prefix. Tool results include role='tool' messages and assistant tool_calls JSON.
    """
    counts: dict[str, int] = {
        "system": 0,
        "rag": 0,
        "history": 0,
        "tool_results": 0,
    }
    for m in messages:
        role = m.get("role", "")
        text = str(m.get("content") or "")
        tool_calls = m.get("tool_calls") or []
        if role == "system":
            if text.startswith("[Reference documents]") or text.startswith(
                "[Additional context]",
            ):
                counts["rag"] += len(text)
            else:
                counts["system"] += len(text)
        elif role == "tool":
            counts["tool_results"] += len(text)
        elif role == "assistant":
            counts["history"] += len(text)
            if tool_calls:
                counts["tool_results"] += len(orjson.dumps(tool_calls))
        else:
            counts["history"] += len(text)
    return counts


def _format_memory_status(ctx: "AgentContext") -> str:
    """Return a one-line summary of the memory layer state."""
    if ctx.services.memory is None:
        return "disabled"
    mem = ctx.services.memory
    by_type = mem.stat_by_type
    return (
        f"enabled (entries={mem.stat_entries},"
        f" semantic={by_type.get('semantic', 0)},"
        f" episodic={by_type.get('episodic', 0)},"
        f" vec_entries={mem.stat_vec_entries})"
    )


def _token_source_label(token_is_exact: bool, tokenize_configured: bool) -> str:
    """Return a human-readable label for the token count source."""
    if token_is_exact:
        return "LLM usage"
    if tokenize_configured:
        return "/tokenize (next turn)"
    return "chars/4"


class _ContextMixin:
    """Context, history, and database slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

    def _print_token_line(
        self,
        ctx: "AgentContext",
        total_chars: int,
    ) -> None:
        """Print token count / estimate with source label and optional limit info."""
        token_is_exact = ctx.stat_input_tokens is not None
        token_estimate = (
            ctx.services.hist_mgr.count_tokens(ctx.history, ctx.stat_input_tokens)
            if ctx.services.hist_mgr is not None
            else total_chars // 4
        )
        token_limit = ctx.cfg.context_token_limit
        token_limit_str = f"{token_limit:,}" if token_limit > 0 else "disabled"
        token_label = "Token count  " if token_is_exact else "Token estimate"
        tokenize_configured = bool(getattr(ctx.cfg, "tokenize_url", ""))
        src = _token_source_label(token_is_exact, tokenize_configured)
        if token_limit > 0:
            token_pct = int(token_estimate * 100 / token_limit)
            print(
                f"  {token_label} : {token_estimate:,}"
                f" ({src}, limit={token_limit:,} [active] {token_pct}%)",
            )
        else:
            print(f"  {token_label} : {token_estimate:,} ({src})")
        print(f"  Token limit     : {token_limit_str}")

    def _cmd_context(self) -> None:
        """Print runtime conversation context state."""
        ctx = self._ctx
        total_chars = (
            ctx.services.hist_mgr.count_chars(ctx.history)
            if ctx.services.hist_mgr is not None
            else sum(len(str(m.get("content") or "")) for m in ctx.history)
        )
        compress_limit = ctx.cfg.context_char_limit
        remaining = compress_limit - total_chars
        n_msgs = len(ctx.history)
        system_msgs = [m for m in ctx.history if m["role"] == "system"]
        sys_preview = str(system_msgs[0].get("content", ""))[:80] if system_msgs else ""
        compress_count = (
            ctx.services.hist_mgr.stat_compress_count
            if ctx.services.hist_mgr is not None
            else 0
        )
        breakdown = _budget_breakdown(ctx.history)
        total_bd = sum(breakdown.values()) or 1  # avoid zero division
        mem_status = _format_memory_status(ctx)
        git_info = get_repo_info()
        git_str = (
            f"{git_info['branch']} @ {git_info['commit']} {git_info['message']}"
            if git_info
            else "unavailable"
        )
        # Token count note: exact when LLM reports usage.prompt_tokens; estimate otherwise.
        # /tokenize exact counting needs async; /context shows best synchronous value.
        print("Context state:")
        print(f"  Messages        : {n_msgs}")
        print(f"  Total chars     : {total_chars:,}")
        print(f"  Compress limit  : {compress_limit:,}")
        print(f"  Remaining       : {remaining:,} chars until compression")
        print(f"  Compress count  : {compress_count}")
        print(f"  System prompt   : {ctx.system_prompt_name}")
        print(f"  System preview  : {sys_preview!r}")
        self._print_token_line(ctx, total_chars)
        print(f"  Memory layer    : {mem_status}")
        print(f"  Git             : {git_str}")
        print("Budget breakdown:")
        for cat, n in breakdown.items():
            pct = n * 100 // total_bd
            print(f"  {cat:<14}: {n:>8,} chars ({pct:>3}%)")

    def _cmd_clear(self, args: str = "") -> None:
        """Reset conversation history to system prompt only and clear session stats.

        /clear     — reset history in the current session
        /clear new — reset history and start a new DB session
        """
        ctx = self._ctx
        ctx.history = ctx.history[:1]
        ctx.stat_turns = 0
        ctx.stat_tool_calls = 0
        ctx.stat_rag_hits = 0
        ctx.stat_tool_errors = 0
        ctx.stat_latency = {}
        ctx.stat_semantic_cache_hits = 0
        if ctx.services.llm is not None:
            ctx.services.llm.stat_retries = 0
        if "new" in args.split():
            ctx.session.start()
            print("History cleared. New session started.")
        else:
            print("History cleared. Session stats reset.")

    def _cmd_undo(self) -> None:
        """Roll back the last user+assistant turn from in-memory history and DB."""
        ctx = self._ctx
        last_user_idx = next(
            (
                i
                for i in range(len(ctx.history) - 1, -1, -1)
                if ctx.history[i]["role"] == "user"
            ),
            None,
        )
        if last_user_idx is None:
            print("Nothing to undo.")
            return
        removed = len(ctx.history) - last_user_idx
        ctx.history = ctx.history[:last_user_idx]
        ctx.stat_turns = max(0, ctx.stat_turns - 1)
        ctx.session.delete_last_turn()
        logger.info(f"Undo: removed {removed} messages from history")
        print("Last turn undone.")

    def _cmd_history(self, args: str) -> None:
        """Print last N user/assistant messages in compact form."""
        try:
            n = int(args.strip()) if args.strip() else 5
        except ValueError:
            print("Usage: /history [n]")
            return
        ctx = self._ctx
        turns = [m for m in ctx.history if m["role"] in ("user", "assistant")]
        recent = turns[-n:]
        if not recent:
            print("No conversation history.")
            return
        for msg in recent:
            content = msg.get("content") or ""
            preview = content[:120].replace("\n", " ")
            if len(content) > 120:
                preview += "..."
            print(f"[{msg['role']}] {preview}")

    def _cmd_system(self, args: str) -> None:
        """Switch the active system prompt to a named preset defined in agent.toml."""
        ctx = self._ctx
        name = args.strip()
        if not name:
            prompts = ctx.cfg.system_prompts
            names = ", ".join(prompts.keys()) if prompts else "(none)"
            print(f"Current: {ctx.system_prompt_name}")
            print(f"Available: {names}")
            return
        if name not in ctx.cfg.system_prompts:
            names = ", ".join(ctx.cfg.system_prompts.keys())
            print(f"Unknown preset '{name}'. Available: {names}")
            return
        ctx.system_prompt_name = name
        prompt = ctx.cfg.system_prompts[name]
        if ctx.history and ctx.history[0]["role"] == "system":
            ctx.history[0]["content"] = prompt
        else:
            ctx.history.insert(0, {"role": "system", "content": prompt})
        logger.info(f"System prompt switched to '{name}'")
        print(f"System prompt: {name}")

    def _cmd_db(self, args: str) -> None:
        """Handle /db stats|urls|clean|rebuild-fts|health|checkpoint|vacuum|purge|recover."""
        parts = args.strip().split(None, 1)
        subcmd = parts[0] if parts else ""
        rest = parts[1] if len(parts) == 2 else ""
        dispatch = {
            "stats": self._db_stats,
            "urls": lambda: self._db_list_urls(rest),
            "clean": lambda: self._db_clean(rest),
            "rebuild-fts": self._db_rebuild_fts,
            "health": self._db_health,
            "checkpoint": lambda: self._db_checkpoint(rest.strip().upper() or None),
            "vacuum": self._db_vacuum,
            "purge": lambda: self._db_purge(rest),
            "recover": lambda: self._db_recover(rest.strip() or None),
        }
        handler = dispatch.get(subcmd)
        if handler:
            handler()
        else:
            print(
                "Usage: /db stats | /db urls [--lang ja|en] [--limit N]"
                " | /db clean <url> | /db rebuild-fts"
                " | /db health | /db checkpoint [MODE]"
                " | /db vacuum | /db purge [--max-sessions N] [--max-age-days N]"
                " | /db recover [<backup-path>]",
            )

    def _db_clean(self, rest: str) -> None:
        """Delete a document by URL from the vector store."""
        url = rest.strip()
        if not url:
            print("Usage: /db clean <url>")
            return
        ok = self._ctx.session.delete_document(url)
        print(f"Document deleted: {url}" if ok else f"Document not found: {url}")

    def _db_stats(self) -> None:
        """Print document/chunk/session/message counts from both DBs."""
        try:
            # documents and chunks live in rag.sqlite
            with SQLiteHelper("rag").open(row_factory=True) as db:
                docs = db.fetchall("SELECT COUNT(*) AS n FROM documents")[0]["n"]
                chunks = db.fetchall("SELECT COUNT(*) AS n FROM chunks")[0]["n"]
            # sessions and messages live in session.sqlite
            with SQLiteHelper("session").open(row_factory=True) as db:
                sessions = db.fetchall("SELECT COUNT(*) AS n FROM sessions")[0]["n"]
                messages = db.fetchall("SELECT COUNT(*) AS n FROM messages")[0]["n"]
            print(f"documents : {docs:,}")
            print(f"chunks    : {chunks:,}")
            print(f"sessions  : {sessions:,}")
            print(f"messages  : {messages:,}")
        except Exception as e:
            print(f"DB stats error: {e}")

    def _db_list_urls(self, rest: str) -> None:
        """Parse --lang / --limit options from rest and delegate to AgentSession."""
        tokens = rest.split()
        lang_raw = _parse_flag_str(tokens, "--lang")
        lang: str | None = lang_raw if lang_raw in ("ja", "en") else None
        limit = _parse_flag_int(tokens, "--limit") or 20
        self._ctx.session.list_documents(lang, limit)

    def _db_rebuild_fts(self) -> None:
        """Rebuild the FTS5 chunks_fts index in rag.sqlite."""
        try:
            # chunks_fts is a virtual table in rag.sqlite, not session.sqlite
            with SQLiteHelper("rag").open(write_mode=True) as db:
                db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
                db.commit()
            print("FTS5 index rebuilt.")
        except Exception as e:
            print(f"FTS rebuild error: {e}")

    def _db_health(self) -> None:
        """Print DB health metrics: journal mode, integrity, page stats."""
        try:
            with SQLiteHelper("session").open() as db:
                info = db.health_check()
            print(f"journal_mode    : {info['journal_mode']}")
            print(f"integrity       : {info['integrity']}")
            print(f"page_count      : {info['page_count']:,}")
            print(f"page_size       : {info['page_size']:,} bytes")
            print(f"freelist_count  : {info['freelist_count']:,}")
            print(f"db_size         : {info['db_size_bytes']:,} bytes")
        except Exception as e:
            print(f"DB health error: {e}")

    def _db_checkpoint(self, mode: str | None) -> None:
        """Run WAL checkpoint. mode: PASSIVE|FULL|RESTART|TRUNCATE (default from config)."""
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                result = checkpoint_wal(db, mode)
            print(f"WAL checkpoint complete: {result}")
        except Exception as e:
            print(f"Checkpoint error: {e}")

    def _db_vacuum(self) -> None:
        """Run VACUUM to rebuild the DB file and reclaim free pages."""
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                vacuum_db(db)
            print("VACUUM complete.")
        except Exception as e:
            print(f"VACUUM error: {e}")

    def _db_purge(self, rest: str) -> None:
        """Purge old sessions. Options: --max-sessions N --max-age-days N"""
        tokens = rest.split()
        max_sessions = _parse_flag_int(tokens, "--max-sessions")
        max_age_days = _parse_flag_int(tokens, "--max-age-days")
        cfg_kwargs: dict[str, int] = {}
        if max_sessions is not None:
            cfg_kwargs["max_sessions"] = max_sessions
        if max_age_days is not None:
            cfg_kwargs["max_age_days"] = max_age_days
        cfg = RetentionConfig(**cfg_kwargs) if cfg_kwargs else None
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                result = purge_old_sessions(db, cfg)
            print(
                f"Purged: {result['age_deleted']} by age, {result['count_deleted']} by count",
            )
        except Exception as e:
            print(f"Purge error: {e}")

    def _db_recover(self, backup_path: str | None) -> None:
        """Run integrity check; restore from backup_path if corruption found."""
        try:
            ok = recover_corruption(backup_path)
            print("Recovery succeeded." if ok else "Recovery failed — check logs.")
        except Exception as e:
            print(f"Recovery error: {e}")
