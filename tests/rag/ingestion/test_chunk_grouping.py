#!/usr/bin/env python3
"""tests/rag/ingestion/test_chunk_grouping.py

Unit tests for ChunkGroupingStrategy: generation-safe grouping key and
rejected-file reporting.

REQ-001: two crawl generations of one URL form distinct groups.
REQ-002: skipped files are reported as a rejected (path, reason) list.
REQ-006: every grouping skip produces a per-file WARNING.
"""

import dataclasses
import logging
from pathlib import Path

import orjson
import rag.ingestion.chunk_grouping as chunk_grouping_module
from rag.exceptions import IngestionFailureReason
from rag.ingestion.chunk_grouping import ChunkGroupingStrategy


class _ListHandler(logging.Handler):
    """Capture LogRecords on a logger that propagates=False, without caplog."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _capture_warnings():
    """Attach a capturing handler to the chunk_grouping module logger."""
    return _ListHandler()


def _payload(**overrides) -> dict:
    data = {
        "url": "https://example.com/doc",
        "content": "本文",
        "title": "Test Doc",
        "lang": "ja",
        "code_blocks": [],
        "etag": None,
        "last_modified": None,
        "normalized_content": None,
        "chunk_index": 0,
        "source_file": "doc.json",
        "chunk_type": "text",
        "chunking_strategy": "heading",
        "fetched_at": "2024-01-01T00:00:00Z",
    }
    data.update(overrides)
    return data


def _write_chunk(dest_dir: Path, filename: str, data: dict) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    path.write_bytes(orjson.dumps(data))
    return path


def _group(strategy: ChunkGroupingStrategy, files: list[Path]):
    """Call group() and normalize the rejected list to (name, reason) pairs."""
    result = strategy.group(files)
    groups, rejected = result
    return groups, [(p.name, reason) for p, reason in rejected]


class TestGenerationSafeKey:
    """REQ-001: group key separates crawl generations of the same URL."""

    def test_two_generations_form_distinct_groups(self, tmp_path: Path) -> None:
        old0 = _write_chunk(
            tmp_path, "doc-0000.json", _payload(fetched_at="2024-01-01T00:00:00Z")
        )
        old1 = _write_chunk(
            tmp_path, "doc-0001.json", _payload(fetched_at="2024-01-01T00:00:00Z")
        )
        new0 = _write_chunk(
            tmp_path, "doc2-0000.json", _payload(fetched_at="2025-06-01T00:00:00Z")
        )

        groups, rejected = _group(ChunkGroupingStrategy(), [old0, old1, new0])

        assert rejected == []
        assert len(groups) == 2
        members = sorted(sorted(p.name for p in paths) for paths in groups.values())
        assert members == [["doc-0000.json", "doc-0001.json"], ["doc2-0000.json"]]

    def test_generation_distinguished_by_etag(self, tmp_path: Path) -> None:
        first = _write_chunk(tmp_path, "a.json", _payload(etag='"etag-1"'))
        second = _write_chunk(tmp_path, "b.json", _payload(etag='"etag-2"'))

        groups, _ = _group(ChunkGroupingStrategy(), [first, second])

        assert len(groups) == 2

    def test_same_generation_files_share_one_group(self, tmp_path: Path) -> None:
        files = [
            _write_chunk(tmp_path, f"doc-{i:04d}.json", _payload(chunk_index=i))
            for i in range(3)
        ]

        groups, rejected = _group(ChunkGroupingStrategy(), files)

        assert rejected == []
        assert len(groups) == 1
        assert sorted(p.name for p in next(iter(groups.values()))) == [
            "doc-0000.json",
            "doc-0001.json",
            "doc-0002.json",
        ]

    def test_group_key_carries_url_and_fetched_at(self, tmp_path: Path) -> None:
        path = _write_chunk(tmp_path, "doc.json", _payload())

        groups, _ = _group(ChunkGroupingStrategy(), [path])

        (key,) = groups.keys()
        assert key.url == "https://example.com/doc"
        assert key.fetched_at == "2024-01-01T00:00:00Z"


class TestRejectedReporting:
    """REQ-002: skipped files are returned with an explicit reason."""

    def test_malformed_payload_reports_parse_failed(self, tmp_path: Path) -> None:
        good = _write_chunk(tmp_path, "good.json", _payload())
        broken = _write_chunk(
            tmp_path,
            "broken.json",
            {"url": "https://example.com/doc", "chunk_index": 0},
        )

        groups, rejected = _group(ChunkGroupingStrategy(), [good, broken])

        assert rejected == [("broken.json", IngestionFailureReason.PARSE_FAILED)]
        assert all(p.name != "broken.json" for paths in groups.values() for p in paths)

    def test_out_of_domain_chunk_type_reports_parse_failed(
        self, tmp_path: Path
    ) -> None:
        # seq-2: read_chunk_json rejects chunk_type outside ('text','code'), which
        # reaches grouping as a ChunkFormatError and is classified PARSE_FAILED.
        good = _write_chunk(tmp_path, "good.json", _payload())
        bad = _write_chunk(tmp_path, "bad.json", _payload(chunk_type="chunk"))

        groups, rejected = _group(ChunkGroupingStrategy(), [good, bad])

        assert rejected == [("bad.json", IngestionFailureReason.PARSE_FAILED)]
        assert list(groups.values()) == [[good]]

    def test_empty_url_reports_parse_failed(self, tmp_path: Path) -> None:
        # read_chunk_json validates 'url' as a non-empty string, so an empty
        # url reaches the grouping layer as a ChunkFormatError.
        path = _write_chunk(tmp_path, "empty.json", _payload(url=""))

        groups, rejected = _group(ChunkGroupingStrategy(), [path])

        assert rejected == [("empty.json", IngestionFailureReason.PARSE_FAILED)]
        assert groups == {}

    def test_invalid_url_reports_validation_failed(self, tmp_path: Path) -> None:
        path = _write_chunk(tmp_path, "bad.json", _payload(url="not-a-url"))

        groups, rejected = _group(ChunkGroupingStrategy(), [path])

        assert rejected == [("bad.json", IngestionFailureReason.VALIDATION_FAILED)]
        assert groups == {}

    def test_file_url_is_accepted(self, tmp_path: Path) -> None:
        path = _write_chunk(tmp_path, "local.json", _payload(url="file:///data/doc.md"))

        groups, rejected = _group(ChunkGroupingStrategy(), [path])

        assert rejected == []
        assert len(groups) == 1


class TestSkipWarnings:
    """REQ-006: every grouping skip logs a per-file WARNING."""

    def _run(self, strategy: ChunkGroupingStrategy, files: list[Path]):
        handler = _capture_warnings()
        chunk_grouping_module.logger.addHandler(handler)
        try:
            groups, rejected = _group(strategy, files)
        finally:
            chunk_grouping_module.logger.removeHandler(handler)
        return groups, rejected, handler.records

    def test_malformed_payload_logs_warning(self, tmp_path: Path) -> None:
        broken = _write_chunk(tmp_path, "broken.json", {"url": "https://a.example.com"})

        _, rejected, records = self._run(ChunkGroupingStrategy(), [broken])

        warnings = [r for r in records if r.levelno == logging.WARNING]
        assert rejected == [("broken.json", IngestionFailureReason.PARSE_FAILED)]
        assert any("broken.json" in r.getMessage() for r in warnings)

    def test_empty_url_logs_warning(self, tmp_path: Path) -> None:
        path = _write_chunk(tmp_path, "empty.json", _payload(url=""))

        _, rejected, records = self._run(ChunkGroupingStrategy(), [path])

        warnings = [r for r in records if r.levelno == logging.WARNING]
        assert rejected == [("empty.json", IngestionFailureReason.PARSE_FAILED)]
        assert any("empty.json" in r.getMessage() for r in warnings)

    def test_invalid_url_logs_warning(self, tmp_path: Path) -> None:
        path = _write_chunk(tmp_path, "bad.json", _payload(url="not-a-url"))

        _, rejected, records = self._run(ChunkGroupingStrategy(), [path])

        warnings = [r for r in records if r.levelno == logging.WARNING]
        assert rejected == [("bad.json", IngestionFailureReason.VALIDATION_FAILED)]
        assert any("not-a-url" in r.getMessage() for r in warnings)

    def test_no_warning_for_accepted_files(self, tmp_path: Path) -> None:
        path = _write_chunk(tmp_path, "ok.json", _payload())

        _, rejected, records = self._run(ChunkGroupingStrategy(), [path])

        warnings = [r for r in records if r.levelno == logging.WARNING]
        assert rejected == []
        assert warnings == []


def test_chunk_generation_dataclass_is_hashable_and_frozen() -> None:
    """The grouping key is a value object usable as a dict key."""
    from rag.ingestion.chunk_grouping import ChunkGeneration

    key = ChunkGeneration(
        url="https://example.com/doc",
        title="Test Doc",
        lang="ja",
        fetched_at="2024-01-01T00:00:00Z",
        etag=None,
        last_modified=None,
        source_file="doc.json",
        chunking_strategy="heading",
        chunk_type="paragraph",
    )
    other = dataclasses.replace(key, fetched_at="2025-06-01T00:00:00Z")

    assert hash(key) == hash(dataclasses.replace(key))
    assert key != other
    assert {key: [Path("x")]}[key] == [Path("x")]
