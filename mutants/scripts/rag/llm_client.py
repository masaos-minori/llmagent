#!/usr/bin/env python3
"""scripts/rag/llm_client.py

RagLLM class and module-level LLM functions for the RAG pipeline.

Provides:
  RagLLM              — LLM-based query expansion (MQE) and cross-encoder reranking
  get_embedding       — convert text to a float embedding vector
  summarize_tool_result — shorten long tool output for LLM context

Import from here:  from rag.llm_client import RagLLM, get_embedding, summarize_tool_result
"""

from __future__ import annotations

import logging
from typing import Any, cast

import httpx
import orjson
from shared.config_loader import ConfigLoader
from shared.json_utils import (
    dumps as _json_dumps,
)
from shared.json_utils import (
    extract_llm_content,
    parse_http_json,
)
from shared.llm_client import build_embed_url, build_llm_url
from shared.types import (
    LLMMessage,
    RagConfig,
    RagHit,
)

from rag.llm_prompts import (
    _MQE_MAX_TOKENS,
    _MQE_TEMPERATURE,
    _REFINER_PROMPT_TEMPLATE,
    _REFINER_TEMPERATURE,
    _RERANK_MAX_TOKENS,
    _RERANK_TEMPERATURE,
    _SUMMARIZE_INPUT_MAX_CHARS,
    _SUMMARIZE_MAX_TOKENS,
    _SUMMARIZE_PROMPT_TEMPLATE,
    _SUMMARIZE_TEMPERATURE,
    MqeParseError,
    RagExpansionError,
    RagRerankError,
    _apply_rerank_scores,
    _build_rerank_prompt,
    _mqe_prompt,
    _parse_mqe_response,
)

logger = logging.getLogger(__name__)

# Module-level cached llm_url; loaded once and reused across calls.
_llm_url_cache: str | None = None
_embed_url_cache: str | None = None


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x__get_cached_llm_url__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__get_cached_llm_url__mutmut)
def _get_cached_llm_url() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_orig() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_1() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is not None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_2() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = None
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_3() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = None
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_4() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(None)
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_5() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get(None, ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_6() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", None))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_7() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get(""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_8() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_9() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("XXllm_urlXX", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_10() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("LLM_URL", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_11() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", "XXXX"))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_12() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = None
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_13() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = "XXXX"
    assert _llm_url_cache is not None
    return _llm_url_cache


def x__get_cached_llm_url__mutmut_14() -> str:
    """Return the cached llm_url, loading from config on first call."""
    global _llm_url_cache
    if _llm_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _llm_url_cache = build_llm_url(cfg.get("llm_url", ""))
        except (FileNotFoundError, ValueError):
            _llm_url_cache = ""
    assert _llm_url_cache is None
    return _llm_url_cache

mutants_x__get_cached_llm_url__mutmut['_mutmut_orig'] = x__get_cached_llm_url__mutmut_orig # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_1'] = x__get_cached_llm_url__mutmut_1 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_2'] = x__get_cached_llm_url__mutmut_2 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_3'] = x__get_cached_llm_url__mutmut_3 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_4'] = x__get_cached_llm_url__mutmut_4 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_5'] = x__get_cached_llm_url__mutmut_5 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_6'] = x__get_cached_llm_url__mutmut_6 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_7'] = x__get_cached_llm_url__mutmut_7 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_8'] = x__get_cached_llm_url__mutmut_8 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_9'] = x__get_cached_llm_url__mutmut_9 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_10'] = x__get_cached_llm_url__mutmut_10 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_11'] = x__get_cached_llm_url__mutmut_11 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_12'] = x__get_cached_llm_url__mutmut_12 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_13'] = x__get_cached_llm_url__mutmut_13 # type: ignore # mutmut generated
mutants_x__get_cached_llm_url__mutmut['x__get_cached_llm_url__mutmut_14'] = x__get_cached_llm_url__mutmut_14 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__get_cached_embed_url__mutmut)
def _get_cached_embed_url() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_orig() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_1() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is not None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_2() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = None
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_3() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = None
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_4() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(None)
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_5() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get(None, ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_6() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", None))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_7() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get(""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_8() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_9() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("XXembed_urlXX", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_10() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("EMBED_URL", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_11() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", "XXXX"))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_12() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = None
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_13() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = "XXXX"
    assert _embed_url_cache is not None
    return _embed_url_cache


def x__get_cached_embed_url__mutmut_14() -> str:
    """Return the cached embed_url, loading from config on first call."""
    global _embed_url_cache
    if _embed_url_cache is None:
        try:
            cfg = ConfigLoader().load_all()
            _embed_url_cache = build_embed_url(cfg.get("embed_url", ""))
        except (FileNotFoundError, ValueError):
            _embed_url_cache = ""
    assert _embed_url_cache is None
    return _embed_url_cache

mutants_x__get_cached_embed_url__mutmut['_mutmut_orig'] = x__get_cached_embed_url__mutmut_orig # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_1'] = x__get_cached_embed_url__mutmut_1 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_2'] = x__get_cached_embed_url__mutmut_2 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_3'] = x__get_cached_embed_url__mutmut_3 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_4'] = x__get_cached_embed_url__mutmut_4 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_5'] = x__get_cached_embed_url__mutmut_5 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_6'] = x__get_cached_embed_url__mutmut_6 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_7'] = x__get_cached_embed_url__mutmut_7 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_8'] = x__get_cached_embed_url__mutmut_8 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_9'] = x__get_cached_embed_url__mutmut_9 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_10'] = x__get_cached_embed_url__mutmut_10 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_11'] = x__get_cached_embed_url__mutmut_11 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_12'] = x__get_cached_embed_url__mutmut_12 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_13'] = x__get_cached_embed_url__mutmut_13 # type: ignore # mutmut generated
mutants_x__get_cached_embed_url__mutmut['x__get_cached_embed_url__mutmut_14'] = x__get_cached_embed_url__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagLLMǁ_call_llm__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagLLMǁexpand_queries__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagLLMǁsummarize_tool_result__mutmut: MutantDict = {}  # type: ignore
mutants_xǁRagLLMǁrefine_context__mutmut: MutantDict = {}  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# RagLLM class
# ─────────────────────────────────────────────────────────────────────────────


class RagLLM:
    """LLM-based query expansion (MQE) and cross-encoder reranking."""

    @_mutmut_mutated(mutants_xǁRagLLMǁ__init____mutmut)
    def __init__(
        self,
        client: httpx.AsyncClient,
        llm_url: str,
        cfg: RagConfig | None = None,
    ) -> None:
        """Initialize with HTTP client, LLM URL, and optional config mapping."""
        self._client = client
        self._llm_url = llm_url
        self._cfg: RagConfig | dict[str, object] = cfg if cfg is not None else {}

    def xǁRagLLMǁ__init____mutmut_orig(
        self,
        client: httpx.AsyncClient,
        llm_url: str,
        cfg: RagConfig | None = None,
    ) -> None:
        """Initialize with HTTP client, LLM URL, and optional config mapping."""
        self._client = client
        self._llm_url = llm_url
        self._cfg: RagConfig | dict[str, object] = cfg if cfg is not None else {}

    def xǁRagLLMǁ__init____mutmut_1(
        self,
        client: httpx.AsyncClient,
        llm_url: str,
        cfg: RagConfig | None = None,
    ) -> None:
        """Initialize with HTTP client, LLM URL, and optional config mapping."""
        self._client = None
        self._llm_url = llm_url
        self._cfg: RagConfig | dict[str, object] = cfg if cfg is not None else {}

    def xǁRagLLMǁ__init____mutmut_2(
        self,
        client: httpx.AsyncClient,
        llm_url: str,
        cfg: RagConfig | None = None,
    ) -> None:
        """Initialize with HTTP client, LLM URL, and optional config mapping."""
        self._client = client
        self._llm_url = None
        self._cfg: RagConfig | dict[str, object] = cfg if cfg is not None else {}

    def xǁRagLLMǁ__init____mutmut_3(
        self,
        client: httpx.AsyncClient,
        llm_url: str,
        cfg: RagConfig | None = None,
    ) -> None:
        """Initialize with HTTP client, LLM URL, and optional config mapping."""
        self._client = client
        self._llm_url = llm_url
        self._cfg: RagConfig | dict[str, object] = None

    def xǁRagLLMǁ__init____mutmut_4(
        self,
        client: httpx.AsyncClient,
        llm_url: str,
        cfg: RagConfig | None = None,
    ) -> None:
        """Initialize with HTTP client, LLM URL, and optional config mapping."""
        self._client = client
        self._llm_url = llm_url
        self._cfg: RagConfig | dict[str, object] = cfg if cfg is None else {}

    @_mutmut_mutated(mutants_xǁRagLLMǁ_call_llm__mutmut)
    async def _call_llm(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_orig(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_1(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = None
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_2(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            None,
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_3(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json=None,
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_4(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_5(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_6(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "XXmessagesXX": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_7(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "MESSAGES": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_8(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "XXtemperatureXX": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_9(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "TEMPERATURE": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_10(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "temperature": temperature,
                "XXmax_tokensXX": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_11(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "temperature": temperature,
                "MAX_TOKENS": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(resp))
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_12(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = None
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_13(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(None)
        return chat_content

    async def xǁRagLLMǁ_call_llm__mutmut_14(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call the chat LLM endpoint and return the response content string."""
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        chat_content: str = extract_llm_content(parse_http_json(None))
        return chat_content

    @_mutmut_mutated(mutants_xǁRagLLMǁexpand_queries__mutmut)
    async def expand_queries(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_orig(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_1(self, query: str, context: str = "XXXX") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_2(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = None
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_3(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                None,
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_4(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                None,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_5(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                None,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_6(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_7(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_8(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_9(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "XXroleXX": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_10(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "ROLE": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_11(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "XXuserXX",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_12(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "USER",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_13(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "XXcontentXX": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_14(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "CONTENT": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_15(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            None, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_16(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, None, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_17(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, None
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_18(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_19(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_20(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_21(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(None, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_22(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, None)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_23(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_24(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, )
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_25(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = None
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_26(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(None, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_27(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, None)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_28(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_29(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, )
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_30(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = None
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(f"MQE expansion failed: {e}") from e

    async def xǁRagLLMǁexpand_queries__mutmut_31(self, query: str, context: str = "") -> list[str]:
        """Expand query to MQE paraphrases via LLM.

        Raises RagExpansionError on HTTP failure, connection error, or parse failure.
        """
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _mqe_prompt(
                            query, context, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _MQE_TEMPERATURE,
                _MQE_MAX_TOKENS,
            )
            result = _parse_mqe_response(raw, query)
            queries: list[str] = result.queries
            return queries
        except (
            httpx.HTTPStatusError,
            httpx.RequestError,
            orjson.JSONDecodeError,
            MqeParseError,
        ) as e:
            raise RagExpansionError(None) from e

    @_mutmut_mutated(mutants_xǁRagLLMǁcross_encoder_rerank__mutmut)
    async def cross_encoder_rerank(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_orig(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_1(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 1.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_2(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_3(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = None
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_4(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                None,
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_5(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                None,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_6(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                None,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_7(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_8(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_9(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_10(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "XXroleXX": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_11(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "ROLE": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_12(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "XXuserXX",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_13(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "USER",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_14(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "XXcontentXX": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_15(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "CONTENT": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_16(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            None, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_17(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, None, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_18(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, None
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_19(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_20(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_21(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_22(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(None, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_23(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, None)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_24(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_25(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, )
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_26(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(None) from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_27(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = None
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_28(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(None, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_29(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, None, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_30(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, None)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_31(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_32(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_33(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, )
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_34(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is not None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_35(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError(None)
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_36(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("XXCross-encoder rerank: score parse returned no resultXX")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_37(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_38(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("CROSS-ENCODER RERANK: SCORE PARSE RETURNED NO RESULT")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_39(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score >= 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_40(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 1.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_41(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = None
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_42(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) and 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_43(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(None, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_44(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, None, None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_45(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr("rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_46(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_47(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", ) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_48(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "XXrerank_scoreXX", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_49(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "RERANK_SCORE", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_50(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 1.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_51(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) > rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_52(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                None,
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_53(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                None,
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_54(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                None,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_55(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_56(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_57(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_58(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "XXRerank score filter: %s chunks remain (min_score=%s)XX",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_59(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_60(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "RERANK SCORE FILTER: %S CHUNKS REMAIN (MIN_SCORE=%S)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = result
        return reranked

    async def xǁRagLLMǁcross_encoder_rerank__mutmut_61(
        self,
        query: str,
        candidates: list[RagHit],
        top_k: int,
        rag_min_score: float = 0.0,
    ) -> list[RagHit]:
        """Re-rank candidates with a single batch LLM call; drops below rag_min_score.

        Raises RagRerankError on HTTP failure, connection error, or parse failure.
        """
        if not candidates:
            return []
        try:
            raw = await self._call_llm(
                [
                    {
                        "role": "user",
                        "content": _build_rerank_prompt(
                            query, candidates, cast(RagConfig, self._cfg)
                        ),
                    }
                ],
                _RERANK_TEMPERATURE,
                _RERANK_MAX_TOKENS,
            )
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            raise RagRerankError(f"Cross-encoder rerank LLM call failed: {e}") from e
        result = _apply_rerank_scores(raw, candidates, top_k)
        if result is None:
            raise RagRerankError("Cross-encoder rerank: score parse returned no result")
        if rag_min_score > 0.0:
            result = [
                c
                for c in result
                if (getattr(c, "rerank_score", None) or 0.0) >= rag_min_score
            ]
            logger.info(
                "Rerank score filter: %s chunks remain (min_score=%s)",
                len(result),
                rag_min_score,
            )
        reranked: list[Any] = None
        return reranked

    @_mutmut_mutated(mutants_xǁRagLLMǁsummarize_tool_result__mutmut)
    async def summarize_tool_result(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_orig(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_1(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = None
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_2(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = None
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_3(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(None)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_4(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:201]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_5(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = None
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_6(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=None,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_7(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=None,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_8(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=None,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_9(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_10(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_11(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_12(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            None,
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_13(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            None,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_14(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            None,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_15(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_16(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_17(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_18(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"XXroleXX": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_19(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"ROLE": "user", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_20(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "XXuserXX", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_21(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "USER", "content": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_22(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "XXcontentXX": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    async def xǁRagLLMǁsummarize_tool_result__mutmut_23(
        self,
        text: str,
        tool_name: str,
        args: dict[str, object],
    ) -> str:
        """Summarize a long tool result via LLM (3-5 sentences).

        Raises on any HTTP or parse failure — callers decide how to handle.
        """
        text_preview = text[:_SUMMARIZE_INPUT_MAX_CHARS]
        args_str = _json_dumps(args)[:200]
        prompt = _SUMMARIZE_PROMPT_TEMPLATE.format(
            tool_name=tool_name,
            args_str=args_str,
            text_preview=text_preview,
        )
        return await self._call_llm(
            [{"role": "user", "CONTENT": prompt}],
            _SUMMARIZE_TEMPERATURE,
            _SUMMARIZE_MAX_TOKENS,
        )

    @_mutmut_mutated(mutants_xǁRagLLMǁrefine_context__mutmut)
    async def refine_context(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_orig(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_1(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = None
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_2(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(None, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_3(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, None):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_4(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_5(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, ):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_6(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 2):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_7(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = None
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_8(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = None
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_9(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(None)
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_10(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = None
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_11(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(None)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_12(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "XX\n\nXX".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_13(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = None
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_14(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=None, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_15(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=None)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_16(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_17(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, )
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_18(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = None
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_19(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            None,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_20(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json=None,
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_21(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=None,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_22(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_23(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_24(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_25(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "XXmessagesXX": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_26(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "MESSAGES": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_27(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"XXroleXX": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_28(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"ROLE": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_29(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "XXuserXX", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_30(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "USER", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_31(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "XXcontentXX": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_32(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "CONTENT": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_33(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "XXtemperatureXX": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_34(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "TEMPERATURE": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_35(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "XXmax_tokensXX": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_36(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "MAX_TOKENS": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(resp))
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_37(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = None
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_38(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(None)
        return refined_text

    async def xǁRagLLMǁrefine_context__mutmut_39(
        self,
        chunks: list[RagHit],
        query: str,
        max_tokens: int,
        per_chunk_chars: int,
        timeout: float,
    ) -> str:
        """Compress chunks to query-relevant key points via a single LLM call; raises on error so callers can fall back."""
        items = []
        for i, c in enumerate(chunks, 1):
            title = c.title if c.title else c.url
            text = c.content[:per_chunk_chars]
            items.append(f"[{i}] {title}\n{text}")
        items_text = "\n\n".join(items)
        prompt = _REFINER_PROMPT_TEMPLATE.format(query=query, items_text=items_text)
        resp = await self._client.post(
            self._llm_url,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": _REFINER_TEMPERATURE,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        refined_text: str = extract_llm_content(parse_http_json(None))
        return refined_text

mutants_xǁRagLLMǁ__init____mutmut['_mutmut_orig'] = RagLLM.xǁRagLLMǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagLLMǁ__init____mutmut['xǁRagLLMǁ__init____mutmut_1'] = RagLLM.xǁRagLLMǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ__init____mutmut['xǁRagLLMǁ__init____mutmut_2'] = RagLLM.xǁRagLLMǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ__init____mutmut['xǁRagLLMǁ__init____mutmut_3'] = RagLLM.xǁRagLLMǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ__init____mutmut['xǁRagLLMǁ__init____mutmut_4'] = RagLLM.xǁRagLLMǁ__init____mutmut_4 # type: ignore # mutmut generated

mutants_xǁRagLLMǁ_call_llm__mutmut['_mutmut_orig'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_1'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_2'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_3'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_4'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_5'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_6'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_7'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_8'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_9'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_10'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_11'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_12'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_13'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagLLMǁ_call_llm__mutmut['xǁRagLLMǁ_call_llm__mutmut_14'] = RagLLM.xǁRagLLMǁ_call_llm__mutmut_14 # type: ignore # mutmut generated

mutants_xǁRagLLMǁexpand_queries__mutmut['_mutmut_orig'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_1'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_2'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_3'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_4'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_5'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_6'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_7'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_8'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_9'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_10'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_11'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_12'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_13'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_14'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_15'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_16'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_17'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_18'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_19'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_20'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_21'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_22'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_23'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_24'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_25'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_26'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_27'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_28'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_29'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_30'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRagLLMǁexpand_queries__mutmut['xǁRagLLMǁexpand_queries__mutmut_31'] = RagLLM.xǁRagLLMǁexpand_queries__mutmut_31 # type: ignore # mutmut generated

mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['_mutmut_orig'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_1'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_2'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_3'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_4'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_5'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_6'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_7'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_8'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_9'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_10'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_11'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_12'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_13'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_14'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_15'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_16'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_17'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_18'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_19'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_20'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_21'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_22'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_23'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_24'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_25'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_26'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_27'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_28'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_29'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_30'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_31'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_31 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_32'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_32 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_33'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_33 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_34'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_34 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_35'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_35 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_36'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_36 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_37'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_37 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_38'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_38 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_39'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_39 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_40'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_40 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_41'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_41 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_42'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_42 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_43'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_43 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_44'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_44 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_45'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_45 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_46'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_46 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_47'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_47 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_48'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_48 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_49'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_49 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_50'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_50 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_51'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_51 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_52'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_52 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_53'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_53 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_54'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_54 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_55'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_55 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_56'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_56 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_57'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_57 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_58'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_58 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_59'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_59 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_60'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_60 # type: ignore # mutmut generated
mutants_xǁRagLLMǁcross_encoder_rerank__mutmut['xǁRagLLMǁcross_encoder_rerank__mutmut_61'] = RagLLM.xǁRagLLMǁcross_encoder_rerank__mutmut_61 # type: ignore # mutmut generated

mutants_xǁRagLLMǁsummarize_tool_result__mutmut['_mutmut_orig'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_1'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_2'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_3'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_4'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_5'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_6'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_7'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_8'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_9'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_10'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_11'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_12'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_13'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_14'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_15'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_16'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_17'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_18'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_19'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_20'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_21'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_22'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRagLLMǁsummarize_tool_result__mutmut['xǁRagLLMǁsummarize_tool_result__mutmut_23'] = RagLLM.xǁRagLLMǁsummarize_tool_result__mutmut_23 # type: ignore # mutmut generated

mutants_xǁRagLLMǁrefine_context__mutmut['_mutmut_orig'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_orig # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_1'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_1 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_2'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_2 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_3'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_3 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_4'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_4 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_5'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_5 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_6'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_6 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_7'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_7 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_8'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_8 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_9'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_9 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_10'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_10 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_11'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_11 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_12'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_12 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_13'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_13 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_14'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_14 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_15'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_15 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_16'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_16 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_17'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_17 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_18'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_18 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_19'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_19 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_20'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_20 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_21'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_21 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_22'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_22 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_23'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_23 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_24'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_24 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_25'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_25 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_26'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_26 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_27'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_27 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_28'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_28 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_29'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_29 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_30'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_30 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_31'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_31 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_32'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_32 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_33'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_33 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_34'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_34 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_35'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_35 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_36'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_36 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_37'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_37 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_38'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_38 # type: ignore # mutmut generated
mutants_xǁRagLLMǁrefine_context__mutmut['xǁRagLLMǁrefine_context__mutmut_39'] = RagLLM.xǁRagLLMǁrefine_context__mutmut_39 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut: MutantDict = {}  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


@_mutmut_mutated(mutants_x_get_embedding__mutmut)
async def get_embedding(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_orig(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_1(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = None
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_2(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        None,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_3(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json=None,
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_4(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_5(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_6(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"XXcontentXX": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_7(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"CONTENT": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_8(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = None
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_9(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get(None)
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_10(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(None).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_11(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("XXembeddingXX")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_12(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("EMBEDDING")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_13(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) and not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_14(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if isinstance(embedding, list) or not embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_15(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or embedding:
        raise ValueError("missing or empty 'embedding' field in embed response")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_16(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError(None)
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_17(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("XXmissing or empty 'embedding' field in embed responseXX")
    return embedding


# ─────────────────────────────────────────────────────────────────────────────
# Module-level functions (externally imported)
# ─────────────────────────────────────────────────────────────────────────────


async def x_get_embedding__mutmut_18(
    text: str, client: httpx.AsyncClient, embed_url: str
) -> list[float]:
    """Convert text to a float embedding vector."""
    resp = await client.post(
        embed_url,
        json={"content": text},
    )
    resp.raise_for_status()
    embedding = parse_http_json(resp).get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("MISSING OR EMPTY 'EMBEDDING' FIELD IN EMBED RESPONSE")
    return embedding

mutants_x_get_embedding__mutmut['_mutmut_orig'] = x_get_embedding__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_1'] = x_get_embedding__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_2'] = x_get_embedding__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_3'] = x_get_embedding__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_4'] = x_get_embedding__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_5'] = x_get_embedding__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_6'] = x_get_embedding__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_7'] = x_get_embedding__mutmut_7 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_8'] = x_get_embedding__mutmut_8 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_9'] = x_get_embedding__mutmut_9 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_10'] = x_get_embedding__mutmut_10 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_11'] = x_get_embedding__mutmut_11 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_12'] = x_get_embedding__mutmut_12 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_13'] = x_get_embedding__mutmut_13 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_14'] = x_get_embedding__mutmut_14 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_15'] = x_get_embedding__mutmut_15 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_16'] = x_get_embedding__mutmut_16 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_17'] = x_get_embedding__mutmut_17 # type: ignore # mutmut generated
mutants_x_get_embedding__mutmut['x_get_embedding__mutmut_18'] = x_get_embedding__mutmut_18 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_summarize_tool_result__mutmut)
async def summarize_tool_result(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(text, tool_name, args)


async def x_summarize_tool_result__mutmut_orig(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(text, tool_name, args)


async def x_summarize_tool_result__mutmut_1(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is not None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(text, tool_name, args)


async def x_summarize_tool_result__mutmut_2(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = None
    return await RagLLM(client, llm_url).summarize_tool_result(text, tool_name, args)


async def x_summarize_tool_result__mutmut_3(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(None, tool_name, args)


async def x_summarize_tool_result__mutmut_4(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(text, None, args)


async def x_summarize_tool_result__mutmut_5(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(text, tool_name, None)


async def x_summarize_tool_result__mutmut_6(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(tool_name, args)


async def x_summarize_tool_result__mutmut_7(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(text, args)


async def x_summarize_tool_result__mutmut_8(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, llm_url).summarize_tool_result(text, tool_name, )


async def x_summarize_tool_result__mutmut_9(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(None, llm_url).summarize_tool_result(text, tool_name, args)


async def x_summarize_tool_result__mutmut_10(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, None).summarize_tool_result(text, tool_name, args)


async def x_summarize_tool_result__mutmut_11(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(llm_url).summarize_tool_result(text, tool_name, args)


async def x_summarize_tool_result__mutmut_12(
    text: str,
    tool_name: str,
    args: dict[str, object],
    client: httpx.AsyncClient,
    llm_url: str | None = None,
) -> str:
    """Tool result summarization. Delegates to RagLLM.

    llm_url: if None, uses cached config value (loaded once per process).
    Raises on LLM call failure.
    """
    if llm_url is None:
        llm_url = _get_cached_llm_url()
    return await RagLLM(client, ).summarize_tool_result(text, tool_name, args)

mutants_x_summarize_tool_result__mutmut['_mutmut_orig'] = x_summarize_tool_result__mutmut_orig # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_1'] = x_summarize_tool_result__mutmut_1 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_2'] = x_summarize_tool_result__mutmut_2 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_3'] = x_summarize_tool_result__mutmut_3 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_4'] = x_summarize_tool_result__mutmut_4 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_5'] = x_summarize_tool_result__mutmut_5 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_6'] = x_summarize_tool_result__mutmut_6 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_7'] = x_summarize_tool_result__mutmut_7 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_8'] = x_summarize_tool_result__mutmut_8 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_9'] = x_summarize_tool_result__mutmut_9 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_10'] = x_summarize_tool_result__mutmut_10 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_11'] = x_summarize_tool_result__mutmut_11 # type: ignore # mutmut generated
mutants_x_summarize_tool_result__mutmut['x_summarize_tool_result__mutmut_12'] = x_summarize_tool_result__mutmut_12 # type: ignore # mutmut generated


__all__ = [
    "RagHit",
    "RagLLM",
    "get_embedding",
    "summarize_tool_result",
]
