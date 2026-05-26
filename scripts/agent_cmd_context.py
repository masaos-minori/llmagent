#!/usr/bin/env python3
"""
agent_cmd_context.py
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

from db_maintenance import (
    RetentionConfig,
    checkpoint_wal,
    purge_old_sessions,
    recover_corruption,
    vacuum_db,
)
from sqlite_helper import SQLiteHelper

if TYPE_CHECKING:
    from agent_context import AgentContext

logger = logging.getLogger(__name__)


def _budget_breakdown(messages: list) -> dict[str, int]:
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
                "[Additional context]"
            ):
                counts["rag"] += len(text)
            else:
                counts["system"] += len(text)
        elif role == "tool":
            counts["tool_results"] += len(text)
        elif role == "assistant":
            counts["history"] += len(text)
            if tool_calls:
                import json  # noqa: PLC0415

                counts["tool_results"] += len(json.dumps(tool_calls))
        else:
            counts["history"] += len(text)
    return counts


class _ContextMixin:
    """Context, history, and database slash-command handlers."""

    if TYPE_CHECKING:
        _ctx: "AgentContext"

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
        print("Context state:")
        print(f"  Messages        : {n_msgs}")
        print(f"  Total chars     : {total_chars:,}")
        print(f"  Compress limit  : {compress_limit:,}")
        print(f"  Remaining       : {remaining:,} chars until compression")
        print(f"  Compress count  : {compress_count}")
        print(f"  System prompt   : {ctx.system_prompt_name}")
        print(f"  System preview  : {sys_preview!r}")
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
        """Switch the active system prompt to a named preset defined in agent.json."""
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
        if subcmd == "stats":
            self._db_stats()
        elif subcmd == "urls":
            self._db_list_urls(rest)
        elif subcmd == "clean":
            url = rest.strip()
            if not url:
                print("Usage: /db clean <url>")
                return
            ok = self._ctx.session.delete_document(url)
            print(f"Document deleted: {url}" if ok else f"Document not found: {url}")
        elif subcmd == "rebuild-fts":
            self._db_rebuild_fts()
        elif subcmd == "health":
            self._db_health()
        elif subcmd == "checkpoint":
            self._db_checkpoint(rest.strip().upper() if rest.strip() else None)
        elif subcmd == "vacuum":
            self._db_vacuum()
        elif subcmd == "purge":
            self._db_purge(rest)
        elif subcmd == "recover":
            self._db_recover(rest.strip() if rest.strip() else None)
        else:
            print(
                "Usage: /db stats | /db urls [--lang ja|en] [--limit N]"
                " | /db clean <url> | /db rebuild-fts"
                " | /db health | /db checkpoint [MODE]"
                " | /db vacuum | /db purge [--max-sessions N] [--max-age-days N]"
                " | /db recover [<backup-path>]"
            )

    def _db_stats(self) -> None:
        """Print document/chunk/session/message counts from DB."""
        try:
            with SQLiteHelper().open(row_factory=True) as db:
                docs = db.fetchall("SELECT COUNT(*) AS n FROM documents")[0]["n"]
                chunks = db.fetchall("SELECT COUNT(*) AS n FROM chunks")[0]["n"]
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
        lang: str | None = None
        limit: int = 20
        tokens = rest.split()
        i = 0
        while i < len(tokens):
            if tokens[i] == "--lang" and i + 1 < len(tokens):
                candidate = tokens[i + 1]
                if candidate in ("ja", "en"):
                    lang = candidate
                i += 2
            elif tokens[i] == "--limit" and i + 1 < len(tokens):
                try:
                    limit = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1
        self._ctx.session.list_documents(lang, limit)

    def _db_rebuild_fts(self) -> None:
        """Rebuild the FTS5 chunks_fts index."""
        try:
            with SQLiteHelper().open(write_mode=True) as db:
                db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
                db.commit()
            print("FTS5 index rebuilt.")
        except Exception as e:
            print(f"FTS rebuild error: {e}")

    def _db_health(self) -> None:
        """Print DB health metrics: journal mode, integrity, page stats."""
        try:
            with SQLiteHelper().open() as db:
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
            with SQLiteHelper().open(write_mode=True) as db:
                result = checkpoint_wal(db, mode)
            print(f"WAL checkpoint complete: {result}")
        except Exception as e:
            print(f"Checkpoint error: {e}")

    def _db_vacuum(self) -> None:
        """Run VACUUM to rebuild the DB file and reclaim free pages."""
        try:
            with SQLiteHelper().open(write_mode=True) as db:
                vacuum_db(db)
            print("VACUUM complete.")
        except Exception as e:
            print(f"VACUUM error: {e}")

    def _db_purge(self, rest: str) -> None:
        """Purge old sessions. Options: --max-sessions N --max-age-days N"""
        tokens = rest.split()
        max_sessions: int | None = None
        max_age_days: int | None = None
        i = 0
        while i < len(tokens):
            if tokens[i] == "--max-sessions" and i + 1 < len(tokens):
                try:
                    max_sessions = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            elif tokens[i] == "--max-age-days" and i + 1 < len(tokens):
                try:
                    max_age_days = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
            else:
                i += 1
        cfg_kwargs: dict[str, int] = {}
        if max_sessions is not None:
            cfg_kwargs["max_sessions"] = max_sessions
        if max_age_days is not None:
            cfg_kwargs["max_age_days"] = max_age_days
        cfg = RetentionConfig(**cfg_kwargs) if cfg_kwargs else None
        try:
            with SQLiteHelper().open(write_mode=True) as db:
                result = purge_old_sessions(db, cfg)
            print(
                f"Purged: {result['age_deleted']} by age, {result['count_deleted']} by count"
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
