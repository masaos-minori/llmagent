# Implementation Procedure: tests/test_validate_artifact.py

## Goal

Add unit tests for `RagIngester._validate_artifact` covering all strict/lenient mode
combinations (Plan 142134 Phase 4). Tests must be fast, pure, and require no DB or filesystem.

## Scope

**In scope:**
- New file `tests/test_validate_artifact.py` OR additions to `tests/test_ingester.py`
  (check which already exists; prefer the existing file if present)
- 7 test cases: 3 lenient-mode, 3 strict-mode field rejections, 1 strict-mode pass

**Out of scope:**
- Integration tests for full ingestion pipeline
- Testing `ingest_url_group` or `_embed_and_store` flag pass-through (covered separately)

## Assumptions

1. `_validate_artifact` is a `@staticmethod` accessible without constructing a full
   `RagIngester` instance: `RagIngester._validate_artifact(payload, expected_type, strict=...)`.
2. `ChunkJsonRaw` is a `TypedDict`; test payloads can be plain `dict` literals that pass
   structural type checking.
3. The `artifact_type` mismatch check applies in both strict and lenient modes.
4. `tests/test_ingester.py` may already exist; read it first to decide whether to add a class
   or create a new file.

## Implementation

### Target file

`tests/test_validate_artifact.py` (or `tests/test_ingester.py`)

### Procedure

1. Check if `tests/test_ingester.py` exists. If yes, add `TestValidateArtifact` class there.
   If no, create `tests/test_validate_artifact.py`.
2. Import: `from scripts.rag.ingestion.ingester import RagIngester`
3. Add parametrized tests (or individual methods) covering:

```python
class TestValidateArtifact:
    BASE_PAYLOAD = {
        "artifact_type": "chunk",
        "schema_version": "1",
        "created_by": "chunk_splitter",
    }

    def test_lenient_missing_schema_version_passes(self):
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "schema_version"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=False) is True

    def test_lenient_missing_created_by_passes(self):
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "created_by"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=False) is True

    def test_lenient_wrong_artifact_type_rejects(self):
        assert RagIngester._validate_artifact(self.BASE_PAYLOAD, "image", strict=False) is False

    def test_strict_missing_schema_version_rejects(self):
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "schema_version"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=True) is False

    def test_strict_missing_artifact_type_rejects(self):
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "artifact_type"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=True) is False

    def test_strict_missing_created_by_rejects(self):
        payload = {k: v for k, v in self.BASE_PAYLOAD.items() if k != "created_by"}
        assert RagIngester._validate_artifact(payload, "chunk", strict=True) is False

    def test_strict_all_fields_correct_type_passes(self):
        assert RagIngester._validate_artifact(self.BASE_PAYLOAD, "chunk", strict=True) is True
```

## Validation plan

| Step | Command | Expected result |
|------|---------|----------------|
| Run new tests | `uv run pytest tests/test_validate_artifact.py -x -q` | all PASSED |
| Existing tests | `uv run pytest tests/test_ingester.py -x -q` | no regressions |
| Lint | `ruff check tests/test_validate_artifact.py` | 0 errors |
| Type check | `mypy tests/test_validate_artifact.py` | no new errors |
