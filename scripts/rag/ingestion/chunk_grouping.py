#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_grouping.py

Isolate URL-based chunk aggregation from ingester.py into ChunkGroupingStrategy class.

ChunkGroupingStrategy owns the logic for grouping chunk files by their URL field —
this is a pure data transformation concern.
"""

from collections import defaultdict
from pathlib import Path

from rag.exceptions import ChunkFormatError
from rag.ingestion.pipeline_utils import read_chunk_json
from rag.utils import validate_url
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


class ChunkGroupingStrategy:
    """Group chunk files by URL read from their JSON 'url' field."""

    def group(self, chunk_files: list[Path]) -> dict[str, list[Path]]:
        """Group chunk files by URL read from their JSON 'url' field."""
        url_groups: dict[str, list[Path]] = defaultdict(list)
        for path in chunk_files:
            try:
                data = read_chunk_json(path)
            except ChunkFormatError:
                continue
            url: str = data.url or ""
            if not url:
                logger.warning(
                    "url field missing: %s",
                    path.name,
                    extra={"source_type": "file", "stage_name": "ingester"},
                )
                continue
            # Accept file:// URLs from local file ingestion in addition to http/https
            if not validate_url(url) and not url.startswith("file://"):
                logger.warning(
                    "invalid url %r in %s, skipping",
                    url,
                    path.name,
                    extra={"source_type": "file", "stage_name": "ingester"},
                )
                continue
            url_groups[url].append(path)
        return url_groups
