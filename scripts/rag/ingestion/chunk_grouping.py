#!/usr/bin/env python3
"""scripts/rag/ingestion/chunk_grouping.py

Isolate URL-based chunk aggregation from ingester.py into ChunkGroupingStrategy class.

ChunkGroupingStrategy owns the logic for grouping chunk files by their
(url, generation signature) — this is a pure data transformation concern.
Files from different crawl generations of the same URL never share a group,
and every file the grouping skips is reported to the caller as a rejected
(path, reason) pair.
"""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from rag.exceptions import ChunkFormatError, IngestionFailureReason
from rag.ingestion.pipeline_utils import read_chunk_json
from rag.models_data import ChunkDocument
from rag.utils import validate_url
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/ingest.log")


@dataclass(frozen=True)
class ChunkGeneration:
    """Generation signature of one chunk file: url plus the 9 payload fields.

    Equal signatures mean the files come from the same crawl generation, so
    they may be ingested as one document group. The field set matches exactly
    what `ingest_url_group` compares as its defense-in-depth group check.
    """

    url: str
    title: str
    lang: str
    fetched_at: str
    etag: str | None
    last_modified: str | None
    source_file: str
    chunking_strategy: str
    chunk_type: str

    @classmethod
    def from_document(cls, data: ChunkDocument) -> "ChunkGeneration":
        """Build the signature from the fields read_chunk_json already validated."""
        return cls(
            url=data.url,
            title=data.title,
            lang=data.lang,
            fetched_at=data.fetched_at,
            etag=data.etag,
            last_modified=data.last_modified,
            source_file=data.source_file,
            chunking_strategy=data.chunking_strategy,
            chunk_type=data.chunk_type,
        )


class ChunkGroupingStrategy:
    """Group chunk files by (url, generation signature) and report rejected files."""

    def group(
        self, chunk_files: list[Path]
    ) -> tuple[
        dict[ChunkGeneration, list[Path]], list[tuple[Path, IngestionFailureReason]]
    ]:
        """Group chunk files by generation signature; return (groups, rejected).

        Rejected entries are (path, reason): `parse_failed` for unreadable or
        malformed payloads, `validation_failed` for urls that fail validation.
        Every rejected file also produces a per-file WARNING. Routing is left
        to the caller; this method moves nothing.
        """
        groups: dict[ChunkGeneration, list[Path]] = defaultdict(list)
        rejected: list[tuple[Path, IngestionFailureReason]] = []
        for path in chunk_files:
            try:
                data = read_chunk_json(path)
            except ChunkFormatError as e:
                logger.warning(
                    "chunk rejected (parse_failed): %s: %s",
                    path.name,
                    e,
                    extra={"source_type": "file", "stage_name": "ingester"},
                )
                rejected.append((path, IngestionFailureReason.PARSE_FAILED))
                continue
            url: str = data.url or ""
            if not url:
                logger.warning(
                    "url field missing: %s",
                    path.name,
                    extra={"source_type": "file", "stage_name": "ingester"},
                )
                rejected.append((path, IngestionFailureReason.VALIDATION_FAILED))
                continue
            # Accept file:// URLs from local file ingestion in addition to http/https
            if not validate_url(url) and not url.startswith("file://"):
                logger.warning(
                    "invalid url %r in %s, skipping",
                    url,
                    path.name,
                    extra={"source_type": "file", "stage_name": "ingester"},
                )
                rejected.append((path, IngestionFailureReason.VALIDATION_FAILED))
                continue
            groups[ChunkGeneration.from_document(data)].append(path)
        return dict(groups), rejected
