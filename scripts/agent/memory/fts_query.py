#!/usr/bin/env python3
"""agent/memory/fts_query.py — FTS5 query builder."""

import re  # noqa: PLC0415


def build_fts_query(text: str) -> str:
    """Build FTS5 MATCH query with token quoting to escape reserved terms.

    All tokens are double-quoted to escape AND/OR/NOT/NEAR as literals.
    No column filter: memories_fts searches content, summary, and tags.
    """
    tokens = re.findall(r"\w+", text)
    if not tokens:
        return '""'
    return " OR ".join(f'"{t}"' for t in tokens)
