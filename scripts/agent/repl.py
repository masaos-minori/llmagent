#!/usr/bin/env python3
"""AgentREPL

Interactive REPL agent with MCP tool calling.
Imported by agent.py as the entry point.
Slash-command handlers live in agent/commands/registry.CommandRegistry.
Turn-level orchestration (LLM loop, tool dispatch) lives in agent/orchestrator.py.

Architecture (dependency injection via AgentContext):
  AgentContext   — shared mutable state container (agent/context.py)
  CLIView        — readline, multiline input display (agent/cli_view.py)
  LLMClient      — HTTP retry, payload build, SSE stream (shared/llm_client.py)
  ToolExecutor   — MCP routing, error handling, TTL cache (shared/tool_executor.py)
  HistoryManager — character counting, LLM-based compression (agent/history.py)
  CommandRegistry — slash-command dispatch (agent/commands/registry.py)
  Orchestrator   — per-turn task control: LLM loop, tool dispatch (agent/orchestrator.py)
  AgentConfig    — mutable runtime config dataclass (agent/config.py)

AgentREPL responsibilities:
  _repl_loop           — main input/dispatch loop
  _init_components     — DI wiring
  run                  — startup sequence
"""

import asyncio
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import time
import uuid
from functools import cached_property
from typing import TYPE_CHECKING

from db.helper import SQLiteHelper
from shared.logger import Logger

from agent.cli_view import CLIView
from agent.commands.registry import CommandRegistry
from agent.context import AgentContext
from agent.diagnostic_store import DiagnosticStore
from agent.memory.models import HistoryMessage
from agent.output_tags import OutputTag
from agent.services.rag_maintenance_service import RagMaintenanceService
from agent.session import SchemaMissingError

if TYPE_CHECKING:
    from agent.orchestrator import Orchestrator

logger = Logger(__name__, "/opt/llm/logs/agent.log")

_REPL_RESERVED_COMMANDS = frozenset(["/exit"])


def builtin_command_names() -> frozenset[str]:
    """Return names of all built-in commands from _COMMANDS."""
    from agent.commands.command_defs_list import _COMMANDS

    return frozenset(cmd.name for cmd in _COMMANDS)


def reserved_repl_command_names() -> frozenset[str]:
    """Return names of REPL-reserved commands."""
    return _REPL_RESERVED_COMMANDS


def completion_command_names() -> frozenset[str]:
    """Return all commands available for tab completion."""
    return builtin_command_names() | reserved_repl_command_names()


# ─────────────────────────────────────────────────────────────────────────────
# REPLAgent: thin coordinator over AgentContext components
# ─────────────────────────────────────────────────────────────────────────────


class AgentREPL:
    """Interactive REPL agent.

    Coordinates LLMClient, ToolExecutor, HistoryManager,
    CommandRegistry, and CLIView via AgentContext dependency injection.
    All persistent session state is held in self._ctx (AgentContext).
    """

    _WAL_CHECKPOINT_TIMEOUT_S: float = 30.0
    _WAL_BACKUP_TIMEOUT_S: float = 10.0
    _GRACEFUL_TIMEOUT_S: float = 10.0

    @cached_property
    def SLASH_COMMANDS(self) -> frozenset[str]:
        """Tab completion candidates derived from _COMMANDS + REPL-reserved commands."""
        return completion_command_names()

    def __init__(self) -> None:
        """Initialize REPL agent with empty context and view."""
        self._ctx = AgentContext()
        self._view = CLIView(list(self.SLASH_COMMANDS))
        self._cmds: CommandRegistry | None = None
        self._orchestrator: Orchestrator | None = None
        self._diagnostic_store = DiagnosticStore()
        self._turn_active: bool = False
        self._shutdown_event: asyncio.Event | None = None
        self._input_coro: asyncio.Task[str] | None = None

    @property
    def _prompt(self) -> str:
        """REPL input prompt string."""
        return "> "

    @property
    def _n_tools(self) -> int:
        """Number of tools available (from config/tools_definitions.toml)."""
        return len(self._ctx.cfg.tool.tool_definitions)

    def _get_chunk_count(self) -> str:
        """Return formatted chunk count from DB, or '?' on error."""
        try:
            count = RagMaintenanceService().stats_rag()[1]
            return f"{count:,}"
        except (sqlite3.Error, OSError, RuntimeError) as e:
            logger.debug("Failed to get chunk count: %s", e)
            return "?"

    async def _persist_session_memories(self, ctx: AgentContext) -> None:
        """Extract and persist session memories before compression or resource close."""
        if ctx.services is not None and ctx.services.memory is not None:
            try:
                history = []
                for m in ctx.conv.history:
                    expected_keys = {"role", "content"}
                    extra_keys = set(m.keys()) - expected_keys
                    if extra_keys:
                        logger.warning(
                            "Unexpected keys in history message: %s — full message: %s",
                            extra_keys,
                            m,
                        )
                    history.append(
                        HistoryMessage(role=m["role"], content=m.get("content") or "")
                    )
                await ctx.services.memory.on_session_stop(
                    session_id=ctx.session.session_id,
                    history=history,
                    turn_id=ctx.turn.current_turn_id,
                )
            except (RuntimeError, sqlite3.Error, OSError):
                logger.exception(
                    "Memory on_session_stop failed; session data may be incomplete"
                )

    def _persist_session_diagnostics(self, ctx: AgentContext) -> None:
        """Persist a lightweight runtime diagnostics summary at session end."""
        try:
            stats = ctx.stats
            llm = ctx.services.llm if ctx.services is not None else None
            hist_mgr = ctx.services.hist_mgr if ctx.services is not None else None
            session_id = ctx.session.session_id

            latency_summary = {}
            for step, samples in stats.stat_latency.items():
                if samples:
                    latency_summary[step] = {
                        "count": len(samples),
                        "mean_ms": round(sum(samples) / len(samples) * 1000, 2),
                        "max_ms": round(max(samples) * 1000, 2),
                    }

            workflow_count = 0
            task_count = 0
            approval_events = 0
            retry_count = 0
            artifacts: list[str] = []
            if session_id is not None:
                try:
                    from agent.workflow.state_store import StateStore

                    store = StateStore()
                    sid = str(session_id)
                    task_count = store.get_task_count(sid)
                    workflow_count = store.get_workflow_count(sid)
                    approval_events = store.get_approval_count(sid)
                    execute_attempts = store.get_execute_attempt_count(sid)
                    retry_count = max(0, execute_attempts - task_count)
                    artifacts = store.get_artifact_uris(sid)
                except (RuntimeError, sqlite3.Error):
                    pass

            rag_query_count = 0
            rag_stage_outcomes: list[dict] = []
            if session_id is not None:
                try:
                    entries = self._diagnostic_store.fetch(session_id)
                    rag_entries = [e for e in entries if e.get("kind") == "rag_query"]
                    rag_query_count = len(rag_entries)
                    for e in rag_entries:
                        try:
                            diag = json.loads(e["content"])
                            rag_stage_outcomes.extend(diag.get("stage_results", []))
                        except (json.JSONDecodeError, KeyError):
                            pass
                except (sqlite3.Error, RuntimeError):
                    pass

            summary = {
                "session_id": session_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "turns": stats.stat_turns,
                "tool_calls": stats.stat_tool_calls,
                "tool_errors": stats.stat_tool_errors,
                "partial_completions": stats.stat_partial_completions,
                "parse_errors": llm.stat_parse_errors if llm is not None else 0,
                "heartbeat_timeouts": (
                    llm.stat_heartbeat_timeouts if llm is not None else 0
                ),
                "reconnects": llm.stat_reconnects if llm is not None else 0,
                "semantic_cache_hits": stats.stat_semantic_cache_hits,
                "input_tokens": stats.stat_input_tokens,
                "output_tokens": stats.stat_output_tokens,
                "compress_count": (
                    hist_mgr.stat_compress_count if hist_mgr is not None else 0
                ),
                "fallback_truncate_count": (
                    hist_mgr.stat_fallback_truncate_count if hist_mgr is not None else 0
                ),
                "latency_summary": latency_summary,
                "workflow_count": workflow_count,
                "task_count": task_count,
                "approval_events": approval_events,
                "retry_count": retry_count,
                "artifacts": artifacts,
                "rag_query_count": rag_query_count,
                "rag_stage_outcomes": rag_stage_outcomes,
            }

            if artifacts or rag_stage_outcomes:
                # `artifacts`/`rag_stage_outcomes` are the same list objects stored under
                # `summary["artifacts"]`/`summary["rag_stage_outcomes"]` above; referencing
                # them directly (instead of indexing the heterogeneous `summary` dict) keeps
                # a single source of truth while giving mypy a concrete `Sized` type.
                logger.warning(
                    "Session diagnostics contain sensitive fields (artifacts=%d, "
                    "rag_stage_outcomes=%d) that will be filtered before persistence",
                    len(artifacts),
                    len(rag_stage_outcomes),
                )

            # Persist to queryable DiagnosticStore
            try:
                self._diagnostic_store.save(
                    session_id,
                    kind="session_summary",
                    content=json.dumps(summary),
                )
            except (RuntimeError, sqlite3.Error) as e:
                # If diagnostic saving fails (e.g., due to encryption enforcement),
                # log the error but do not crash the REPL.
                logger.debug("DiagnosticStore.save failed: %s", e)
                self._view.write_warning(f"Diagnostics could not be saved: {e}")

        except (OSError, sqlite3.Error):
            logger.debug("Failed to persist session diagnostics", exc_info=True)

    def _wal_checkpoint_sync(self) -> tuple[bool, list[tuple[str, str]]]:
        """Attempt a WAL checkpoint (PASSIVE, falling back to TRUNCATE with retries).

        Runs synchronously; intended to be invoked via `loop.run_in_executor(...)` since
        `time.sleep()` blocks. Returns `(True, [])` on PASSIVE/TRUNCATE success or when
        journal mode is not WAL; returns `(False, errors)` when TRUNCATE exhausts its
        retries.
        """
        errors: list[tuple[str, str]] = []
        with SQLiteHelper("session").open(write_mode=True) as db:
            wal_mode = db.execute("PRAGMA journal_mode").fetchone()[0]
            if wal_mode.lower() != "wal":
                logger.debug("WAL checkpoint skipped: journal mode is %r", wal_mode)
                return True, errors
            # Try PASSIVE checkpoint first (no exclusive lock required)
            _passive_start = time.monotonic()
            try:
                db.checkpoint("PASSIVE")
                elapsed = time.monotonic() - _passive_start
                if elapsed > 5:
                    logger.warning(
                        "WAL PASSIVE checkpoint took %s seconds, falling back to TRUNCATE",
                        round(elapsed, 2),
                    )
                else:
                    logger.info("WAL checkpoint completed (PASSIVE) on shutdown")
                    return True, errors
            except sqlite3.Error as passive_err:
                logger.warning(
                    "WAL PASSIVE checkpoint failed, falling back to TRUNCATE: %s",
                    passive_err,
                )
            # Retry TRUNCATE checkpoint with exponential backoff
            for attempt in range(3):
                try:
                    db.checkpoint("TRUNCATE")
                    logger.info(
                        "WAL checkpoint completed (TRUNCATE) on shutdown after %d retries",
                        attempt + 1,
                    )
                    return True, errors
                except sqlite3.Error as truncate_err:
                    if attempt < 2:
                        logger.warning(
                            "WAL TRUNCATE checkpoint attempt %d failed, retrying: %s",
                            attempt + 1,
                            truncate_err,
                        )
                        time.sleep(2**attempt)
                    else:
                        logger.error(
                            "WAL TRUNCATE checkpoint failed after 3 attempts: %s",
                            truncate_err,
                        )
                        errors.append(
                            (
                                "wal_checkpoint_truncate",
                                f"{type(truncate_err).__name__}: {truncate_err}",
                            )
                        )
            return False, errors

    def _is_db_path_allowed(self, resolved_db_path: str) -> bool:
        """Return True when `resolved_db_path` is inside `cfg.approval.allowed_root`.

        Note: SQLite WAL files are always in the same directory as the DB file,
        so validating the DB path is equivalent to validating the WAL path.
        """
        allowed_root = self._ctx.cfg.approval.allowed_root
        if not allowed_root:
            return True
        resolved_root = os.path.realpath(allowed_root)
        return resolved_db_path == resolved_root or resolved_db_path.startswith(
            resolved_root + os.sep
        )

    def _wal_backup_sync(self) -> tuple[str | None, list[tuple[str, str]]]:
        """Copy the WAL file to a backup location. Runs synchronously via an executor.

        Returns `(backup_path_or_None, errors)`.
        """
        errors: list[tuple[str, str]] = []
        wal_backup_path: str | None = None
        try:
            with SQLiteHelper("session").open(write_mode=True) as db:
                db_path = db.execute("PRAGMA database_list").fetchone()[2]
                if db_path:
                    resolved_db_path = os.path.realpath(db_path)
                    if not self._is_db_path_allowed(resolved_db_path):
                        logger.warning(
                            "WAL backup skipped: resolved db path %s is outside allowed_root %s",
                            resolved_db_path,
                            self._ctx.cfg.approval.allowed_root,
                        )
                        errors.append(
                            (
                                "wal_backup_path_rejected",
                                f"resolved db path {resolved_db_path} is outside allowed_root "
                                f"{self._ctx.cfg.approval.allowed_root!r}",
                            )
                        )
                        return wal_backup_path, errors
                    wal_file = f"{db_path}-wal"
                    backup_dir = os.path.dirname(db_path) or "/tmp"
                    if not os.path.isdir(backup_dir) or not os.access(
                        backup_dir, os.W_OK
                    ):
                        logger.warning(
                            "WAL backup skipped: backup directory %s is not writable",
                            backup_dir,
                        )
                        errors.append(
                            (
                                "wal_backup_dir_not_writable",
                                f"backup directory not writable: {backup_dir}",
                            )
                        )
                        return wal_backup_path, errors
                    session_id = self._ctx.session.session_id
                    session_tag = (
                        str(session_id)
                        if session_id is not None
                        else uuid.uuid4().hex[:8]
                    )
                    wal_backup_path = os.path.join(
                        backup_dir,
                        f"{os.path.basename(db_path)}-wal-backup-{session_tag}-{int(time.time())}",
                    )
                    shutil.copy2(wal_file, wal_backup_path)
                    logger.warning("WAL file backed up to %s", wal_backup_path)
        except Exception as backup_err:
            logger.error("Failed to backup WAL file: %s", backup_err)
            errors.append(("wal_backup", f"{type(backup_err).__name__}: {backup_err}"))
        return wal_backup_path, errors

    async def _close_resources(self) -> None:
        """Close all session resources. Called in the run() finally block."""
        self._view.write_history()
        errors: list[tuple[str, str]] = []
        loop = asyncio.get_running_loop()

        async def _do_cleanup():
            nonlocal errors
            # 1. Cancel all pending tasks (except this one)
            pending_tasks = [
                t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()
            ]
            if pending_tasks:
                logger.info(
                    "Cancelling %d pending tasks during shutdown", len(pending_tasks)
                )
                for t in pending_tasks:
                    t.cancel()

                results = await asyncio.gather(*pending_tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        errors.append(
                            ("task_cancellation", f"{type(res).__name__}: {res}")
                        )

            # 2. WAL checkpoint before closing connections
            truncated_or_ok = False
            try:
                truncated_or_ok, checkpoint_errors = await asyncio.wait_for(
                    loop.run_in_executor(None, self._wal_checkpoint_sync),
                    timeout=self._WAL_CHECKPOINT_TIMEOUT_S,
                )
                errors.extend(checkpoint_errors)
            except TimeoutError:
                errors.append(
                    (
                        "wal_checkpoint_timeout",
                        f"TimeoutError: exceeded {self._WAL_CHECKPOINT_TIMEOUT_S}s",
                    )
                )
                logger.error(
                    "WAL checkpoint timed out after %.1fs on shutdown",
                    self._WAL_CHECKPOINT_TIMEOUT_S,
                )
            except sqlite3.Error as e:
                errors.append(("wal_checkpoint", f"{type(e).__name__}: {e}"))
                logger.error("Unexpected error during WAL checkpoint: %s", e)
            except Exception as e:
                errors.append(("wal_checkpoint_error", f"{type(e).__name__}: {e}"))
                logger.error("Unexpected error during WAL checkpoint: %s", e)

            if not truncated_or_ok:
                # Copy WAL file to backup location before closing connection
                try:
                    _wal_backup_path, backup_errors = await asyncio.wait_for(
                        loop.run_in_executor(None, self._wal_backup_sync),
                        timeout=self._WAL_BACKUP_TIMEOUT_S,
                    )
                    errors.extend(backup_errors)
                except TimeoutError:
                    errors.append(
                        (
                            "wal_backup_timeout",
                            f"TimeoutError: exceeded {self._WAL_BACKUP_TIMEOUT_S}s",
                        )
                    )
                    logger.error(
                        "WAL backup timed out after %.1fs on shutdown",
                        self._WAL_BACKUP_TIMEOUT_S,
                    )
                except Exception as e:
                    errors.append(("wal_backup_error", f"{type(e).__name__}: {e}"))
                    logger.error("Unexpected error during WAL backup: %s", e)

            # 3. Concurrent Service Shutdown
            svc = self._ctx.services
            if svc is not None:
                shutdown_tasks = []

                # Attempt service lifecycle shutdown
                shutdown_tasks.append(svc.lifecycle.shutdown_all())

                # Attempt HTTP client close
                shutdown_tasks.append(svc.http.aclose())

                results = await asyncio.gather(*shutdown_tasks, return_exceptions=True)
                for i, res in enumerate(results):
                    if isinstance(res, Exception):
                        err_name = "lifecycle_shutdown" if i == 0 else "http_close"
                        errors.append((err_name, f"{type(res).__name__}: {res}"))
                        logger.error("%s failed: %s", err_name, res)
            else:
                logger.debug("No services available to shut down")

        try:
            await asyncio.wait_for(_do_cleanup(), timeout=self._GRACEFUL_TIMEOUT_S)
        except TimeoutError:
            errors.append(
                (
                    "shutdown_timeout",
                    f"TimeoutError: exceeded {self._GRACEFUL_TIMEOUT_S}s",
                )
            )
            logger.error(
                "Shutdown sequence timed out after %.1fs", self._GRACEFUL_TIMEOUT_S
            )
        except Exception as e:
            errors.append(("shutdown_error", f"{type(e).__name__}: {e}"))
            logger.exception("Critical error during shutdown sequence")

        if errors:
            summary = "; ".join(f"{name}: {err}" for name, err in errors)
            logger.error("Resource close errors (%d): %s", len(errors), summary)

    # ── Main REPL loop ─────────────────────────────────────────────────────────

    async def _repl_loop(self) -> None:
        """Process user input lines until /exit, EOF, or shutdown request."""
        ctx = self._ctx
        if self._cmds is None:
            raise RuntimeError("_repl_loop called before _init_components()")
        if self._orchestrator is None:
            raise RuntimeError("_repl_loop called before _init_components()")
        loop = asyncio.get_running_loop()
        while True:
            line = await self._read_input(loop)
            if line is None:
                break
            if not line:
                continue
            if self._should_exit(line, ctx):
                break
            # Warn once about disabled memory
            if ctx.conv.memory_disabled and not ctx.conv.memory_warning_shown:
                ctx.conv.memory_warning_shown = True
                self._view.write_warning(
                    f"{OutputTag.NON_FATAL} Memory is disabled for this session."
                )
            self._turn_active = True
            ctx.conv.is_processing = True
            try:
                dispatch_task = asyncio.ensure_future(self._dispatch_line(line, ctx))
                if (
                    self._shutdown_event is not None
                    and not self._shutdown_event.is_set()
                ):
                    shutdown_task = asyncio.ensure_future(self._shutdown_event.wait())
                    done, pending = await asyncio.wait(
                        {dispatch_task, shutdown_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if dispatch_task in done:
                        dispatch_task.result()  # propagate exception if any
                        continue
                    # shutdown_task completed first — cancel only shutdown_task, keep dispatch_task running
                    assert shutdown_task in pending or shutdown_task in done
                    if shutdown_task in pending:
                        shutdown_task.cancel()
                    try:
                        await asyncio.wait_for(
                            dispatch_task, timeout=self._GRACEFUL_TIMEOUT_S
                        )
                    except TimeoutError:
                        logger.warning(
                            "Graceful shutdown: turn did not complete within %.1fs; forcing exit",
                            self._GRACEFUL_TIMEOUT_S,
                        )
                        break
                else:
                    # _shutdown_event is None or already set — await the already-created dispatch_task
                    try:
                        await asyncio.wait_for(
                            dispatch_task,
                            timeout=self._GRACEFUL_TIMEOUT_S
                            if ctx.conv.shutdown_requested
                            else None,
                        )
                    except TimeoutError:
                        if ctx.conv.shutdown_requested:
                            logger.warning(
                                "Graceful shutdown: turn did not complete within %.1fs; forcing exit",
                                self._GRACEFUL_TIMEOUT_S,
                            )
                            break
                        raise
            except TimeoutError:
                if ctx.conv.shutdown_requested:
                    logger.warning(
                        "Graceful shutdown: turn did not complete within %.1fs; forcing exit",
                        self._GRACEFUL_TIMEOUT_S,
                    )
                    break
                raise
            finally:
                self._turn_active = False
                ctx.conv.is_processing = False
            if ctx.conv.shutdown_requested:
                break

    async def _read_input(self, loop: asyncio.AbstractEventLoop) -> str | None:
        """Read a single input line, handling EOF/keyboard interrupt and multiline continuation."""
        shutdown_event = self._shutdown_event
        if shutdown_event is not None:

            async def _input_task() -> str:
                """Read one line of user input via executor."""
                return await loop.run_in_executor(None, lambda: input(self._prompt))

            input_coro = asyncio.ensure_future(_input_task())
            self._input_coro = input_coro
            shutdown_done = False

            async def _shutdown_watcher() -> None:
                """Wait for shutdown event and signal completion."""
                nonlocal shutdown_done
                await shutdown_event.wait()
                shutdown_done = True

            shutdown_coro = asyncio.ensure_future(_shutdown_watcher())
            try:
                done, pending = await asyncio.wait(
                    {input_coro, shutdown_coro},
                    return_when=asyncio.FIRST_COMPLETED,
                )
            except Exception:
                input_coro.cancel()
                shutdown_coro.cancel()
                raise
            for t in pending:
                t.cancel()
            if shutdown_done or shutdown_coro in done:
                self._view.write_turn_end()
                self._input_coro = None
                return None
            try:
                raw = input_coro.result()
            except asyncio.CancelledError:
                # Input was cancelled by signal handler — treat as shutdown
                self._view.write_turn_end()
                self._input_coro = None
                return None
            except EOFError:
                self._view.write_turn_end()
                self._input_coro = None
                return None
            except KeyboardInterrupt:
                self._view.write_turn_end()
                self._input_coro = None
                return None
        else:
            try:
                raw = await loop.run_in_executor(None, lambda: input(self._prompt))
            except (EOFError, KeyboardInterrupt):
                self._view.write_turn_end()
                return None
        line = raw.strip()
        if line.endswith("\\"):
            line = await self._view.read_multiline(loop, line)
            line = line.strip()
        return line

    def _should_exit(self, line: str, ctx: AgentContext) -> bool:
        """Return True when the REPL loop should terminate."""
        if ctx.conv.shutdown_requested:
            self._view.write_warning("Shutdown requested, exiting...")
            return True
        if line == "/exit":
            return True
        return False

    async def _dispatch_line(self, line: str, ctx: AgentContext) -> None:
        """Dispatch a non-empty, non-exit line to commands or the orchestrator."""
        if self._cmds is None:
            raise RuntimeError("_dispatch_line called before _init_components()")
        if self._orchestrator is None:
            raise RuntimeError("_dispatch_line called before _init_components()")
        if line.startswith("/"):
            matched = await self._cmds.dispatch(line)
            if not matched:
                self._view.write_warning(
                    f"Unknown command: {line}  (type /help for commands)"
                )
        else:
            _prev_partial = ctx.stats.stat_partial_completions
            await self._orchestrator.handle_turn(line)
            if ctx.stats.stat_partial_completions > _prev_partial:
                self._view.write_warning(
                    "Partial LLM completion stored. Use /stats to see count."
                )

    def _get_workflow_status(self) -> str:
        """Return a human-readable workflow status string for the startup banner."""
        if self._orchestrator is None:
            return "unknown"
        status = self._orchestrator.workflow_status()
        if status["tracking"] == "enabled":
            return "enabled"
        return "not loaded"

    def _print_startup_banner(self) -> None:
        """Print the startup line showing DB chunks, tool count, and workflow status."""
        chunk_count = self._get_chunk_count()
        workflow_status = self._get_workflow_status()
        mem_cfg = self._ctx.cfg.memory
        memory_mode = "enabled" if mem_cfg.use_memory_layer else "disabled"
        self._view.write_startup_banner(
            chunk_count,
            self._n_tools,
            workflow_status,
            memory_mode=memory_mode,
        )

    async def _run_repl_loop(self) -> None:
        """Run the main REPL loop."""
        ctx = self._ctx
        try:
            self._print_startup_banner()
            try:
                ctx.session.start()
            except SchemaMissingError as e:
                self._view.write_fatal(str(e))
                raise
            except RuntimeError as e:
                self._view.write_fatal(f"Session start failed: {e}")
                raise
            except sqlite3.Error as e:
                self._view.write_fatal(
                    f"Database unavailable during session start ({e.__class__.__name__}): {e}. Check DB connectivity or run: bash deploy/init_db.sh"
                )
                raise RuntimeError(
                    f"Database unavailable ({e.__class__.__name__}): {e}"
                ) from None
            if (
                ctx.services_required.tools is not None
                and ctx.session.session_id is not None
            ):
                ctx.services_required.tools.set_session_id(str(ctx.session.session_id))
            await self._repl_loop()
        except RuntimeError as e:
            self._view.write_fatal(str(e))
            raise
        finally:
            self._persist_session_diagnostics(ctx)
            await self._persist_session_memories(ctx)
            await self._close_resources()

    async def run(self) -> None:
        """Start the interactive REPL.

        Delegates startup orchestration to StartupOrchestrator (component init,
        MCP server spawning, health checks, security audit, initial prompt setup),
        then enters the main input loop.
        """
        from agent.startup import (
            StartupOrchestrator,  # noqa: PLC0415 — lazy: avoids circular import at module level
        )

        loop = asyncio.get_running_loop()
        self._shutdown_event = asyncio.Event()

        def _sigterm_handler() -> None:
            """Handle SIGTERM by cancelling input and setting shutdown flag.

            Dispatch differs by platform: on Unix this runs via
            loop.add_signal_handler on the event loop thread; on Windows it runs
            via loop.call_soon_threadsafe, scheduled from a console-ctrl handler
            thread. Both paths invoke this same closure.
            """
            self._ctx.conv.shutdown_requested = True
            if self._shutdown_event is not None:
                self._shutdown_event.set()
            # Only cancel the input coroutine when no turn is active: _input_coro
            # tracks the idle input wait, not an in-flight turn. Cancelling it
            # while a turn is active would be a no-op at best; _repl_loop() uses
            # a task-race against _shutdown_event so that _GRACEFUL_TIMEOUT_S
            # seconds after the signal fires (not after the next turn check),
            # the in-flight turn is force-cut off.
            if (
                not self._turn_active
                and self._input_coro is not None
                and not self._input_coro.done()
            ):
                try:
                    self._input_coro.cancel()
                except RuntimeError:
                    pass  # Task already cancelled or not running
            logger.info("SIGTERM received; graceful shutdown initiated")

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, _sigterm_handler)
            except NotImplementedError:
                # asyncio.add_signal_handler is not supported on Windows.
                # Try pywin32 console control handler as fallback.
                try:
                    import sys

                    # Only register if we're running in a console window
                    if hasattr(sys, "frozen"):
                        try:
                            import win32api
                            import win32con

                            def _console_ctrl_handler(ctrl_type: int) -> bool:
                                if ctrl_type == win32con.CTRL_CLOSE_EVENT:
                                    loop.call_soon_threadsafe(_sigterm_handler)
                                return True

                            win32api.SetConsoleCtrlHandler(_console_ctrl_handler, True)
                            logger.debug(
                                "Registered Windows console control handler for %s",
                                sig,
                            )
                        except ImportError:
                            # pywin32 not installed — cannot provide Windows signal handling
                            logger.warning(
                                "pywin32 not available; signal handling disabled on Windows. "
                                "Install pywin32 for Ctrl+C/Ctrl+Break support."
                            )
                        except Exception as e:
                            logger.error(
                                "Failed to set Windows console control handler: %s", e
                            )
                    else:
                        # Not in a console — no signal mechanism available on Windows
                        logger.warning(
                            "Signal handling not available on Windows outside console; "
                            "use Ctrl+C or close the terminal to shut down"
                        )
                except Exception:
                    pass

        startup = StartupOrchestrator(self._ctx, self._view)
        _spawned_subprocesses: list[subprocess.Popen] = []
        try:
            self._cmds, self._orchestrator, _spawned_subprocesses = await startup.run()
        except Exception as e:
            self._view.write_fatal(f"Startup failed: {e}")
            # Terminate any subprocesses started during partial (failed) startup.
            all_procs = _spawned_subprocesses
            if hasattr(startup, "_spawned_subprocesses"):
                all_procs = list(all_procs) + list(startup._spawned_subprocesses)
            for proc in all_procs:
                if proc.poll() is None:
                    proc.terminate()
            raise
        finally:
            await self._close_resources()
        # Show memory disabled warning immediately after startup if applicable
        if self._ctx.conv.memory_disabled and not self._ctx.conv.memory_warning_shown:
            self._ctx.conv.memory_warning_shown = True
            self._view.write_warning(
                f"{OutputTag.NON_FATAL} Memory is disabled for this session."
            )
        await self._run_repl_loop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the interactive REPL."""
    asyncio.run(AgentREPL().run())


if __name__ == "__main__":
    main()
