#!/usr/bin/env python3
"""mcp_servers/mdq/db_grep.py

Grep operations for MdqService.

Dependency direction: db_grep → models
Import from here:  from mcp_servers.mdq.db_grep import find_grep_match, grep_docs
"""

from __future__ import annotations

import re
import sqlite3

from mcp_servers.mdq.models import GrepDocMatch


def find_grep_match(
    row: sqlite3.Row,
    compiled: re.Pattern[str],
    max_chars: int,
    ctx_before: int,
    ctx_after: int,
) -> GrepDocMatch | None:
    """Find a grep match in a chunk row."""
    full_text = f"{row['heading']}\n{row['content']}"
    for re_match in compiled.finditer(full_text):
        match_start = re_match.start()
        lines = full_text.split("\n")
        match_line = 0
        line_offset = 0
        for i, line in enumerate(lines):
            if line_offset + len(line) >= match_start:
                match_line = i
                break
            line_offset += len(line) + 1
        start_idx = max(0, match_line - ctx_before)
        end_idx = min(len(lines), match_line + ctx_after + 1)
        _context_lines = lines[start_idx:end_idx]
        match_text = re_match.group()[:max_chars]
        return GrepDocMatch(
            chunk_id=row["chunk_id"],
            source_path=row["source_path"],
            heading_path=row["heading_path"],
            match_text=match_text,
            line_number=start_idx + 1,
        )
    return None


def grep_docs(
    conn: sqlite3.Connection,
    compiled: re.Pattern[str],
    req_paths: list[str],
    max_matches: int,
    max_chars: int,
    ctx_before: int,
    ctx_after: int,
) -> str:
    """Execute a grep search across chunks."""
    where_clauses = []
    params: list = []

    if req_paths:
        placeholders = ",".join("?" for _ in req_paths)
        where_clauses.append(f"source_path IN ({placeholders})")
        params.extend(req_paths)

    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    rows = conn.execute(
        f"SELECT chunk_id, source_path, heading_path, heading, content, start_line FROM chunks {where_clause}",
        params,
    ).fetchall()

    matches: list[GrepDocMatch] = []
    for row in rows:
        match = find_grep_match(row, compiled, max_chars, ctx_before, ctx_after)
        if match is None:
            continue
        matches.append(match)
        if len(matches) >= max_matches:
            break

    truncated = len(matches) >= max_matches

    if not matches:
        return "No matches found."

    parts = []
    for m in matches:
        parts.append(f"File: {m.source_path}")
        parts.append(f"Chunk: {m.chunk_id}")
        if m.heading_path:
            parts.append(f"Heading: {m.heading_path}")
        parts.append(f"Line: {m.line_number}")
        parts.append(f"Match: {m.match_text}")
        parts.append("---")

    result = "\n".join(parts)
    if truncated:
        result += (
            f"\n\n[Truncated — cap of {max_matches} matches reached. "
            f"Use a more specific pattern or path filter to narrow results.]"
        )
    return result
