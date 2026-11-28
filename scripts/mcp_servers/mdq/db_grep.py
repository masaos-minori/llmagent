#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/db_grep.py

Grep operations for MdqService.

Dependency direction: db_grep → models
Import from here:  from mcp_servers.mdq.db_grep import find_grep_match, grep_docs

Reported line semantics (REQ-006, UNK-03): `line_number` is the source-file line of
the first stored content line, computed as `start_line + 1 + k` where k is the match's
line index within the stored content; the synthetic heading line stands at `start_line`.
Regex semantics are stated, not changed: `re.compile` is called with no flags, so `.`
does not cross lines, `^` and `$` anchor only at the ends of the chunk text, and every
match is reported at the line where it starts.
"""

from __future__ import annotations

import re
import sqlite3

from mcp_servers.mdq.mdq_models import GrepDocMatch, GrepDocsMetadata


def find_grep_match(
    row: sqlite3.Row,
    compiled: re.Pattern[str],
    max_chars: int,
    ctx_before: int,
    ctx_after: int,
) -> list[GrepDocMatch]:
    """Produce every pattern hit in one chunk row, with context and reported line.

    A chunk contributes all of its hits (REQ-006); the collector's cap is applied on
    the collected list. `line_number` is `start_line + 1 + k` (UNK-03): k is the
    match's line index within the stored content, so a match on the synthetic heading
    line reports the row's `start_line`. `max_chars` bounds the context-inclusive text
    — the match text plus the returned context lines, counted as their joined length —
    so context is what shrinks when the limit is tight: the match text is exact within
    `max_chars` itself, and each returned line is a whole line, taken nearest the match
    first and alternating sides. An empty context request returns empty lists.
    """
    full_text = f"{row['heading']}\n{row['content']}"
    lines = full_text.split("\n")
    matches: list[GrepDocMatch] = []
    for re_match in compiled.finditer(full_text):
        match_start = re_match.start()
        match_line = 0
        line_offset = 0
        for i, line in enumerate(lines):
            if line_offset + len(line) >= match_start:
                match_line = i
                break
            line_offset += len(line) + 1

        match_text = re_match.group()[:max_chars]
        # Lines are whole or absent, nearest the match first, alternating sides, until
        # the match text plus the returned lines reach `max_chars` joined (REQ-006).
        budget = max_chars - len(match_text)
        before_pool = lines[max(0, match_line - ctx_before) : match_line][::-1]
        after_pool = lines[match_line + 1 : min(len(lines), match_line + 1 + ctx_after)]
        context_before: list[str] = []
        context_after: list[str] = []
        while before_pool or after_pool:
            added = False
            if before_pool and budget >= len(before_pool[0]) + 1:
                budget -= len(before_pool[0]) + 1
                context_before.append(before_pool.pop(0))
                added = True
            if after_pool and budget >= len(after_pool[0]) + 1:
                budget -= len(after_pool[0]) + 1
                context_after.append(after_pool.pop(0))
                added = True
            if not added:
                break
        context_before.reverse()

        matches.append(
            GrepDocMatch(
                chunk_id=row["chunk_id"],
                source_path=row["source_path"],
                heading_path=row["heading_path"],
                match_text=match_text,
                line_number=row["start_line"] + match_line,
                context_before_lines=context_before,
                context_after_lines=context_after,
            )
        )
    return matches


def _build_path_where_clause(req_paths: list[str]) -> tuple[str, list]:
    """Build the optional `WHERE source_path IN (...)` clause and its bound params."""
    where_clauses = []
    params: list = []

    if req_paths:
        placeholders = ",".join("?" for _ in req_paths)
        where_clauses.append(f"source_path IN ({placeholders})")
        params.extend(req_paths)

    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    return where_clause, params


def _fetch_chunk_rows(
    conn: sqlite3.Connection, where_clause: str, params: list
) -> list[sqlite3.Row]:
    """Fetch chunk rows eligible for grep matching, filtered by `where_clause`."""
    return conn.execute(
        f"SELECT chunk_id, source_path, heading_path, heading,"
        f" content, start_line FROM chunks {where_clause}",  # nosec B608 — WHERE clause built from fixed column names; values bound via params
        params,
    ).fetchall()


def _collect_grep_matches(
    rows: list[sqlite3.Row],
    compiled: re.Pattern[str],
    max_chars: int,
    ctx_before: int,
    ctx_after: int,
    max_matches: int,
) -> tuple[list[GrepDocMatch], bool]:
    """Scan `rows` for matches, stopping once `max_matches` is reached.

    A row can yield several matches, so the cap is applied to the collected list, not
    per row (REQ-006).
    """
    matches: list[GrepDocMatch] = []
    for row in rows:
        matches.extend(find_grep_match(row, compiled, max_chars, ctx_before, ctx_after))
        if len(matches) >= max_matches:
            matches = matches[:max_matches]
            break

    truncated = len(matches) >= max_matches
    return matches, truncated


def _format_grep_matches(
    matches: list[GrepDocMatch], truncated: bool, max_matches: int
) -> str:
    """Render collected matches into the tool's visible text output."""
    parts = []
    for m in matches:
        parts.append(f"File: {m.source_path}")
        parts.append(f"Chunk: {m.chunk_id}")
        if m.heading_path:
            parts.append(f"Heading: {m.heading_path}")
        parts.append(f"Line: {m.line_number}")
        parts.extend(f"  {line}" for line in m.context_before_lines)
        parts.append(f"Match: {m.match_text}")
        parts.extend(f"  {line}" for line in m.context_after_lines)
        parts.append("---")

    result = "\n".join(parts)
    if truncated:
        result += (
            f"\n\n[Truncated — cap of {max_matches} matches reached. "
            f"Use a more specific pattern or path filter to narrow results.]"
        )
    return result


def _build_grep_metadata(
    compiled: re.Pattern[str],
    req_paths: list[str],
    match_count: int,
    truncated: bool,
) -> GrepDocsMetadata:
    """Build the structured audit metadata accompanying a grep result."""
    return GrepDocsMetadata(
        pattern_preview=compiled.pattern[:80],
        path_filter_count=len(req_paths),
        match_count=match_count,
        truncated=truncated,
        grep_enabled=True,
    )


def grep_docs(
    conn: sqlite3.Connection,
    compiled: re.Pattern[str],
    req_paths: list[str],
    max_matches: int,
    max_chars: int,
    ctx_before: int,
    ctx_after: int,
) -> tuple[str, GrepDocsMetadata]:
    """Execute a grep search across chunks."""
    where_clause, params = _build_path_where_clause(req_paths)
    rows = _fetch_chunk_rows(conn, where_clause, params)
    matches, truncated = _collect_grep_matches(
        rows, compiled, max_chars, ctx_before, ctx_after, max_matches
    )

    if not matches:
        return "No matches found.", _build_grep_metadata(
            compiled, req_paths, match_count=0, truncated=False
        )

    result = _format_grep_matches(matches, truncated, max_matches)
    return result, _build_grep_metadata(
        compiled, req_paths, match_count=len(matches), truncated=truncated
    )
