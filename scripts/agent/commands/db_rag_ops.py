"""db_rag_ops.py — RAG database operation handlers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.commands.mixin_base import MixinBase

from agent.commands.utils import parse_command_args, parse_flag_int
from agent.services.rag_maintenance_service import RagMaintenanceService

logger = logging.getLogger(__name__)


class DbRagOps:
    """Handles RAG database operations: clean, list_urls, rebuild_fts, vec_rebuild, reconcile_url, recover, consistency."""

    def __init__(self, ctx: Any, out: Any) -> None:
        self._ctx = ctx
        self._out = out

    async def clean(self, rest: str) -> None:
        """Delete a document by URL from the vector store via rag-pipeline-mcp."""
        url = rest.strip()
        if not url:
            self._out.write_validation_error("/db rag clean <url>")
            return
        if self._ctx.services_required.tools is None:
            self._out.write_error(
                "rag-pipeline-mcp unavailable: tool executor not initialized"
            )
            return
        try:
            result = await self._ctx.services_required.tools.execute(
                "rag_delete_document", {"url": url}
            )
            if result.is_error:
                self._out.write_error(result.output)
            else:
                self._out.write(result.output)
        except Exception as e:  # noqa: BLE001
            self._out.write_error(f"rag-pipeline-mcp unavailable: {e}")

    async def list_urls(self, rest: str) -> None:
        """List indexed documents via rag-pipeline-mcp."""
        tokens = rest.split()
        parsed = parse_command_args(tokens)
        lang_raw = parsed.flags.get("lang")
        lang: str | None = str(lang_raw) if lang_raw in ("ja", "en") else None
        limit = parse_flag_int(tokens, "--limit") or 20
        args_dict: dict[str, Any] = {"limit": limit}
        if lang:
            args_dict["lang"] = lang
        if self._ctx.services_required.tools is None:
            self._out.write_error(
                "rag-pipeline-mcp unavailable: tool executor not initialized"
            )
            return
        try:
            result = await self._ctx.services_required.tools.execute(
                "rag_list_documents", args_dict
            )
            if result.is_error:
                self._out.write_error(result.output)
            else:
                self._out.write(result.output)
        except Exception as e:  # noqa: BLE001
            self._out.write_error(f"rag-pipeline-mcp unavailable: {e}")

    def rebuild_fts(self) -> None:
        """Rebuild the RAG full-text search index."""
        RagMaintenanceService().rebuild_fts()
        self._out.write_success("FTS5 index rebuilt [RAG]")

    def vec_rebuild(self) -> None:
        """Rebuild the vector index from chunks."""
        count = RagMaintenanceService().rebuild_vec()
        self._out.write_success(f"Vec index rebuilt: {count} rows [RAG]")

    def reconcile_url(self, rest: str) -> None:
        """Rebuild FTS/vec for a single URL."""
        url = rest.strip()
        if not url:
            self._out.write_validation_error("Usage: /db rag reconcile-url <url>")
            return
        result = RagMaintenanceService().reconcile_url(url)
        if not result["found"]:
            self._out.write_error(f"URL not found: {url}")
        else:
            self._out.write_success(
                f"Reconciled {result['chunks']} chunks for {url} [RAG]"
            )

    def recover(self, backup_path: str | None) -> None:
        """Run integrity check; restore from backup_path if corruption found."""
        result = RagMaintenanceService().recover(backup_path)
        if result.integrity_ok:
            self._out.write_success(f"Recovery succeeded: {result.detail} [RAG]")
        else:
            self._out.write_no_data(f"Recovery failed: {result.detail} [RAG]")

    def consistency(self) -> None:
        """Run RAG search index synchronization check."""
        try:
            result = RagMaintenanceService().consistency()
            numeric_line = (
                f"  chunks: {result.report.chunks}  fts: {result.report.fts}  vec: {result.report.vec}"
                f"  fts_gap: {result.report.fts_gap}  orphan_vec: {result.report.orphan_vec_count}"
                f"  fts_orphan: {result.report.fts_orphan_count}"
            )
            if result.is_consistent:
                self._out.write_success(
                    f"{numeric_line}\nRAG consistency: OK (chunks/FTS/vec in sync)"
                )
            else:
                self._out.write(f"{numeric_line}\nRAG consistency: FAIL")
                for issue in result.issues:
                    self._out.write_error(f"Consistency issue: {issue}")
        except Exception as e:  # noqa: BLE001 — skip if rag.sqlite absent or unreadable
            logger.debug("RAG consistency check skipped: %s", e)
