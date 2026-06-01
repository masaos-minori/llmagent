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


def parse_markdown_outline(content: str) -> DocumentOutline:
    """Parse Markdown content and extract outline information."""
    headings = []
    tags = []

    # Split content into lines
    lines = content.splitlines()

    # Look for tags in the frontmatter (if any)
    for line in lines:
        if line.startswith("---"):
            # This is a frontmatter block
            break
        if line.startswith("tags:"):
            # Extract tags from the line
            tags_line = line[5:].strip()
            if tags_line.startswith("["):
                # Handle array format
                tags_str = tags_line[1:-1]  # Remove brackets
                tags = [
                    tag.strip().strip("'\"")
                    for tag in tags_str.split(",")
                    if tag.strip()
                ]
            else:
                # Handle comma-separated format
                tags = [tag.strip() for tag in tags_line.split(",") if tag.strip()]
            break

    # Parse headings
    for i, line in enumerate(lines):
        # Match Markdown headings (## Heading, ### Heading, etc.)
        heading_match = re.match(r"^(#+)\s+(.*)", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()

            # Add to headings list
            headings.append({"level": level, "text": text, "line_number": i + 1})

    # Create and return the outline
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
