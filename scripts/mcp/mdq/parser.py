#!/usr/bin/env python3
"""mcp/mdq/parser.py
Markdown parsing functionality — heading-based section extraction.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from mcp.mdq.models import ParseMarkdownRequest

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def parse_markdown(service: MdqService, req: ParseMarkdownRequest) -> list[dict]:
    """Parse a Markdown file and return its sections as a list of dicts.

    Each dict has keys: heading, content.
    """
    logger.info("Parsing Markdown file: %s", req.path)
    path = Path(req.path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {req.path}")

    content = path.read_text(encoding="utf-8")
    sections: list[dict] = []

    current_heading = ""
    current_content: list[str] = []
    in_section = False

    for line in content.splitlines():
        stripped = line.rstrip()
        if stripped.startswith("#"):
            # Save previous section if any
            if in_section and current_heading:
                sections.append(
                    {
                        "heading": current_heading,
                        "content": "\n".join(current_content).strip(),
                    }
                )

            # Start new section
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            if heading_level <= 6 and stripped[heading_level:].startswith(" "):
                current_heading = stripped[heading_level + 1 :].strip()
                current_content = []
                in_section = True
            else:
                if in_section:
                    current_content.append(line)
        elif in_section:
            current_content.append(line)
        else:
            # Content before any heading
            if stripped:
                current_heading = "<root>"
                current_content = [line]
                in_section = True

    # Save last section
    if in_section and current_heading:
        sections.append(
            {
                "heading": current_heading,
                "content": "\n".join(current_content).strip(),
            }
        )

    return sections
