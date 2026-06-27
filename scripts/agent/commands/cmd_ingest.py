#!/usr/bin/env python3
"""agent/commands/cmd_ingest.py
Export, ingest, and compact mixin for CommandRegistry.

Provides _IngestMixin with:
  _cmd_export            — /export: dump conversation to Markdown or JSON
  _cmd_ingest            — /ingest: crawl/ingest a URL or local file
  _cmd_compact           — /compact: force immediate context compression
  _cmd_rag               — /rag: search the RAG knowledge base
"""

import logging

import orjson
from mcp.rag_pipeline.models import RagPipelineConfig, build_rag_cfg_adapter

from agent.commands.mixin_base import MixinBase
from agent.history import HistoryCompressionError
from agent.services.export_formatter import render_export, write_export

logger = logging.getLogger(__name__)

RAG_SEARCH_PARTS_COUNT = 2


class _IngestMixin(MixinBase):
    """Export, ingest, and compact slash-command handlers."""

    def _cmd_export(self, args: str) -> None:
        """Export the current conversation history to Markdown or JSON.

        Usage: /export [md|json] [filename]
        """
        ctx = self._ctx
        parts = args.strip().split()
        fmt = "md"
        outfile: str | None = None
        for part in parts:
            if part in ("md", "json"):
                fmt = part
            else:
                outfile = part
        content = render_export(ctx.conv.history, fmt)
        write_export(content, outfile, len(ctx.conv.history))

    async def _cmd_ingest(self, args: str) -> None:
        """Crawl/ingest a URL or local file into the RAG DB from within the REPL.

        Usage: /ingest <url|path> [ja|en] [--snippets-only]
        --snippets-only forces heading-based Markdown snippet chunking.
        """
        from agent.services.exceptions import (
            IngestStageError,  # noqa: PLC0415 — lazy: deferred to avoid import cost
        )
        from agent.services.ingest_workflow import (
            IngestWorkflowService,  # noqa: PLC0415 — lazy: heavy ingest pipeline deferred to /ingest call
        )

        parts = args.strip().split()
        if not parts:
            self._out.write("Usage: /ingest <url|path> [lang=ja|en] [--snippets-only]")
            return
        target = parts[0]
        lang = "ja"
        snippets_only = False
        for p in parts[1:]:
            if p in ("ja", "en"):
                lang = p
            elif p == "--snippets-only":
                snippets_only = True

        def on_status(msg: str) -> None:
            self._out.write(f"  {msg}")

        # Build a temporary pipeline to get the semantic cache for invalidation
        cache = None
        if self._ctx.services is not None and self._ctx.services.http is not None:
            from rag.pipeline import (  # noqa: PLC0415 — lazy: heavy RAG module deferred
                RagPipeline,
            )
            from shared.config_loader import ConfigLoader  # noqa: PLC0415 — lazy

            rag_cfg_dict = ConfigLoader().load_all()
            if rag_cfg_dict.get("use_search", True):
                rag_cfg = build_rag_cfg_adapter(
                    RagPipelineConfig.from_dict(rag_cfg_dict)
                )
                temp_pipeline = RagPipeline(self._ctx.services.http, rag_cfg)
                cache = temp_pipeline.semantic_cache

        svc = IngestWorkflowService()
        try:
            await svc.run(
                target,
                lang=lang,
                snippets_only=snippets_only,
                on_status=on_status,
                on_ingest_complete=(
                    lambda: cache.invalidate() if cache is not None else None
                ),
            )
        except IngestStageError as e:
            logger.error("Ingest failed at stage=%s: %s", e.stage, e.detail)
            self._out.write(f"  [ingest] error ({e.stage}): {e.detail}")

    async def _cmd_rag(self, args: str) -> None:
        """Search the RAG knowledge base with a query.

        Usage:
          /rag search <query>           Run RAG search and print context
          /rag search <query> --debug   Also print per-stage latency
        """
        from rag.pipeline import (
            RagPipeline,  # noqa: PLC0415 — lazy: heavy RAG module deferred to /rag call
        )
        from shared.config_loader import (
            ConfigLoader,  # noqa: PLC0415 — lazy: deferred to /rag call
        )

        ctx = self._ctx
        parts = args.strip().split(None, 1)
        sub = parts[0] if parts else ""
        if sub != "search" or len(parts) < RAG_SEARCH_PARTS_COUNT:
            self._out.write("Usage: /rag search <query> [--debug]")
            return

        remainder = parts[1]
        debug = "--debug" in remainder
        query = remainder.replace("--debug", "").strip()
        if not query:
            self._out.write("Usage: /rag search <query> [--debug]")
            return

        if ctx.services is None or ctx.services.http is None:
            self._out.write("HTTP client not available.")
            return

        rag_cfg_dict = ConfigLoader().load_all()

        if not rag_cfg_dict.get("use_search", True):
            self._out.write("RAG search is disabled (use_search=false in config).")
            return

        rag_cfg = build_rag_cfg_adapter(RagPipelineConfig.from_dict(rag_cfg_dict))
        pipeline = RagPipeline(ctx.services.http, rag_cfg)

        debug_fn = None
        if debug:

            def debug_fn(
                queries: list,
                all_results: list,
                merged: list,
                reranked: list,
                rrf_config: dict | None = None,
            ) -> None:
                self._out.write_debug_rag(
                    {
                        "queries": queries,
                        "all_results": all_results,
                        "merged": [dict(c) for c in merged],
                        "reranked": [dict(c) for c in reranked],
                        "rrf_config": rrf_config or {},
                    }
                )

        context = await pipeline.augment(query, debug_fn=debug_fn)

        # Check search degradation after augment() returns
        diag = pipeline.last_search_diagnostics
        search_degraded = diag.embed_failed > 0 or diag.fts_errors > 0

        if debug and diag.result_source.value == "remote":
            kind = diag.http_result_kind.value
            kind_label = (
                "success (empty response — no in-process fallback)"
                if kind == "empty"
                else kind
            )
            self._out.write(
                f"[debug] http mode: result_source=remote http_result_kind={kind_label}"
            )

        if not context:
            if search_degraded:
                parts = []
                if diag.embed_failed > 0:
                    parts.append(f"embed_failed={diag.embed_failed}")
                if diag.fts_errors > 0:
                    parts.append(f"fts_errors={diag.fts_errors}")
                self._out.write(
                    f"No results found [warn: search degraded — {', '.join(parts)}]"
                )
            else:
                self._out.write("No results found.")
        else:
            self._out.write(context)

        refiner_fb = next(
            (
                sr
                for sr in pipeline.last_stage_results
                if sr["stage_name"] == "Refiner" and sr["status"] == "fallback"
            ),
            None,
        )
        if refiner_fb:
            self._out.write(
                f"[warn] refiner fallback: {refiner_fb['fallback_reason']}"
                " — raw chunks used (run with --debug for stage details)"
            )

        if search_degraded:
            parts = []
            if diag.embed_failed > 0:
                parts.append(f"embed_failed={diag.embed_failed}")
            if diag.fts_errors > 0:
                parts.append(f"fts_errors={diag.fts_errors}")
            self._out.write(
                f"[warn] search degraded: {', '.join(parts)}"
                " — results may be incomplete (FTS-only fallback)"
            )

        if debug:
            self._print_rag_debug(pipeline.last_timings, pipeline.last_stage_results)
            _debug_diag = pipeline.get_diagnostics()
            rfc = _debug_diag.get("refiner_fallback_count", 0)
            if rfc > 0:
                rec = _debug_diag.get("refiner_exception_count", 0)
                reasons = [
                    r["fallback_reason"]
                    for r in pipeline.last_stage_results
                    if r.get("stage_name") == "Refiner"
                    and r.get("status") == "fallback"
                ]
                reason_str = ", ".join(str(r) for r in reasons if r)
                exc_note = f" ({rec} exception(s))" if rec > 0 else ""
                self._out.write(
                    f"[refiner] fallback: {rfc} time(s){exc_note}"
                    + (f" — {reason_str}" if reason_str else "")
                )

        if ctx.diagnostics is not None:
            try:
                diag_data: dict = pipeline.get_diagnostics()
                diag_data["query"] = query
                ctx.diagnostics.save(
                    ctx.session.session_id,
                    kind="rag_query",
                    content=orjson.dumps(diag_data).decode(),
                )
            except Exception:  # noqa: BLE001 — diagnostics must not crash the command
                logger.debug("Failed to persist RAG query diagnostics", exc_info=True)

    def _print_rag_debug(
        self,
        timings: dict[str, float],
        stage_results: list | None = None,
    ) -> None:
        """Print per-stage wall-clock timings and stage results from a RAG pipeline run."""
        if not timings:
            return
        self._out.write("\n--- Stage timings ---")
        for stage_name, elapsed in timings.items():
            self._out.write(f"  {stage_name}: {elapsed * 1000:.1f} ms")
        if stage_results:
            self._out.write("\n--- Stage results ---")
            _icons = {"success": "✓", "fallback": "~", "failure": "✗"}
            for sr in stage_results:
                icon = _icons.get(sr["status"], "?")
                line = (
                    f"  {icon} {sr['stage_name']}: {sr['status']}"
                    f" ({sr['elapsed_seconds'] * 1000:.1f} ms)"
                )
                if sr.get("fallback_reason"):
                    line += f" — {sr['fallback_reason']}"
                self._out.write(line)

    async def _cmd_compact(self) -> None:
        """Force immediate compression of conversation history.

        Bypasses the context_char_limit threshold and compresses the oldest
        context_compress_turns pairs unconditionally.
        """
        ctx = self._ctx
        if ctx.services.hist_mgr is None:
            self._out.write("History manager not available.")
            return
        turn_msgs = [m for m in ctx.conv.history if m["role"] != "system"]
        # compress_turns * 2: each "turn" = 1 user + 1 assistant message
        n_compress = ctx.services.hist_mgr.compress_turns * 2
        if len(turn_msgs) <= n_compress:
            self._out.write("Nothing to compact: history too short.")
            return
        try:
            ctx.conv.history = await ctx.services.hist_mgr.force_compress(
                ctx.conv.history
            )
        except HistoryCompressionError as e:
            self._out.write_error(f"Compression failed: {e}")
            return
