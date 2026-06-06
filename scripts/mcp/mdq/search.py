#!/usr/bin/env python3
"""mcp/mdq/search.py
Search functionality using FTS5.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mcp.mdq.models import SearchDocsRequest

if TYPE_CHECKING:
    from mcp.mdq.service import MdqService

logger = logging.getLogger(__name__)


async def search_docs(service: MdqService, req: SearchDocsRequest) -> str:
    """Search indexed Markdown sections by query."""
    logger.info("Searching docs with query: %s", req.query)
    # Placeholder implementation
    # In a real implementation, this would query the FTS5 database
    return f"Search results for: {req.query}"
