"""scripts/rag/stages/search.py

Search stage for RAG pipeline."""

from __future__ import annotations

import asyncio
import sqlite3
from typing import TYPE_CHECKING, Any, cast

from rag.repository import RagRepository
from rag.stage import PipelineContext, PipelineStage

if TYPE_CHECKING:
    import httpx
    from db.helper import SQLiteHelper

from shared.logger import Logger
from shared.types import RagConfig, RawHit

from rag.models_result import SearchDiagnostics

logger = Logger(__name__, "/opt/llm/logs/search.log")


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__search_all_queries__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__search_all_queries__mutmut)
async def _search_all_queries(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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


async def x__search_all_queries__mutmut_orig(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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


async def x__search_all_queries__mutmut_1(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = None
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


async def x__search_all_queries__mutmut_2(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=None,
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


async def x__search_all_queries__mutmut_3(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
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


async def x__search_all_queries__mutmut_4(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_5(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(None, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_6(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, None, embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_7(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), None) for q in queries),
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


async def x__search_all_queries__mutmut_8(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(cast(_httpx.AsyncClient, http), embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_9(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_10(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), ) for q in queries),
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


async def x__search_all_queries__mutmut_11(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(None, http), embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_12(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, None), embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_13(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(http), embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_14(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, ), embed_url) for q in queries),
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


async def x__search_all_queries__mutmut_15(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=False,
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


async def x__search_all_queries__mutmut_16(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = None
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


async def x__search_all_queries__mutmut_17(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = None
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


async def x__search_all_queries__mutmut_18(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(None)
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


async def x__search_all_queries__mutmut_19(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(db)
    embed_ok = None
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


async def x__search_all_queries__mutmut_20(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(db)
    embed_ok = 1
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


async def x__search_all_queries__mutmut_21(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(db)
    embed_ok = 0
    embed_failed = None
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


async def x__search_all_queries__mutmut_22(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(db)
    embed_ok = 0
    embed_failed = 1
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


async def x__search_all_queries__mutmut_23(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(db)
    embed_ok = 0
    embed_failed = 0
    fts_errors = None
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


async def x__search_all_queries__mutmut_24(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
    )

    raw = await asyncio.gather(
        *(get_embedding(q, cast(_httpx.AsyncClient, http), embed_url) for q in queries),
        return_exceptions=True,
    )
    all_results: list[list[RawHit]] = []
    repo = RagRepository(db)
    embed_ok = 0
    embed_failed = 0
    fts_errors = 1
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


async def x__search_all_queries__mutmut_25(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
    for q, result in zip(None, raw):
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


async def x__search_all_queries__mutmut_26(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
    for q, result in zip(queries, None):
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


async def x__search_all_queries__mutmut_27(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
    for q, result in zip(raw):
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


async def x__search_all_queries__mutmut_28(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
    for q, result in zip(queries, ):
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


async def x__search_all_queries__mutmut_29(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning(None, q, result)
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


async def x__search_all_queries__mutmut_30(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Embedding failed for '%s': %s", None, result)
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


async def x__search_all_queries__mutmut_31(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Embedding failed for '%s': %s", q, None)
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


async def x__search_all_queries__mutmut_32(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning(q, result)
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


async def x__search_all_queries__mutmut_33(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Embedding failed for '%s': %s", result)
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


async def x__search_all_queries__mutmut_34(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Embedding failed for '%s': %s", q, )
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


async def x__search_all_queries__mutmut_35(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("XXEmbedding failed for '%s': %sXX", q, result)
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


async def x__search_all_queries__mutmut_36(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("embedding failed for '%s': %s", q, result)
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


async def x__search_all_queries__mutmut_37(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("EMBEDDING FAILED FOR '%S': %S", q, result)
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


async def x__search_all_queries__mutmut_38(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            embed_failed = 1
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


async def x__search_all_queries__mutmut_39(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            embed_failed -= 1
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


async def x__search_all_queries__mutmut_40(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            embed_failed += 2
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


async def x__search_all_queries__mutmut_41(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            break
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


async def x__search_all_queries__mutmut_42(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        if isinstance(result, list):
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


async def x__search_all_queries__mutmut_43(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning(None, q, type(result))
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


async def x__search_all_queries__mutmut_44(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Unexpected embedding type for '%s': %s", None, type(result))
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


async def x__search_all_queries__mutmut_45(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Unexpected embedding type for '%s': %s", q, None)
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


async def x__search_all_queries__mutmut_46(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning(q, type(result))
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


async def x__search_all_queries__mutmut_47(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Unexpected embedding type for '%s': %s", type(result))
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


async def x__search_all_queries__mutmut_48(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Unexpected embedding type for '%s': %s", q, )
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


async def x__search_all_queries__mutmut_49(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("XXUnexpected embedding type for '%s': %sXX", q, type(result))
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


async def x__search_all_queries__mutmut_50(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("unexpected embedding type for '%s': %s", q, type(result))
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


async def x__search_all_queries__mutmut_51(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("UNEXPECTED EMBEDDING TYPE FOR '%S': %S", q, type(result))
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


async def x__search_all_queries__mutmut_52(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Unexpected embedding type for '%s': %s", q, type(None))
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


async def x__search_all_queries__mutmut_53(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            embed_failed = 1
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


async def x__search_all_queries__mutmut_54(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            embed_failed -= 1
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


async def x__search_all_queries__mutmut_55(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            embed_failed += 2
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


async def x__search_all_queries__mutmut_56(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            break
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


async def x__search_all_queries__mutmut_57(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        embed_ok = 1
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


async def x__search_all_queries__mutmut_58(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        embed_ok -= 1
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


async def x__search_all_queries__mutmut_59(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        embed_ok += 2
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


async def x__search_all_queries__mutmut_60(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = None
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


async def x__search_all_queries__mutmut_61(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast(None, repo.vector_search(result, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_62(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("list[RawHit]", None)
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


async def x__search_all_queries__mutmut_63(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast(repo.vector_search(result, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_64(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("list[RawHit]", )
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


async def x__search_all_queries__mutmut_65(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("XXlist[RawHit]XX", repo.vector_search(result, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_66(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("list[rawhit]", repo.vector_search(result, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_67(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("LIST[RAWHIT]", repo.vector_search(result, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_68(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("list[RawHit]", repo.vector_search(None, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_69(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("list[RawHit]", repo.vector_search(result, None))
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


async def x__search_all_queries__mutmut_70(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("list[RawHit]", repo.vector_search(cfg.top_k_search))
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


async def x__search_all_queries__mutmut_71(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            vec_res = cast("list[RawHit]", repo.vector_search(result, ))
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


async def x__search_all_queries__mutmut_72(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = None
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


async def x__search_all_queries__mutmut_73(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast(None, repo.fts_search(q, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_74(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("list[RawHit]", None)
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


async def x__search_all_queries__mutmut_75(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast(repo.fts_search(q, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_76(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("list[RawHit]", )
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


async def x__search_all_queries__mutmut_77(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("XXlist[RawHit]XX", repo.fts_search(q, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_78(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("list[rawhit]", repo.fts_search(q, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_79(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("LIST[RAWHIT]", repo.fts_search(q, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_80(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("list[RawHit]", repo.fts_search(None, cfg.top_k_search))
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


async def x__search_all_queries__mutmut_81(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("list[RawHit]", repo.fts_search(q, None))
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


async def x__search_all_queries__mutmut_82(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("list[RawHit]", repo.fts_search(cfg.top_k_search))
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


async def x__search_all_queries__mutmut_83(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_res = cast("list[RawHit]", repo.fts_search(q, ))
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


async def x__search_all_queries__mutmut_84(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
                all_results.append(None)
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


async def x__search_all_queries__mutmut_85(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
                all_results.append(None)
        except (sqlite3.OperationalError, RuntimeError) as e:
            logger.warning("Search failed for '%s': %s", q, e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_86(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning(None, q, e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_87(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Search failed for '%s': %s", None, e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_88(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Search failed for '%s': %s", q, None)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_89(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning(q, e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_90(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Search failed for '%s': %s", e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_91(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("Search failed for '%s': %s", q, )
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_92(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("XXSearch failed for '%s': %sXX", q, e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_93(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("search failed for '%s': %s", q, e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_94(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            logger.warning("SEARCH FAILED FOR '%S': %S", q, e)
            fts_errors += 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_95(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_errors = 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_96(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_errors -= 1
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_97(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
            fts_errors += 2
    return all_results, SearchDiagnostics(
        embed_ok=embed_ok,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_98(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        embed_ok=None,
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_99(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        embed_failed=None,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_100(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        fts_errors=None,
    )


async def x__search_all_queries__mutmut_101(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        embed_failed=embed_failed,
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_102(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        fts_errors=fts_errors,
    )


async def x__search_all_queries__mutmut_103(
    queries: list[str],
    db: SQLiteHelper,
    cfg: RagConfig,
    http: httpx.AsyncClient | None,
    embed_url: str,
) -> tuple[list[list[RawHit]], SearchDiagnostics]:
    """Run concurrent embedding fetches then sequential DB searches; sequential DB avoids shared-connection conflicts."""
    import httpx as _httpx  # lazy: avoids circular import at module level

    from rag.llm_client import (
        get_embedding,  # lazy: avoids circular import at module level
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
        )

mutants_x__search_all_queries__mutmut['_mutmut_orig'] = x__search_all_queries__mutmut_orig # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_1'] = x__search_all_queries__mutmut_1 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_2'] = x__search_all_queries__mutmut_2 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_3'] = x__search_all_queries__mutmut_3 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_4'] = x__search_all_queries__mutmut_4 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_5'] = x__search_all_queries__mutmut_5 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_6'] = x__search_all_queries__mutmut_6 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_7'] = x__search_all_queries__mutmut_7 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_8'] = x__search_all_queries__mutmut_8 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_9'] = x__search_all_queries__mutmut_9 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_10'] = x__search_all_queries__mutmut_10 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_11'] = x__search_all_queries__mutmut_11 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_12'] = x__search_all_queries__mutmut_12 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_13'] = x__search_all_queries__mutmut_13 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_14'] = x__search_all_queries__mutmut_14 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_15'] = x__search_all_queries__mutmut_15 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_16'] = x__search_all_queries__mutmut_16 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_17'] = x__search_all_queries__mutmut_17 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_18'] = x__search_all_queries__mutmut_18 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_19'] = x__search_all_queries__mutmut_19 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_20'] = x__search_all_queries__mutmut_20 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_21'] = x__search_all_queries__mutmut_21 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_22'] = x__search_all_queries__mutmut_22 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_23'] = x__search_all_queries__mutmut_23 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_24'] = x__search_all_queries__mutmut_24 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_25'] = x__search_all_queries__mutmut_25 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_26'] = x__search_all_queries__mutmut_26 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_27'] = x__search_all_queries__mutmut_27 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_28'] = x__search_all_queries__mutmut_28 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_29'] = x__search_all_queries__mutmut_29 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_30'] = x__search_all_queries__mutmut_30 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_31'] = x__search_all_queries__mutmut_31 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_32'] = x__search_all_queries__mutmut_32 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_33'] = x__search_all_queries__mutmut_33 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_34'] = x__search_all_queries__mutmut_34 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_35'] = x__search_all_queries__mutmut_35 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_36'] = x__search_all_queries__mutmut_36 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_37'] = x__search_all_queries__mutmut_37 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_38'] = x__search_all_queries__mutmut_38 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_39'] = x__search_all_queries__mutmut_39 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_40'] = x__search_all_queries__mutmut_40 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_41'] = x__search_all_queries__mutmut_41 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_42'] = x__search_all_queries__mutmut_42 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_43'] = x__search_all_queries__mutmut_43 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_44'] = x__search_all_queries__mutmut_44 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_45'] = x__search_all_queries__mutmut_45 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_46'] = x__search_all_queries__mutmut_46 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_47'] = x__search_all_queries__mutmut_47 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_48'] = x__search_all_queries__mutmut_48 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_49'] = x__search_all_queries__mutmut_49 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_50'] = x__search_all_queries__mutmut_50 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_51'] = x__search_all_queries__mutmut_51 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_52'] = x__search_all_queries__mutmut_52 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_53'] = x__search_all_queries__mutmut_53 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_54'] = x__search_all_queries__mutmut_54 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_55'] = x__search_all_queries__mutmut_55 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_56'] = x__search_all_queries__mutmut_56 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_57'] = x__search_all_queries__mutmut_57 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_58'] = x__search_all_queries__mutmut_58 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_59'] = x__search_all_queries__mutmut_59 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_60'] = x__search_all_queries__mutmut_60 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_61'] = x__search_all_queries__mutmut_61 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_62'] = x__search_all_queries__mutmut_62 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_63'] = x__search_all_queries__mutmut_63 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_64'] = x__search_all_queries__mutmut_64 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_65'] = x__search_all_queries__mutmut_65 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_66'] = x__search_all_queries__mutmut_66 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_67'] = x__search_all_queries__mutmut_67 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_68'] = x__search_all_queries__mutmut_68 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_69'] = x__search_all_queries__mutmut_69 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_70'] = x__search_all_queries__mutmut_70 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_71'] = x__search_all_queries__mutmut_71 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_72'] = x__search_all_queries__mutmut_72 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_73'] = x__search_all_queries__mutmut_73 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_74'] = x__search_all_queries__mutmut_74 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_75'] = x__search_all_queries__mutmut_75 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_76'] = x__search_all_queries__mutmut_76 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_77'] = x__search_all_queries__mutmut_77 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_78'] = x__search_all_queries__mutmut_78 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_79'] = x__search_all_queries__mutmut_79 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_80'] = x__search_all_queries__mutmut_80 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_81'] = x__search_all_queries__mutmut_81 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_82'] = x__search_all_queries__mutmut_82 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_83'] = x__search_all_queries__mutmut_83 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_84'] = x__search_all_queries__mutmut_84 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_85'] = x__search_all_queries__mutmut_85 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_86'] = x__search_all_queries__mutmut_86 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_87'] = x__search_all_queries__mutmut_87 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_88'] = x__search_all_queries__mutmut_88 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_89'] = x__search_all_queries__mutmut_89 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_90'] = x__search_all_queries__mutmut_90 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_91'] = x__search_all_queries__mutmut_91 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_92'] = x__search_all_queries__mutmut_92 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_93'] = x__search_all_queries__mutmut_93 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_94'] = x__search_all_queries__mutmut_94 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_95'] = x__search_all_queries__mutmut_95 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_96'] = x__search_all_queries__mutmut_96 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_97'] = x__search_all_queries__mutmut_97 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_98'] = x__search_all_queries__mutmut_98 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_99'] = x__search_all_queries__mutmut_99 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_100'] = x__search_all_queries__mutmut_100 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_101'] = x__search_all_queries__mutmut_101 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_102'] = x__search_all_queries__mutmut_102 # type: ignore # mutmut generated
mutants_x__search_all_queries__mutmut['x__search_all_queries__mutmut_103'] = x__search_all_queries__mutmut_103 # type: ignore # mutmut generated
mutants_xǁSearchStageǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁSearchStageǁrun__mutmut: MutantDict = {}  # type: ignore


class SearchStage(PipelineStage):
    """Semantic + BM25 hybrid search stage across all expanded queries."""

    @_mutmut_mutated(mutants_xǁSearchStageǁ__init____mutmut)
    def __init__(
        self,
        cfg: RagConfig,
        http: httpx.AsyncClient | None = None,
        embed_url: str = "",
    ) -> None:
        """Initialize with RAG config, optional HTTP client, and embedding URL."""
        self._cfg = cfg
        self._http = http
        self._embed_url = embed_url

    def xǁSearchStageǁ__init____mutmut_orig(
        self,
        cfg: RagConfig,
        http: httpx.AsyncClient | None = None,
        embed_url: str = "",
    ) -> None:
        """Initialize with RAG config, optional HTTP client, and embedding URL."""
        self._cfg = cfg
        self._http = http
        self._embed_url = embed_url

    def xǁSearchStageǁ__init____mutmut_1(
        self,
        cfg: RagConfig,
        http: httpx.AsyncClient | None = None,
        embed_url: str = "XXXX",
    ) -> None:
        """Initialize with RAG config, optional HTTP client, and embedding URL."""
        self._cfg = cfg
        self._http = http
        self._embed_url = embed_url

    def xǁSearchStageǁ__init____mutmut_2(
        self,
        cfg: RagConfig,
        http: httpx.AsyncClient | None = None,
        embed_url: str = "",
    ) -> None:
        """Initialize with RAG config, optional HTTP client, and embedding URL."""
        self._cfg = None
        self._http = http
        self._embed_url = embed_url

    def xǁSearchStageǁ__init____mutmut_3(
        self,
        cfg: RagConfig,
        http: httpx.AsyncClient | None = None,
        embed_url: str = "",
    ) -> None:
        """Initialize with RAG config, optional HTTP client, and embedding URL."""
        self._cfg = cfg
        self._http = None
        self._embed_url = embed_url

    def xǁSearchStageǁ__init____mutmut_4(
        self,
        cfg: RagConfig,
        http: httpx.AsyncClient | None = None,
        embed_url: str = "",
    ) -> None:
        """Initialize with RAG config, optional HTTP client, and embedding URL."""
        self._cfg = cfg
        self._http = http
        self._embed_url = None

    @_mutmut_mutated(mutants_xǁSearchStageǁrun__mutmut)
    async def run(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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

    async def xǁSearchStageǁrun__mutmut_orig(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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

    async def xǁSearchStageǁrun__mutmut_1(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is not None:
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

    async def xǁSearchStageǁrun__mutmut_2(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning(None)
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

    async def xǁSearchStageǁrun__mutmut_3(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("XXSearchStage.run: db is None, returning empty resultsXX")
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

    async def xǁSearchStageǁrun__mutmut_4(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("searchstage.run: db is none, returning empty results")
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

    async def xǁSearchStageǁrun__mutmut_5(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SEARCHSTAGE.RUN: DB IS NONE, RETURNING EMPTY RESULTS")
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

    async def xǁSearchStageǁrun__mutmut_6(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = None
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

    async def xǁSearchStageǁrun__mutmut_7(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = None
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

    async def xǁSearchStageǁrun__mutmut_8(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            None, db, self._cfg, self._http, self._embed_url
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

    async def xǁSearchStageǁrun__mutmut_9(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, None, self._cfg, self._http, self._embed_url
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

    async def xǁSearchStageǁrun__mutmut_10(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, None, self._http, self._embed_url
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

    async def xǁSearchStageǁrun__mutmut_11(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, None, self._embed_url
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

    async def xǁSearchStageǁrun__mutmut_12(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http, None
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

    async def xǁSearchStageǁrun__mutmut_13(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            db, self._cfg, self._http, self._embed_url
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

    async def xǁSearchStageǁrun__mutmut_14(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, self._cfg, self._http, self._embed_url
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

    async def xǁSearchStageǁrun__mutmut_15(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._http, self._embed_url
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

    async def xǁSearchStageǁrun__mutmut_16(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._embed_url
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

    async def xǁSearchStageǁrun__mutmut_17(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http, )
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

    async def xǁSearchStageǁrun__mutmut_18(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http, self._embed_url
        )
        ctx.search_results = None
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

    async def xǁSearchStageǁrun__mutmut_19(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http, self._embed_url
        )
        ctx.search_results = results
        ctx.search_diagnostics = None
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

    async def xǁSearchStageǁrun__mutmut_20(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http, self._embed_url
        )
        ctx.search_results = results
        ctx.search_diagnostics = diagnostics
        if diagnostics.embed_failed >= 0:
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

    async def xǁSearchStageǁrun__mutmut_21(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
        if db is None:
            logger.warning("SearchStage.run: db is None, returning empty results")
            ctx.search_results = []
            return
        results, diagnostics = await _search_all_queries(
            ctx.queries, db, self._cfg, self._http, self._embed_url
        )
        ctx.search_results = results
        ctx.search_diagnostics = diagnostics
        if diagnostics.embed_failed > 1:
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

    async def xǁSearchStageǁrun__mutmut_22(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                None,
                diagnostics.embed_failed,
                diagnostics.embed_ok + diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_23(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                None,
                diagnostics.embed_ok + diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_24(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                None,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_25(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                diagnostics.embed_failed,
                diagnostics.embed_ok + diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_26(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                diagnostics.embed_ok + diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_27(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_28(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                "XXsearch degraded: %d/%d queries lacked embeddingXX",
                diagnostics.embed_failed,
                diagnostics.embed_ok + diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_29(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                "SEARCH DEGRADED: %D/%D QUERIES LACKED EMBEDDING",
                diagnostics.embed_failed,
                diagnostics.embed_ok + diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_30(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                diagnostics.embed_ok - diagnostics.embed_failed,
            )
        if diagnostics.fts_errors > 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_31(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
        if diagnostics.fts_errors >= 0:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_32(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
        if diagnostics.fts_errors > 1:
            logger.warning(
                "search degraded: %d FTS/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_33(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                None,
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_34(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                None,
            )

    async def xǁSearchStageǁrun__mutmut_35(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_36(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                )

    async def xǁSearchStageǁrun__mutmut_37(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                "XXsearch degraded: %d FTS/vec errorsXX",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_38(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                "search degraded: %d fts/vec errors",
                diagnostics.fts_errors,
            )

    async def xǁSearchStageǁrun__mutmut_39(
        self, ctx: PipelineContext, db: SQLiteHelper | None = None, **kwargs: Any
    ) -> None:
        """Execute hybrid search for all queries and store results in context."""
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
                "SEARCH DEGRADED: %D FTS/VEC ERRORS",
                diagnostics.fts_errors,
            )

mutants_xǁSearchStageǁ__init____mutmut['_mutmut_orig'] = SearchStage.xǁSearchStageǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁSearchStageǁ__init____mutmut['xǁSearchStageǁ__init____mutmut_1'] = SearchStage.xǁSearchStageǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁSearchStageǁ__init____mutmut['xǁSearchStageǁ__init____mutmut_2'] = SearchStage.xǁSearchStageǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁSearchStageǁ__init____mutmut['xǁSearchStageǁ__init____mutmut_3'] = SearchStage.xǁSearchStageǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁSearchStageǁ__init____mutmut['xǁSearchStageǁ__init____mutmut_4'] = SearchStage.xǁSearchStageǁ__init____mutmut_4 # type: ignore # mutmut generated

mutants_xǁSearchStageǁrun__mutmut['_mutmut_orig'] = SearchStage.xǁSearchStageǁrun__mutmut_orig # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_1'] = SearchStage.xǁSearchStageǁrun__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_2'] = SearchStage.xǁSearchStageǁrun__mutmut_2 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_3'] = SearchStage.xǁSearchStageǁrun__mutmut_3 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_4'] = SearchStage.xǁSearchStageǁrun__mutmut_4 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_5'] = SearchStage.xǁSearchStageǁrun__mutmut_5 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_6'] = SearchStage.xǁSearchStageǁrun__mutmut_6 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_7'] = SearchStage.xǁSearchStageǁrun__mutmut_7 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_8'] = SearchStage.xǁSearchStageǁrun__mutmut_8 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_9'] = SearchStage.xǁSearchStageǁrun__mutmut_9 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_10'] = SearchStage.xǁSearchStageǁrun__mutmut_10 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_11'] = SearchStage.xǁSearchStageǁrun__mutmut_11 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_12'] = SearchStage.xǁSearchStageǁrun__mutmut_12 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_13'] = SearchStage.xǁSearchStageǁrun__mutmut_13 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_14'] = SearchStage.xǁSearchStageǁrun__mutmut_14 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_15'] = SearchStage.xǁSearchStageǁrun__mutmut_15 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_16'] = SearchStage.xǁSearchStageǁrun__mutmut_16 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_17'] = SearchStage.xǁSearchStageǁrun__mutmut_17 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_18'] = SearchStage.xǁSearchStageǁrun__mutmut_18 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_19'] = SearchStage.xǁSearchStageǁrun__mutmut_19 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_20'] = SearchStage.xǁSearchStageǁrun__mutmut_20 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_21'] = SearchStage.xǁSearchStageǁrun__mutmut_21 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_22'] = SearchStage.xǁSearchStageǁrun__mutmut_22 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_23'] = SearchStage.xǁSearchStageǁrun__mutmut_23 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_24'] = SearchStage.xǁSearchStageǁrun__mutmut_24 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_25'] = SearchStage.xǁSearchStageǁrun__mutmut_25 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_26'] = SearchStage.xǁSearchStageǁrun__mutmut_26 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_27'] = SearchStage.xǁSearchStageǁrun__mutmut_27 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_28'] = SearchStage.xǁSearchStageǁrun__mutmut_28 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_29'] = SearchStage.xǁSearchStageǁrun__mutmut_29 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_30'] = SearchStage.xǁSearchStageǁrun__mutmut_30 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_31'] = SearchStage.xǁSearchStageǁrun__mutmut_31 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_32'] = SearchStage.xǁSearchStageǁrun__mutmut_32 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_33'] = SearchStage.xǁSearchStageǁrun__mutmut_33 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_34'] = SearchStage.xǁSearchStageǁrun__mutmut_34 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_35'] = SearchStage.xǁSearchStageǁrun__mutmut_35 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_36'] = SearchStage.xǁSearchStageǁrun__mutmut_36 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_37'] = SearchStage.xǁSearchStageǁrun__mutmut_37 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_38'] = SearchStage.xǁSearchStageǁrun__mutmut_38 # type: ignore # mutmut generated
mutants_xǁSearchStageǁrun__mutmut['xǁSearchStageǁrun__mutmut_39'] = SearchStage.xǁSearchStageǁrun__mutmut_39 # type: ignore # mutmut generated
