#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_utils.py

Shared buffer helpers for ChunkEnglishMixin and ChunkJapaneseMixin.

Imported by chunk_english.py, chunk_japanese.py, and chunk_splitter.py.
"""

from __future__ import annotations


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_start_next_buf__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_start_next_buf__mutmut)
def start_next_buf(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if not chunk_overlap:
        return next_item
    overlap = prev[-chunk_overlap:]
    return (overlap + sep + next_item).strip() if overlap else next_item


def x_start_next_buf__mutmut_orig(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if not chunk_overlap:
        return next_item
    overlap = prev[-chunk_overlap:]
    return (overlap + sep + next_item).strip() if overlap else next_item


def x_start_next_buf__mutmut_1(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if chunk_overlap:
        return next_item
    overlap = prev[-chunk_overlap:]
    return (overlap + sep + next_item).strip() if overlap else next_item


def x_start_next_buf__mutmut_2(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if not chunk_overlap:
        return next_item
    overlap = None
    return (overlap + sep + next_item).strip() if overlap else next_item


def x_start_next_buf__mutmut_3(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if not chunk_overlap:
        return next_item
    overlap = prev[+chunk_overlap:]
    return (overlap + sep + next_item).strip() if overlap else next_item


def x_start_next_buf__mutmut_4(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if not chunk_overlap:
        return next_item
    overlap = prev[-chunk_overlap:]
    return (overlap + sep - next_item).strip() if overlap else next_item


def x_start_next_buf__mutmut_5(prev: str, next_item: str, sep: str, chunk_overlap: int) -> str:
    """Start a new accumulation buffer with optional tail-overlap from prev."""
    if not chunk_overlap:
        return next_item
    overlap = prev[-chunk_overlap:]
    return (overlap - sep + next_item).strip() if overlap else next_item

mutants_x_start_next_buf__mutmut['_mutmut_orig'] = x_start_next_buf__mutmut_orig # type: ignore # mutmut generated
mutants_x_start_next_buf__mutmut['x_start_next_buf__mutmut_1'] = x_start_next_buf__mutmut_1 # type: ignore # mutmut generated
mutants_x_start_next_buf__mutmut['x_start_next_buf__mutmut_2'] = x_start_next_buf__mutmut_2 # type: ignore # mutmut generated
mutants_x_start_next_buf__mutmut['x_start_next_buf__mutmut_3'] = x_start_next_buf__mutmut_3 # type: ignore # mutmut generated
mutants_x_start_next_buf__mutmut['x_start_next_buf__mutmut_4'] = x_start_next_buf__mutmut_4 # type: ignore # mutmut generated
mutants_x_start_next_buf__mutmut['x_start_next_buf__mutmut_5'] = x_start_next_buf__mutmut_5 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_merge_text_items__mutmut)
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
    if not items:
        return []
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_orig(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_1(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if items:
        return []
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_2(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = None
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_3(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = None
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_4(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = None
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_5(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = "XXXX"
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_6(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) - overhead <= max_chunk:
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_7(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) - len(item) + overhead <= max_chunk:
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_8(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead < max_chunk:
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_9(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = None
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_10(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep - item).strip()
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_11(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf - sep + item).strip()
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
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_12(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) > min_chunk:
            result.append(buf)
            buf = start_next_buf(buf, item, sep, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_13(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(None)
            buf = start_next_buf(buf, item, sep, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_14(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = None
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_15(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(None, item, sep, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_16(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(buf, None, sep, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_17(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(buf, item, None, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_18(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(buf, item, sep, None)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_19(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(item, sep, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_20(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(buf, sep, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_21(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(buf, item, chunk_overlap)
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_22(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
    overhead = len(sep)
    result: list[str] = []
    buf = ""
    for item in items:
        if len(buf) + len(item) + overhead <= max_chunk:
            buf = (buf + sep + item).strip()
        elif len(buf) >= min_chunk:
            result.append(buf)
            buf = start_next_buf(buf, item, sep, )
        else:
            buf = item
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_23(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
            buf = None
    if not buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_24(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
    if buf:
        return result
    if len(buf) >= min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_25(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
    if len(buf) > min_chunk:
        result.append(buf)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_26(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result.append(None)
    elif result:
        result[-1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_27(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result[-1] = None
    return result


def x_merge_text_items__mutmut_28(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result[+1] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_29(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result[-2] = (result[-1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_30(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result[-1] = (result[-1] + sep - buf).strip()
    return result


def x_merge_text_items__mutmut_31(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result[-1] = (result[-1] - sep + buf).strip()
    return result


def x_merge_text_items__mutmut_32(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result[-1] = (result[+1] + sep + buf).strip()
    return result


def x_merge_text_items__mutmut_33(
    items: list[str],
    sep: str,
    min_chunk: int,
    max_chunk: int,
    chunk_overlap: int,
) -> list[str]:
    """Accumulate items into chunks satisfying min_chunk <= len <= max_chunk.

    A short tail item is merged into the last chunk instead of discarded.
    """
    if not items:
        return []
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
        result[-1] = (result[-2] + sep + buf).strip()
    return result

mutants_x_merge_text_items__mutmut['_mutmut_orig'] = x_merge_text_items__mutmut_orig # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_1'] = x_merge_text_items__mutmut_1 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_2'] = x_merge_text_items__mutmut_2 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_3'] = x_merge_text_items__mutmut_3 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_4'] = x_merge_text_items__mutmut_4 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_5'] = x_merge_text_items__mutmut_5 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_6'] = x_merge_text_items__mutmut_6 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_7'] = x_merge_text_items__mutmut_7 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_8'] = x_merge_text_items__mutmut_8 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_9'] = x_merge_text_items__mutmut_9 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_10'] = x_merge_text_items__mutmut_10 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_11'] = x_merge_text_items__mutmut_11 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_12'] = x_merge_text_items__mutmut_12 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_13'] = x_merge_text_items__mutmut_13 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_14'] = x_merge_text_items__mutmut_14 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_15'] = x_merge_text_items__mutmut_15 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_16'] = x_merge_text_items__mutmut_16 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_17'] = x_merge_text_items__mutmut_17 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_18'] = x_merge_text_items__mutmut_18 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_19'] = x_merge_text_items__mutmut_19 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_20'] = x_merge_text_items__mutmut_20 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_21'] = x_merge_text_items__mutmut_21 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_22'] = x_merge_text_items__mutmut_22 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_23'] = x_merge_text_items__mutmut_23 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_24'] = x_merge_text_items__mutmut_24 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_25'] = x_merge_text_items__mutmut_25 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_26'] = x_merge_text_items__mutmut_26 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_27'] = x_merge_text_items__mutmut_27 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_28'] = x_merge_text_items__mutmut_28 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_29'] = x_merge_text_items__mutmut_29 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_30'] = x_merge_text_items__mutmut_30 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_31'] = x_merge_text_items__mutmut_31 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_32'] = x_merge_text_items__mutmut_32 # type: ignore # mutmut generated
mutants_x_merge_text_items__mutmut['x_merge_text_items__mutmut_33'] = x_merge_text_items__mutmut_33 # type: ignore # mutmut generated
