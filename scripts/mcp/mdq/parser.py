#!/usr/bin/env python3
"""mcp/mdq/parser.py
Hierarchy-aware Markdown parsing — heading-based section extraction.

Produces section records with:
- heading, heading_level, heading_path, content, start_line, end_line, ordinal, parent_heading

Supported Markdown features:
- ATX headings (## Heading) — all levels 1-6
- Fenced code blocks (```, ~~~) — # inside fences are not headings
- Content before first heading (as <root> section)
- Repeated heading names (distinct chunk identities via ordinal)
- Nested heading hierarchy (heading_path includes ancestors)
- Optional YAML frontmatter (parsed and stripped)
- Malformed headings (ignored)

Unsupported Markdown features:
- Setext-style headings (===, --- underlines)
- Inline tags (<del>, <ins>, etc.) — not parsed
- HTML blocks — not parsed, treated as plain text
- MDX — not supported
- GFM tables — not parsed (but not required for section extraction)

Fallback behavior for unsupported syntax:
- Unsupported syntax may cause heading misclassification. For example,
  a Setext-style heading (text followed by === underline) will be treated
  as plain text with no heading level, and its content will be included
  in the preceding section rather than creating a new one.
- HTML headings (<h1>, <h2>) are not recognized — content is treated as plain text.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from mcp.mdq.models import ParsedSection, ParseMarkdownRequest

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def parse_markdown(
    service: MdqService, req: ParseMarkdownRequest
) -> list[ParsedSection]:
    """Parse a Markdown file and return its sections as a list of dicts.

    Each dict has keys: heading, heading_level, heading_path, content,
    start_line, end_line, ordinal, parent_heading.
    """
    logger.info("Parsing Markdown file: %s", req.path)
    path = Path(req.path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {req.path}")

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    sections: list[ParsedSection] = []
    in_fence = False
    fence_char = ""
    current_section: dict | None = None
    heading_stack: list[tuple[int, str]] = []  # (level, heading_text)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        # Handle fenced code blocks
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if not in_fence:
                in_fence = True
                fence_char = stripped[:3]
                i += 1
                continue
            elif stripped.startswith(fence_char):
                in_fence = False
                fence_char = ""
                i += 1
                continue

        # Skip fenced code block content
        if in_fence:
            i += 1
            continue

        # Check for frontmatter delimiter (only at start of file)
        if i == 0 and stripped == "---":
            # Look for closing ---
            j = i + 1
            while j < len(lines) and lines[j].rstrip() != "---":
                j += 1
            if j < len(lines) and lines[j].rstrip() == "---":
                # Skip frontmatter (lines i to j inclusive)
                i = j + 1
                continue

        # Check for ATX heading inside fenced code blocks are already skipped above
        heading_info = _parse_atx_heading(stripped)
        if heading_info is not None:
            heading_level_val, heading_text_val = heading_info
            heading_match = True
        else:
            heading_level_val = 0
            heading_text_val = ""

        # If not a valid heading, treat as section content
        if not heading_match:
            if current_section is None:
                # Start new <root> section for content before first heading
                current_section = {
                    "heading": "<root>",
                    "heading_level": 0,
                    "heading_path": "",
                    "content_lines": [],
                    "start_line": i + 1,
                    "parent_heading": None,
                }
            if current_section is not None:
                current_section["content_lines"].append(line)
            i += 1
            continue

        # Save previous section before starting a new one
        if current_section is not None and current_section["content_lines"]:
            sections.append(_finalize_section(current_section))

        # Update heading stack (pop ancestors of this level)
        while heading_stack and heading_stack[-1][0] >= heading_level_val:
            heading_stack.pop()

        # Build heading path from ancestors
        heading_path = " > ".join(h[1] for h in heading_stack) if heading_stack else ""

        # Compute ordinal among same-level headings
        same_level_headings = [h for h in heading_stack if h[0] == heading_level_val]
        ordinal = len(same_level_headings) + 1

        parent_heading = heading_stack[-1][1] if heading_stack else None

        current_section = {
            "heading": heading_text_val,
            "heading_level": heading_level_val,
            "heading_path": heading_path,
            "content_lines": [],
            "start_line": i + 1,
            "parent_heading": parent_heading,
        }

        # Update heading stack with this heading
        heading_stack.append((heading_level_val, heading_text_val))

        i += 1

    # Save the last section
    if current_section is not None and current_section["content_lines"]:
        sections.append(_finalize_section(current_section))

    return sections


def _finalize_section(section: dict) -> ParsedSection:
    """Convert a raw section dict to a finalized ParsedSection."""
    content = "\n".join(section["content_lines"]).strip()
    return {
        "heading": section["heading"],
        "heading_level": section["heading_level"],
        "heading_path": section["heading_path"],
        "content": content,
        "start_line": section["start_line"],
        "end_line": section["start_line"] + len(section["content_lines"]),
        "ordinal": section.get("ordinal", 0),
        "parent_heading": section["parent_heading"],
    }


def _parse_atx_heading(line: str) -> tuple[int, str] | None:
    """Parse an ATX-style heading. Returns (level, text) or None."""
    if not line.startswith("#"):
        return None
    level = 0
    for ch in line:
        if ch == "#":
            level += 1
        else:
            break
    if level <= 6 and len(line) > level and line[level] == " ":
        text = line[level + 1:].strip()
        return (level, text)
    return None
