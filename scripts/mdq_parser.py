#!/usr/bin/env python3
"""scripts/mdq_parser.py
Markdown parser for the MDQ MCP server.

This script provides functions to parse Markdown documents and extract
structure information including headings, tags, and content.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────────────────────────────────────


class DocumentOutline(BaseModel):
    """Represents the outline of a Markdown document."""

    path: str
    headings: list[
        dict[str, Any]
    ]  # List of heading dictionaries with level, text, etc.
    tags: list[str]


# ──────────────────────────────────────────────────────────────────────────────
# Parser Functions
# ──────────────────────────────────────────────────────────────────────────────


def _parse_tags_line(tags_line: str) -> list[str]:
    """Parse a 'tags:' value into a list of tag strings.

    Handles both YAML array format ('[a, b]') and comma-separated format ('a, b').
    """
    if tags_line.startswith("["):
        inner = tags_line[1:-1]  # strip brackets
        return [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
    return [t.strip() for t in tags_line.split(",") if t.strip()]


def _extract_frontmatter_tags(lines: list[str]) -> list[str]:
    """Scan lines before the first '---' fence for a 'tags:' entry."""
    for line in lines:
        if line.startswith("---"):
            return []
        if line.startswith("tags:"):
            return _parse_tags_line(line[5:].strip())
    return []


def parse_markdown_outline(content: str) -> DocumentOutline:
    """Parse Markdown content and extract outline information."""
    lines = content.splitlines()
    tags = _extract_frontmatter_tags(lines)
    headings = [
        {"level": len(m.group(1)), "text": m.group(2).strip(), "line_number": i + 1}
        for i, line in enumerate(lines)
        if (m := re.match(r"^(#+)\s+(.*)", line))
    ]
    return DocumentOutline(path="", headings=headings, tags=tags)


def extract_chunk_content(content: str, heading: str) -> str:
    """Extract content for a specific heading from the Markdown document."""
    # Find the heading in the content
    start_pos = content.find(f"## {heading}")

    if start_pos == -1:
        return content  # Return entire content if heading not found

    # Find the next heading to determine the end of this section
    end_pos = content.find("\n## ", start_pos + 1)

    if end_pos == -1:
        # No next heading, so take content to the end
        return content[start_pos:].strip()
    # Return content between start and end
    return content[start_pos:end_pos].strip()
