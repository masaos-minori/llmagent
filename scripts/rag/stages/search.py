"""Search stage for RAG pipeline."""

from __future__ import annotations

import asyncio
import sqlite3
from typing import TYPE_CHECKING, Any, cast

from shared.types import RagConfig

from rag.repository import RagRepository
from rag.stage import PipelineContext, PipelineStage

if TYPE_CHECKING:
    import httpx
    from db.helper import SQLiteHelper

from shared.logger import Logger

from rag.models_result import SearchDiagnostics
from rag.types import RawHit

logger = Logger(__name__, "/opt/llm/logs/search.log")


async def _search_all_queries(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # noqa: PLC0415 — lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # noqa: PLC0415 — lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(db)
    embed_ok = 0
    embed_failed = 0
    fts_errors = 0
    for q, result in zip(queries, raw):
        if isinstance(result, Exception):
            logger.warning("Embedding failed for '%s': %s", q, result)
            embed_failed += 1
            continue
        if not isinstance(result, list):
            logger.warning("Unexpected embedding type for '%s': %s", q, type(result))
            embed_failed += 1
            continue
        embed_ok += 1
        try:
            vec_res = cast("list[RawHit]", repo.vector_search(result, cfg.top_k_search))
            fts_res = cast("list[RawHit]", repo.fts_search(q, cfg.top_k_search))
            if vec_res:
                all_results.append(vec_res)
            if fts_res:
                all_results.append(fts_res)
        except (sqlite3.OperationalError, RuntimeError) as e:
            logger.warning("Search failed for '%s': %s", q, e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


class SearchStage(PipelineStage):
    def __init__(
        self,
        cfg: RagConfig,
        http: httpx.AsyncClient | None = None,
        embed_url: str = "",
    ) -> None:
        self._cfg = cfg
        self._http = http
        self._embed_url = embed_url

    async def run(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http, self._embed_url
        )
        ctx.search_results = results
        ctx.search_diagnostics = diagnostics
        if diagnostics.embed_failed > 0:
            logger.warning(
                "search degraded: %d/%d queries lacked embedding",
                diagnostics.embed_failed,
                diagnostics.embed_ok + diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )
