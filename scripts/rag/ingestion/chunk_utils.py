#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_utils.py

Shared buffer helpers for ChunkEnglishMixin and ChunkJapaneseMixin.

Imported by chunk_english.py, chunk_japanese.py, and chunk_splitter.py.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence


def start_next_buf(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if not chunk_overlap:
        return next_item
    overlap = prev[-chunk_overlap:]
    return (overlap + sep + next_item).strip() if overlap else next_item


def accumulate_items[T](
    items: Sequence[T],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
    *,
    fits: Callable[[T, T], bool],
    append_item: Callable[[T, T], T],
    segment_oversized: Callable[[T, T], list[str] | None],
    place_oversized: Callable[[T, T, list[str]], tuple[Sequence[T], T]],
    should_emit: Callable[[T], bool],
    emit_and_overlap: Callable[[list[T], T, T], T],
    short_tail: Callable[[list[T], T, T], T],
    finalize_buffer: Callable[[list[T], T], None],
    initial_buffer: T,
) -> list[T]:
    """Own the shared min/max/overlap accumulation loop for one chunking path.

    Three chunkers (code, English, Japanese) previously encoded the same
    min/max/overlap intent with divergent oversized-item, short-tail, and
    end-of-stream rules. This collaborator keeps a single greedy-accumulation
    loop and takes each path's divergent decisions as explicit callbacks, so no
    path re-implements the loop and output stays byte-identical to before.

    ``T`` is the element type for the path: a plain ``str`` (code/English) or an
    ``(original, normalized)`` pair (Japanese). ``initial_buffer`` is the empty
    starting buffer whose concrete shape matches ``T``. Each callback encodes
    exactly one divergent decision axis (fits test, oversized strategy, emit
    threshold, overlap, short-tail handling, end-of-stream finalize), so the
    loop body itself carries no per-path behavior.
    """
    result: list[T] = []
    buf = initial_buffer
    for item in items:
        pieces = segment_oversized(buf, item)
        if pieces is not None:
            appends, buf = place_oversized(buf, item, pieces)
            result.extend(appends)
            continue
        if fits(buf, item):
            buf = append_item(buf, item)
            continue
        if should_emit(buf):
            buf = emit_and_overlap(result, buf, item)
        else:
            buf = short_tail(result, buf, item)
    finalize_buffer(result, buf)
    return result


def _split_overlong(item: str, sep: str, max_chunk: int) -> list[str]:
    """Split one item longer than max_chunk into chunks each within max_chunk.

    Greedy fill: within each max_chunk window break at the last space or newline,
    otherwise hard-cut at max_chunk. The concatenation of the returned chunks
    reproduces item exactly. Raw character slicing only, so language-independent.
    """
    chunks: list[str] = []
    start = 0
    end = len(item)
    if max_chunk <= 0:
        raise ValueError(f"max_chunk must be positive, got {max_chunk}")
    while start < end:
        window_end = min(start + max_chunk, end)
        if window_end == end:
            chunks.append(item[start:])
            break
        window = item[start:window_end]
        gap = max(window.rfind(" "), window.rfind("\n"))
        cut = start + gap + 1 if gap >= 0 else window_end
        chunks.append(item[start:cut])
        start = cut
    return chunks


def merge_text_items(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.

    Delegates to :func:`accumulate_items`; the code path's oversized/short-tail
    and end-of-stream rules are expressed as its strategy callbacks.
    """

    def fits(buf: str, item: str) -> bool:
        return len(buf) + len(item) + len(sep) <= max_chunk

    def append_item(buf: str, item: str) -> str:
        return (buf + sep + item).strip()

    def segment_oversized(buf: str, item: str) -> list[str] | None:
        # Only split when the buffer is too short to emit on its own; a
        # substantial buffer absorbs the overlong item via the emit path,
        # matching the pre-refactor control flow.
        if len(item) > max_chunk and len(buf) < min_chunk:
            return _split_overlong(item, sep, max_chunk)
        return None

    def place_oversized(
        buf: str, item: str, pieces: list[str]
    ) -> tuple[list[str], str]:
        # The short (< min_chunk) buffer is dropped, exactly as before.
        return (pieces, "")

    def should_emit(buf: str) -> bool:
        return len(buf) >= min_chunk

    def emit_and_overlap(result: list[str], buf: str, item: str) -> str:
        result.append(buf)
        return start_next_buf(buf, item, sep, chunk_overlap)

    def short_tail(result: list[str], buf: str, item: str) -> str:
        return item

    def finalize_buffer(result: list[str], buf: str) -> None:
        if not buf:
            return
        if len(buf) >= min_chunk:
            result.append(buf)
        elif result:
            result[-1] = (result[-1] + sep + buf).strip()

    return accumulate_items(
        items,
        sep,
        min_chunk,
        max_chunk,
        chunk_overlap,
        fits=fits,
        append_item=append_item,
        segment_oversized=segment_oversized,
        place_oversized=place_oversized,
        should_emit=should_emit,
        emit_and_overlap=emit_and_overlap,
        short_tail=short_tail,
        finalize_buffer=finalize_buffer,
        initial_buffer="",
    )
