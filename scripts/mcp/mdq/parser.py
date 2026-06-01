#!/usr/bin/env python3
"""mcp/mdq/parser.py
Markdown parser for Markdown Context Compression Engine.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def parse_markdown_file(file_path: str) -> dict[str, Any]:
    """Parse a Markdown file and return its structure."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Simple heading extraction
        headings = []
        lines = content.split("\n")
        current_order = 0

        for i, line in enumerate(lines):
            match = re.match(r"^(#+)\s+(.*)", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                # Create a path-like structure for the heading
                path = f"{level}>{title}"
                headings.append(
                    {
                        "heading_level": level,
                        "heading_title": title,
                        "heading_path": path,
                        "line_number": i + 1,
                        "chunk_id": current_order,
                        "token_count": len(title.split()),
                    },
                )
                current_order += 1

        # Extract title from first heading or filename
        title = ""
        for heading in headings:
            if heading["heading_level"] == 1:
                title = heading["heading_title"]
                break

        if not title:
            title = file_path.rsplit("/", maxsplit=1)[-1].split(".", maxsplit=1)[0]

        return {
            "title": title,
            "outline": headings,
            "content": content,
        }
    except Exception as e:
        logger.error(f"Error parsing Markdown file {file_path}: {e}")
        raise


def extract_headings(content: str) -> list[dict[str, Any]]:
    """Extract headings from Markdown content."""
    headings = []
    lines = content.split("\n")
    current_order = 0

    for i, line in enumerate(lines):
        match = re.match(r"^(#+)\s+(.*)", line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            # Create a path-like structure for the heading
            path = f"{level}>{title}"
            headings.append(
                {
                    "heading_level": level,
                    "heading_title": title,
                    "heading_path": path,
                    "line_number": i + 1,
                    "chunk_id": current_order,
                    "token_count": len(title.split()),
                },
            )
            current_order += 1

    return headings


def create_heading_path(headings: list[dict[str, Any]], index: int) -> str:
    """Create a heading path from a list of headings up to a given index."""
    path_parts = []
    for i in range(index + 1):
        if i < len(headings):
            path_parts.append(
                f"{headings[i]['heading_level']}>{headings[i]['heading_title']}",
            )
    return " > ".join(path_parts)


def get_heading_path_from_line(content: str, line_number: int) -> str:
    """Get the heading path for a specific line number."""
    lines = content.split("\n")
    if line_number <= 0 or line_number > len(lines):
        return ""

    # Find the heading that contains this line
    headings = extract_headings(content)
    for i, heading in enumerate(headings):
        if heading["line_number"] <= line_number:
            # Check if this is the last heading before or at this line
            if i == len(headings) - 1 or headings[i + 1]["line_number"] > line_number:
                return str(heading["heading_path"])

    return ""
