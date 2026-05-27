#!/usr/bin/env python3
"""
rag_mcp_server.py
外部 RAG HTTP サービス (port 8010)。
agent_rag.py の augment() が rag_service_url 設定時に呼び出すバックエンド。

エンドポイント:
  POST /v1/search  {"query": str, "history_context": str} -> {"context": str}
  GET  /health     -> {"status": "ok"}
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from agent_config import build_agent_config
from agent_rag import RagPipeline
from config_loader import ConfigLoader
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# サービス全体で共有する RagPipeline と httpx クライアント
_http: httpx.AsyncClient | None = None
_rag: RagPipeline | None = None


def _load_base_cfg() -> dict:
    """config/agent.json + config/common.json をマージして返す。"""
    try:
        return ConfigLoader().load("common.json", "agent.json")
    except Exception as e:
        logger.warning(f"Config load failed: {e}")
        return {}


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    global _http, _rag
    # Disable rag_service_url to force in-process execution and prevent HTTP loop
    base_cfg = _load_base_cfg()
    base_cfg["rag_service_url"] = ""
    cfg = build_agent_config(base_cfg)
    _http = httpx.AsyncClient(timeout=cfg.http_timeout)
    _rag = RagPipeline(_http, cfg)
    logger.info("rag-mcp: RagPipeline initialized (in-process mode)")
    yield
    if _http is not None:
        await _http.aclose()
    logger.info("rag-mcp: shutdown complete")


app = FastAPI(title="rag-mcp", version="1.0", lifespan=_lifespan)


class SearchRequest(BaseModel):
    query: str
    history_context: str = ""


class SearchResponse(BaseModel):
    context: str


@app.post("/v1/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """Run the RAG pipeline and return the formatted context string."""
    if _rag is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    context = await _rag.augment(req.query, history_context=req.history_context)
    return SearchResponse(context=context)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("rag_mcp_server:app", host="127.0.0.1", port=8010, workers=1)
