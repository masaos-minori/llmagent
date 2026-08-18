#!/usr/bin/env python3
"""scripts/rag/ingestion/pipeline_utils.py

Shared I/O utilities for the RAG ingestion pipeline.
"""

from pathlib import Path
from typing import NotRequired, TypedDict, cast

import orjson
from rag.exceptions import ChunkFormatError
from rag.models_data import ChunkDocument
from rag.models_result import SkipInfo
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/pipeline.log")


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


class ChunkJsonRaw(TypedDict):
    """Typed dict for raw chunk/crawl JSON payload fields."""

    url: str
    content: str
    title: NotRequired[str]
    lang: NotRequired[str]
    code_blocks: NotRequired[list[str]]
    etag: NotRequired[str | None]
    last_modified: NotRequired[str | None]
    fetched_at: NotRequired[str | None]
    chunking_strategy: NotRequired[str]
    normalized_content: NotRequired[str | None]
    chunk_index: NotRequired[int]
    source_file: NotRequired[str]
    chunk_type: NotRequired[str]
    artifact_type: NotRequired[
        str
    ]  # ingestion-pipeline metadata only; not persisted to DB
    schema_version: NotRequired[str]
    created_by: NotRequired[str]
mutants_x__read_chunk_json_raw__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__read_chunk_json_raw__mutmut)
def _read_chunk_json_raw(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_orig(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_1(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = None
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_2(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning(None, path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_3(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", None, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_4(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, None)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_5(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning(path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_6(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_7(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, )
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_8(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("XXskip chunk %s: %sXX", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_9(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("SKIP CHUNK %S: %S", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_10(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = None
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_11(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(None)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_12(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning(None, path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_13(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", None, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_14(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, None)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_15(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning(path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_16(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_17(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, )
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_18(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("XXskip chunk %s: JSON parse error: %sXX", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_19(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: json parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_20(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("SKIP CHUNK %S: JSON PARSE ERROR: %S", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_21(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_22(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            None,
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_23(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            None,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_24(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            None,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_25(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_26(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_27(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_28(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "XXskip chunk %s: expected JSON object, got %sXX",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_29(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected json object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_30(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "SKIP CHUNK %S: EXPECTED JSON OBJECT, GOT %S",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_31(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(None).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_32(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = None
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_33(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get(None)
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_34(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("XXurlXX")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_35(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("URL")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_36(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = None
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_37(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get(None)
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_38(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("XXcontentXX")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_39(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("CONTENT")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_40(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) and not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_41(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_42(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_43(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning(None, path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_44(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", None)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_45(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning(path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_46(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", )
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_47(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("XXskip chunk %s: missing or invalid 'url'XX", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_48(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("SKIP CHUNK %S: MISSING OR INVALID 'URL'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_49(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) and not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_50(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_51(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_52(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning(None, path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_53(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", None)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_54(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning(path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_55(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", )
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_56(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("XXskip chunk %s: missing or invalid 'content'XX", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_57(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("SKIP CHUNK %S: MISSING OR INVALID 'CONTENT'", path.name)
        return None
    return cast(ChunkJsonRaw, data)


def x__read_chunk_json_raw__mutmut_58(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(None, data)


def x__read_chunk_json_raw__mutmut_59(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, None)


def x__read_chunk_json_raw__mutmut_60(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(data)


def x__read_chunk_json_raw__mutmut_61(path: Path) -> ChunkJsonRaw | None:
    """Read and parse a chunk JSON file as a raw dict; returns None on any failure."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        logger.warning("skip chunk %s: %s", path.name, e)
        return None
    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError as e:
        logger.warning("skip chunk %s: JSON parse error: %s", path.name, e)
        return None
    if not isinstance(data, dict):
        logger.warning(
            "skip chunk %s: expected JSON object, got %s",
            path.name,
            type(data).__name__,
        )
        return None
    url = data.get("url")
    content = data.get("content")
    if not isinstance(url, str) or not url:
        logger.warning("skip chunk %s: missing or invalid 'url'", path.name)
        return None
    if not isinstance(content, str) or not content:
        logger.warning("skip chunk %s: missing or invalid 'content'", path.name)
        return None
    return cast(ChunkJsonRaw, )

mutants_x__read_chunk_json_raw__mutmut['_mutmut_orig'] = x__read_chunk_json_raw__mutmut_orig # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_1'] = x__read_chunk_json_raw__mutmut_1 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_2'] = x__read_chunk_json_raw__mutmut_2 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_3'] = x__read_chunk_json_raw__mutmut_3 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_4'] = x__read_chunk_json_raw__mutmut_4 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_5'] = x__read_chunk_json_raw__mutmut_5 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_6'] = x__read_chunk_json_raw__mutmut_6 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_7'] = x__read_chunk_json_raw__mutmut_7 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_8'] = x__read_chunk_json_raw__mutmut_8 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_9'] = x__read_chunk_json_raw__mutmut_9 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_10'] = x__read_chunk_json_raw__mutmut_10 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_11'] = x__read_chunk_json_raw__mutmut_11 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_12'] = x__read_chunk_json_raw__mutmut_12 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_13'] = x__read_chunk_json_raw__mutmut_13 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_14'] = x__read_chunk_json_raw__mutmut_14 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_15'] = x__read_chunk_json_raw__mutmut_15 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_16'] = x__read_chunk_json_raw__mutmut_16 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_17'] = x__read_chunk_json_raw__mutmut_17 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_18'] = x__read_chunk_json_raw__mutmut_18 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_19'] = x__read_chunk_json_raw__mutmut_19 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_20'] = x__read_chunk_json_raw__mutmut_20 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_21'] = x__read_chunk_json_raw__mutmut_21 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_22'] = x__read_chunk_json_raw__mutmut_22 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_23'] = x__read_chunk_json_raw__mutmut_23 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_24'] = x__read_chunk_json_raw__mutmut_24 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_25'] = x__read_chunk_json_raw__mutmut_25 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_26'] = x__read_chunk_json_raw__mutmut_26 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_27'] = x__read_chunk_json_raw__mutmut_27 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_28'] = x__read_chunk_json_raw__mutmut_28 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_29'] = x__read_chunk_json_raw__mutmut_29 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_30'] = x__read_chunk_json_raw__mutmut_30 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_31'] = x__read_chunk_json_raw__mutmut_31 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_32'] = x__read_chunk_json_raw__mutmut_32 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_33'] = x__read_chunk_json_raw__mutmut_33 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_34'] = x__read_chunk_json_raw__mutmut_34 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_35'] = x__read_chunk_json_raw__mutmut_35 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_36'] = x__read_chunk_json_raw__mutmut_36 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_37'] = x__read_chunk_json_raw__mutmut_37 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_38'] = x__read_chunk_json_raw__mutmut_38 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_39'] = x__read_chunk_json_raw__mutmut_39 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_40'] = x__read_chunk_json_raw__mutmut_40 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_41'] = x__read_chunk_json_raw__mutmut_41 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_42'] = x__read_chunk_json_raw__mutmut_42 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_43'] = x__read_chunk_json_raw__mutmut_43 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_44'] = x__read_chunk_json_raw__mutmut_44 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_45'] = x__read_chunk_json_raw__mutmut_45 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_46'] = x__read_chunk_json_raw__mutmut_46 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_47'] = x__read_chunk_json_raw__mutmut_47 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_48'] = x__read_chunk_json_raw__mutmut_48 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_49'] = x__read_chunk_json_raw__mutmut_49 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_50'] = x__read_chunk_json_raw__mutmut_50 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_51'] = x__read_chunk_json_raw__mutmut_51 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_52'] = x__read_chunk_json_raw__mutmut_52 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_53'] = x__read_chunk_json_raw__mutmut_53 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_54'] = x__read_chunk_json_raw__mutmut_54 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_55'] = x__read_chunk_json_raw__mutmut_55 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_56'] = x__read_chunk_json_raw__mutmut_56 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_57'] = x__read_chunk_json_raw__mutmut_57 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_58'] = x__read_chunk_json_raw__mutmut_58 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_59'] = x__read_chunk_json_raw__mutmut_59 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_60'] = x__read_chunk_json_raw__mutmut_60 # type: ignore # mutmut generated
mutants_x__read_chunk_json_raw__mutmut['x__read_chunk_json_raw__mutmut_61'] = x__read_chunk_json_raw__mutmut_61 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_read_json_file__mutmut)
def read_json_file(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_orig(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_1(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = None
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_2(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(None)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_3(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is not None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_4(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(None)
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_5(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = None
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_6(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") and ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_7(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(None, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_8(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, None) or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_9(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str("title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_10(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, ) or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_11(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "XXtitleXX") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_12(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "TITLE") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_13(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or "XXXX"
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_14(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = None
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_15(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") and "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_16(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(None, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_17(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, None) or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_18(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str("lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_19(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, ) or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_20(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "XXlangXX") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_21(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "LANG") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_22(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "XXenXX"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_23(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "EN"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_24(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = None
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_25(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") and []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_26(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(None, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_27(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, None) or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_28(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list("code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_29(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, ) or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_30(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "XXcode_blocksXX") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_31(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "CODE_BLOCKS") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_32(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = None
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_33(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(None, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_34(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, None)
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_35(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str("etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_36(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, )
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_37(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "XXetagXX")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_38(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "ETAG")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_39(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = None
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_40(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(None, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_41(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, None)
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_42(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str("last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_43(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, )
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_44(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "XXlast_modifiedXX")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_45(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "LAST_MODIFIED")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_46(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = None
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_47(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(None, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_48(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, None, "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_49(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", None)
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_50(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default("chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_51(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_52(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", )
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_53(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "XXchunking_strategyXX", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_54(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "CHUNKING_STRATEGY", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_55(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "XXtextXX")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_56(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "TEXT")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_57(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = None
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_58(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(None, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_59(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, None)
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_60(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str("normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_61(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, )
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_62(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "XXnormalized_contentXX")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_63(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "NORMALIZED_CONTENT")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_64(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = None
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_65(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(None, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_66(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, None, 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_67(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", None)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_68(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default("chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_69(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_70(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", )
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_71(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "XXchunk_indexXX", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_72(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "CHUNK_INDEX", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_73(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 1)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_74(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = None
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_75(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") and ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_76(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(None, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_77(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, None) or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_78(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str("source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_79(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, ) or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_80(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "XXsource_fileXX") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_81(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "SOURCE_FILE") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_82(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or "XXXX"
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_83(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = None
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_84(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") and ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_85(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(None, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_86(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, None) or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_87(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str("chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_88(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, ) or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_89(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "XXchunk_typeXX") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_90(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "CHUNK_TYPE") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_91(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or "XXXX"
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_92(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=None,
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_93(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=None,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_94(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=None,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_95(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=None,
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_96(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=None,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_97(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=None,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_98(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=None,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_99(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=None,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_100(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=None,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_101(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=None,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_102(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=None,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_103(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=None,
    )


def x_read_json_file__mutmut_104(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_105(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_106(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_107(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_108(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_109(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_110(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_111(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_112(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_113(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_114(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_115(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        )


def x_read_json_file__mutmut_116(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["XXurlXX"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_117(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["URL"],
        title=title,
        lang=lang,
        content=data["content"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_118(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["XXcontentXX"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )


def x_read_json_file__mutmut_119(path: Path) -> ChunkDocument:
    """Read and parse a JSON file; return ChunkDocument. Raises on failure."""
    data = _read_chunk_json_raw(path)
    if data is None:
        raise ChunkFormatError(f"Failed to read chunk file: {path}")
    title = _get_str(data, "title") or ""
    lang = _get_str(data, "lang") or "en"
    code_blocks = _get_list(data, "code_blocks") or []
    etag = _get_str(data, "etag")
    last_modified = _get_str(data, "last_modified")
    chunking_strategy = _get_str_with_default(data, "chunking_strategy", "text")
    normalized_content = _get_str(data, "normalized_content")
    chunk_index = _get_int_with_default(data, "chunk_index", 0)
    source_file = _get_str(data, "source_file") or ""
    chunk_type = _get_str(data, "chunk_type") or ""
    return ChunkDocument(
        url=data["url"],
        title=title,
        lang=lang,
        content=data["CONTENT"],
        code_blocks=code_blocks,
        etag=etag,
        last_modified=last_modified,
        chunking_strategy=chunking_strategy,
        normalized_content=normalized_content,
        chunk_index=chunk_index,
        source_file=source_file,
        chunk_type=chunk_type,
    )

mutants_x_read_json_file__mutmut['_mutmut_orig'] = x_read_json_file__mutmut_orig # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_1'] = x_read_json_file__mutmut_1 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_2'] = x_read_json_file__mutmut_2 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_3'] = x_read_json_file__mutmut_3 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_4'] = x_read_json_file__mutmut_4 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_5'] = x_read_json_file__mutmut_5 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_6'] = x_read_json_file__mutmut_6 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_7'] = x_read_json_file__mutmut_7 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_8'] = x_read_json_file__mutmut_8 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_9'] = x_read_json_file__mutmut_9 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_10'] = x_read_json_file__mutmut_10 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_11'] = x_read_json_file__mutmut_11 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_12'] = x_read_json_file__mutmut_12 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_13'] = x_read_json_file__mutmut_13 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_14'] = x_read_json_file__mutmut_14 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_15'] = x_read_json_file__mutmut_15 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_16'] = x_read_json_file__mutmut_16 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_17'] = x_read_json_file__mutmut_17 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_18'] = x_read_json_file__mutmut_18 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_19'] = x_read_json_file__mutmut_19 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_20'] = x_read_json_file__mutmut_20 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_21'] = x_read_json_file__mutmut_21 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_22'] = x_read_json_file__mutmut_22 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_23'] = x_read_json_file__mutmut_23 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_24'] = x_read_json_file__mutmut_24 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_25'] = x_read_json_file__mutmut_25 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_26'] = x_read_json_file__mutmut_26 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_27'] = x_read_json_file__mutmut_27 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_28'] = x_read_json_file__mutmut_28 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_29'] = x_read_json_file__mutmut_29 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_30'] = x_read_json_file__mutmut_30 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_31'] = x_read_json_file__mutmut_31 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_32'] = x_read_json_file__mutmut_32 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_33'] = x_read_json_file__mutmut_33 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_34'] = x_read_json_file__mutmut_34 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_35'] = x_read_json_file__mutmut_35 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_36'] = x_read_json_file__mutmut_36 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_37'] = x_read_json_file__mutmut_37 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_38'] = x_read_json_file__mutmut_38 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_39'] = x_read_json_file__mutmut_39 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_40'] = x_read_json_file__mutmut_40 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_41'] = x_read_json_file__mutmut_41 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_42'] = x_read_json_file__mutmut_42 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_43'] = x_read_json_file__mutmut_43 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_44'] = x_read_json_file__mutmut_44 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_45'] = x_read_json_file__mutmut_45 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_46'] = x_read_json_file__mutmut_46 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_47'] = x_read_json_file__mutmut_47 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_48'] = x_read_json_file__mutmut_48 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_49'] = x_read_json_file__mutmut_49 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_50'] = x_read_json_file__mutmut_50 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_51'] = x_read_json_file__mutmut_51 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_52'] = x_read_json_file__mutmut_52 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_53'] = x_read_json_file__mutmut_53 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_54'] = x_read_json_file__mutmut_54 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_55'] = x_read_json_file__mutmut_55 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_56'] = x_read_json_file__mutmut_56 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_57'] = x_read_json_file__mutmut_57 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_58'] = x_read_json_file__mutmut_58 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_59'] = x_read_json_file__mutmut_59 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_60'] = x_read_json_file__mutmut_60 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_61'] = x_read_json_file__mutmut_61 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_62'] = x_read_json_file__mutmut_62 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_63'] = x_read_json_file__mutmut_63 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_64'] = x_read_json_file__mutmut_64 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_65'] = x_read_json_file__mutmut_65 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_66'] = x_read_json_file__mutmut_66 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_67'] = x_read_json_file__mutmut_67 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_68'] = x_read_json_file__mutmut_68 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_69'] = x_read_json_file__mutmut_69 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_70'] = x_read_json_file__mutmut_70 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_71'] = x_read_json_file__mutmut_71 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_72'] = x_read_json_file__mutmut_72 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_73'] = x_read_json_file__mutmut_73 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_74'] = x_read_json_file__mutmut_74 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_75'] = x_read_json_file__mutmut_75 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_76'] = x_read_json_file__mutmut_76 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_77'] = x_read_json_file__mutmut_77 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_78'] = x_read_json_file__mutmut_78 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_79'] = x_read_json_file__mutmut_79 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_80'] = x_read_json_file__mutmut_80 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_81'] = x_read_json_file__mutmut_81 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_82'] = x_read_json_file__mutmut_82 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_83'] = x_read_json_file__mutmut_83 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_84'] = x_read_json_file__mutmut_84 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_85'] = x_read_json_file__mutmut_85 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_86'] = x_read_json_file__mutmut_86 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_87'] = x_read_json_file__mutmut_87 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_88'] = x_read_json_file__mutmut_88 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_89'] = x_read_json_file__mutmut_89 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_90'] = x_read_json_file__mutmut_90 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_91'] = x_read_json_file__mutmut_91 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_92'] = x_read_json_file__mutmut_92 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_93'] = x_read_json_file__mutmut_93 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_94'] = x_read_json_file__mutmut_94 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_95'] = x_read_json_file__mutmut_95 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_96'] = x_read_json_file__mutmut_96 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_97'] = x_read_json_file__mutmut_97 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_98'] = x_read_json_file__mutmut_98 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_99'] = x_read_json_file__mutmut_99 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_100'] = x_read_json_file__mutmut_100 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_101'] = x_read_json_file__mutmut_101 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_102'] = x_read_json_file__mutmut_102 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_103'] = x_read_json_file__mutmut_103 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_104'] = x_read_json_file__mutmut_104 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_105'] = x_read_json_file__mutmut_105 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_106'] = x_read_json_file__mutmut_106 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_107'] = x_read_json_file__mutmut_107 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_108'] = x_read_json_file__mutmut_108 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_109'] = x_read_json_file__mutmut_109 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_110'] = x_read_json_file__mutmut_110 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_111'] = x_read_json_file__mutmut_111 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_112'] = x_read_json_file__mutmut_112 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_113'] = x_read_json_file__mutmut_113 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_114'] = x_read_json_file__mutmut_114 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_115'] = x_read_json_file__mutmut_115 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_116'] = x_read_json_file__mutmut_116 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_117'] = x_read_json_file__mutmut_117 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_118'] = x_read_json_file__mutmut_118 # type: ignore # mutmut generated
mutants_x_read_json_file__mutmut['x_read_json_file__mutmut_119'] = x_read_json_file__mutmut_119 # type: ignore # mutmut generated
mutants_x__get_str__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__get_str__mutmut)
def _get_str(data: ChunkJsonRaw, key: str) -> str | None:
    """Get a string value from data."""
    val = data.get(key)
    return val if isinstance(val, str) else None


def x__get_str__mutmut_orig(data: ChunkJsonRaw, key: str) -> str | None:
    """Get a string value from data."""
    val = data.get(key)
    return val if isinstance(val, str) else None


def x__get_str__mutmut_1(data: ChunkJsonRaw, key: str) -> str | None:
    """Get a string value from data."""
    val = None
    return val if isinstance(val, str) else None


def x__get_str__mutmut_2(data: ChunkJsonRaw, key: str) -> str | None:
    """Get a string value from data."""
    val = data.get(None)
    return val if isinstance(val, str) else None

mutants_x__get_str__mutmut['_mutmut_orig'] = x__get_str__mutmut_orig # type: ignore # mutmut generated
mutants_x__get_str__mutmut['x__get_str__mutmut_1'] = x__get_str__mutmut_1 # type: ignore # mutmut generated
mutants_x__get_str__mutmut['x__get_str__mutmut_2'] = x__get_str__mutmut_2 # type: ignore # mutmut generated
mutants_x__get_list__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__get_list__mutmut)
def _get_list(data: ChunkJsonRaw, key: str) -> list[str] | None:
    """Get a list value from data."""
    val = data.get(key)
    return list(val) if isinstance(val, list) else None


def x__get_list__mutmut_orig(data: ChunkJsonRaw, key: str) -> list[str] | None:
    """Get a list value from data."""
    val = data.get(key)
    return list(val) if isinstance(val, list) else None


def x__get_list__mutmut_1(data: ChunkJsonRaw, key: str) -> list[str] | None:
    """Get a list value from data."""
    val = None
    return list(val) if isinstance(val, list) else None


def x__get_list__mutmut_2(data: ChunkJsonRaw, key: str) -> list[str] | None:
    """Get a list value from data."""
    val = data.get(None)
    return list(val) if isinstance(val, list) else None


def x__get_list__mutmut_3(data: ChunkJsonRaw, key: str) -> list[str] | None:
    """Get a list value from data."""
    val = data.get(key)
    return list(None) if isinstance(val, list) else None

mutants_x__get_list__mutmut['_mutmut_orig'] = x__get_list__mutmut_orig # type: ignore # mutmut generated
mutants_x__get_list__mutmut['x__get_list__mutmut_1'] = x__get_list__mutmut_1 # type: ignore # mutmut generated
mutants_x__get_list__mutmut['x__get_list__mutmut_2'] = x__get_list__mutmut_2 # type: ignore # mutmut generated
mutants_x__get_list__mutmut['x__get_list__mutmut_3'] = x__get_list__mutmut_3 # type: ignore # mutmut generated
mutants_x__get_str_with_default__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__get_str_with_default__mutmut)
def _get_str_with_default(data: ChunkJsonRaw, key: str, default: str) -> str:
    """Get a string value with default fallback."""
    val = data.get(key)
    return val if isinstance(val, str) else default


def x__get_str_with_default__mutmut_orig(data: ChunkJsonRaw, key: str, default: str) -> str:
    """Get a string value with default fallback."""
    val = data.get(key)
    return val if isinstance(val, str) else default


def x__get_str_with_default__mutmut_1(data: ChunkJsonRaw, key: str, default: str) -> str:
    """Get a string value with default fallback."""
    val = None
    return val if isinstance(val, str) else default


def x__get_str_with_default__mutmut_2(data: ChunkJsonRaw, key: str, default: str) -> str:
    """Get a string value with default fallback."""
    val = data.get(None)
    return val if isinstance(val, str) else default

mutants_x__get_str_with_default__mutmut['_mutmut_orig'] = x__get_str_with_default__mutmut_orig # type: ignore # mutmut generated
mutants_x__get_str_with_default__mutmut['x__get_str_with_default__mutmut_1'] = x__get_str_with_default__mutmut_1 # type: ignore # mutmut generated
mutants_x__get_str_with_default__mutmut['x__get_str_with_default__mutmut_2'] = x__get_str_with_default__mutmut_2 # type: ignore # mutmut generated
mutants_x__get_int_with_default__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__get_int_with_default__mutmut)
def _get_int_with_default(data: ChunkJsonRaw, key: str, default: int) -> int:
    """Get an integer value with default fallback."""
    val = data.get(key)
    if val is None:
        return default
    try:
        return int(val)  # type: ignore[call-overload, no-any-return]
    except (ValueError, TypeError):
        return default


def x__get_int_with_default__mutmut_orig(data: ChunkJsonRaw, key: str, default: int) -> int:
    """Get an integer value with default fallback."""
    val = data.get(key)
    if val is None:
        return default
    try:
        return int(val)  # type: ignore[call-overload, no-any-return]
    except (ValueError, TypeError):
        return default


def x__get_int_with_default__mutmut_1(data: ChunkJsonRaw, key: str, default: int) -> int:
    """Get an integer value with default fallback."""
    val = None
    if val is None:
        return default
    try:
        return int(val)  # type: ignore[call-overload, no-any-return]
    except (ValueError, TypeError):
        return default


def x__get_int_with_default__mutmut_2(data: ChunkJsonRaw, key: str, default: int) -> int:
    """Get an integer value with default fallback."""
    val = data.get(None)
    if val is None:
        return default
    try:
        return int(val)  # type: ignore[call-overload, no-any-return]
    except (ValueError, TypeError):
        return default


def x__get_int_with_default__mutmut_3(data: ChunkJsonRaw, key: str, default: int) -> int:
    """Get an integer value with default fallback."""
    val = data.get(key)
    if val is not None:
        return default
    try:
        return int(val)  # type: ignore[call-overload, no-any-return]
    except (ValueError, TypeError):
        return default


def x__get_int_with_default__mutmut_4(data: ChunkJsonRaw, key: str, default: int) -> int:
    """Get an integer value with default fallback."""
    val = data.get(key)
    if val is None:
        return default
    try:
        return int(None)  # type: ignore[call-overload, no-any-return]
    except (ValueError, TypeError):
        return default

mutants_x__get_int_with_default__mutmut['_mutmut_orig'] = x__get_int_with_default__mutmut_orig # type: ignore # mutmut generated
mutants_x__get_int_with_default__mutmut['x__get_int_with_default__mutmut_1'] = x__get_int_with_default__mutmut_1 # type: ignore # mutmut generated
mutants_x__get_int_with_default__mutmut['x__get_int_with_default__mutmut_2'] = x__get_int_with_default__mutmut_2 # type: ignore # mutmut generated
mutants_x__get_int_with_default__mutmut['x__get_int_with_default__mutmut_3'] = x__get_int_with_default__mutmut_3 # type: ignore # mutmut generated
mutants_x__get_int_with_default__mutmut['x__get_int_with_default__mutmut_4'] = x__get_int_with_default__mutmut_4 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_collect_source_files__mutmut)
def collect_source_files(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_orig(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_1(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_2(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_3(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=None, reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_4(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason=None)]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_5(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_6(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), )]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_7(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(None), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_8(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="XXfile not foundXX")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_9(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="FILE NOT FOUND")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.json"))
    return files, []


def x_collect_source_files__mutmut_10(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = None
    return files, []


def x_collect_source_files__mutmut_11(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(None)
    return files, []


def x_collect_source_files__mutmut_12(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob(None))
    return files, []


def x_collect_source_files__mutmut_13(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("XX*.jsonXX"))
    return files, []


def x_collect_source_files__mutmut_14(
    rag_src_dir: Path, target: Path | None = None
) -> tuple[list[Path], list[SkipInfo]]:
    """Return (files_to_process, skipped) from rag_src_dir."""
    if target is not None:
        if not target.exists():
            return [], [SkipInfo(path=str(target), reason="file not found")]
        return [target], []
    files = sorted(rag_src_dir.glob("*.JSON"))
    return files, []

mutants_x_collect_source_files__mutmut['_mutmut_orig'] = x_collect_source_files__mutmut_orig # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_1'] = x_collect_source_files__mutmut_1 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_2'] = x_collect_source_files__mutmut_2 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_3'] = x_collect_source_files__mutmut_3 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_4'] = x_collect_source_files__mutmut_4 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_5'] = x_collect_source_files__mutmut_5 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_6'] = x_collect_source_files__mutmut_6 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_7'] = x_collect_source_files__mutmut_7 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_8'] = x_collect_source_files__mutmut_8 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_9'] = x_collect_source_files__mutmut_9 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_10'] = x_collect_source_files__mutmut_10 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_11'] = x_collect_source_files__mutmut_11 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_12'] = x_collect_source_files__mutmut_12 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_13'] = x_collect_source_files__mutmut_13 # type: ignore # mutmut generated
mutants_x_collect_source_files__mutmut['x_collect_source_files__mutmut_14'] = x_collect_source_files__mutmut_14 # type: ignore # mutmut generated
mutants_x_is_already_processed__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_is_already_processed__mutmut)
def is_already_processed(sentinel_path: Path, force: bool) -> bool:
    """Return True when the sentinel file exists and force=False (skip signal)."""
    return not force and sentinel_path.exists()


def x_is_already_processed__mutmut_orig(sentinel_path: Path, force: bool) -> bool:
    """Return True when the sentinel file exists and force=False (skip signal)."""
    return not force and sentinel_path.exists()


def x_is_already_processed__mutmut_1(sentinel_path: Path, force: bool) -> bool:
    """Return True when the sentinel file exists and force=False (skip signal)."""
    return not force or sentinel_path.exists()


def x_is_already_processed__mutmut_2(sentinel_path: Path, force: bool) -> bool:
    """Return True when the sentinel file exists and force=False (skip signal)."""
    return force and sentinel_path.exists()

mutants_x_is_already_processed__mutmut['_mutmut_orig'] = x_is_already_processed__mutmut_orig # type: ignore # mutmut generated
mutants_x_is_already_processed__mutmut['x_is_already_processed__mutmut_1'] = x_is_already_processed__mutmut_1 # type: ignore # mutmut generated
mutants_x_is_already_processed__mutmut['x_is_already_processed__mutmut_2'] = x_is_already_processed__mutmut_2 # type: ignore # mutmut generated
