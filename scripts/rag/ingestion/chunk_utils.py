#!/usr/bin/env python3
"""chunk_utils.py
Shared buffer helpers for ChunkEnglishMixin and ChunkJapaneseMixin.

Imported by chunk_english.py, chunk_japanese.py, and chunk_splitter.py.
"""

from __future__ import annotations


def start_next_buf(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if not chunk_overlap:
        return next_item
    overlap = prev[-chunk_overlap:]
    return (overlap + sep + next_item).strip() if overlap else next_item


def merge_text_items(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(buf, item, sep, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        # Merge short tail into last chunk to avoid discarding content
        result[-1] = (result[-1] + sep + buf).strip()
    return result
