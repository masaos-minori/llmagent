"""tests/test_mcp_rag_pipeline.py
Regression guards for rag-pipeline-mcp server after /v1/search removal.
"""

from __future__ import annotations

import importlib

# ── Model removal guard ───────────────────────────────────────────────────────


def test_rag_search_models_removed() -> None:
    """RagSearchRequest and RagSearchResponse must not exist in models module."""
    mod = importlib.import_module("mcp.rag_pipeline.models")
    assert not hasattr(mod, "RagSearchRequest"), (
        "RagSearchRequest was re-introduced in mcp.rag_pipeline.models"
    )
    assert not hasattr(mod, "RagSearchResponse"), (
        "RagSearchResponse was re-introduced in mcp.rag_pipeline.models"
    )


# ── Route removal guard ───────────────────────────────────────────────────────


def test_v1_search_route_permanently_removed() -> None:
    """POST /v1/search must not be registered as a FastAPI route."""
    from mcp.rag_pipeline.server import app

    paths = [getattr(r, "path", None) for r in app.routes]
    assert "/v1/search" not in paths, "POST /v1/search must remain removed"


# ── Canonical route present ───────────────────────────────────────────────────


def test_v1_call_tool_route_present() -> None:
    """POST /v1/call_tool must be registered."""
    from mcp.rag_pipeline.server import app

    paths = [getattr(r, "path", None) for r in app.routes]
    assert "/v1/call_tool" in paths, "POST /v1/call_tool must be present"
