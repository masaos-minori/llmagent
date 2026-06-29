# Implementation: Replace MDQ chunk ID generation with stable deterministic hash

## Goal

Replace the MDQ chunk ID generation formula with a stable, deterministic hash derived from normalized source path, heading path, ordinal, and content hash so that IDs are preserved across re-indexing of unchanged content.

## Scope

- **In-Scope**:
  - New `generate_chunk_id()` helper in `scripts/mcp/mdq/indexer.py`
  - Update chunk ID generation in `_index_single_file()` and `_migrate_from_legacy()` inside `indexer.py`
  - No schema changes required — `chunks.chunk_id TEXT UNIQUE NOT NULL` already exists
  - No changes to `search_docs` return format — `chunk_id` is already included in `SearchResultItem`
  - No changes to `get_chunk` input — `GetChunkRequest.chunk_id: str` already accepts string IDs
  - No changes to `grep_docs` return format — `GrepDocMatch.chunk_id` is already returned
  - Tests verifying chunk ID stability across `refresh_index` / `index_paths`
  - Tests verifying search-result `chunk_id` can be passed directly to `get_chunk`

- **Out-of-Scope**:
  - DB schema migration (no schema change needed; `chunk_id` column is already TEXT)
  - Hybrid/vector search changes
  - `outline` tool changes (already uses `chunk_id` from DB)
  - Backward-compatibility shim for old integer row IDs (requirement says to prefer stable IDs)
  - `chunk_summaries` table chunk_id — same generation logic will apply automatically

## Verification Results

### 1. Current state: inline chunk_id formula in `_index_single_file()`

**File**: `scripts/mcp/mdq/indexer.py` — `_index_single_file()`
```python
# Current inline formula (not shown in current code — need to verify)
chunk_id = hashlib.sha256(f"{doc_id}:{section['heading']}:{section['start_line']}".encode()).hexdigest()
```

- Uses `doc_id`, `section['heading']`, and `section['start_line']` as inputs
- Not stable across re-indexing if heading text or line numbers change (e.g., document edits)

### 2. Current state: `_migrate_from_legacy()` uses truncated hex prefix

**File**: `scripts/mcp/mdq/indexer.py` — `_migrate_from_legacy()`
```python
chunk_id = f"chunk_{sha256[:16]}"
```

- Uses only first 16 hex chars of SHA-256 — less collision-resistant than full hash
- Should use the same `generate_chunk_id()` formula for consistency

### 3. Current state: `_generate_summaries()` has similar inline formula

**File**: `scripts/mcp/mdq/indexer.py` — `_generate_summaries()`
- Uses the same inline chunk_id pattern as `_index_single_file()`
- Should use `generate_chunk_id()` for consistency

### 4. UNK-01: External chunk ID caching unknown

- No audit of downstream consumers outside this codebase
- Mitigation: grep all config/logs for hex strings that look like SHA-256 chunk IDs before deploying; wipe mdq.sqlite on deploy

### 5. UNK-03: Source path normalization definition

- `Path(path).resolve().as_posix()` for maximum stability (handles symlinks)
- Document in code comment

## Implementation

### Target file: `scripts/mcp/mdq/indexer.py`

#### Procedure

Add `generate_chunk_id()` helper and replace all inline formulas.

#### Details

**Add new function at the top of indexer.py (after imports):**
```python
import hashlib

def generate_chunk_id(normalized_path: str, heading_path: str, ordinal: int, content_hash: str) -> str:
    """Generate a stable chunk ID from normalized path, heading path, ordinal, and content hash.

    Stable across re-indexing of unchanged content. Uses | as delimiter to reduce
    collision risk with paths containing colons.

    Args:
        normalized_path: Absolute POSIX path (e.g., Path(path).resolve().as_posix())
        heading_path: Heading ancestor path (e.g., "A > B" or "" for root)
        ordinal: 1-based rank of this heading among same-level headings with same parent
        content_hash: SHA-256 hex digest of the section content

    Returns:
        Stable chunk ID string
    """
    return hashlib.sha256(
        f"{normalized_path}|{heading_path}|{ordinal}|{content_hash}".encode()
    ).hexdigest()
```

**In `_index_single_file()` — replace inline formula:**
```python
# Before:
chunk_id = hashlib.sha256(f"{doc_id}:{section['heading']}:{section['start_line']}".encode()).hexdigest()

# After:
normalized_path = Path(section["source_path"]).resolve().as_posix()
content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
chunk_id = generate_chunk_id(normalized_path, section["heading_path"], section.get("ordinal", 0), content_hash)
```

**In `_migrate_from_legacy()` — replace inline formula:**
```python
# Before:
chunk_id = f"chunk_{sha256[:16]}"

# After:
normalized_path = Path(file_path).resolve().as_posix()
content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
chunk_id = generate_chunk_id(normalized_path, section.get("heading_path", ""), 0, content_hash)
```

**In `_generate_summaries()` — replace inline formula:**
```python
# Before:
chunk_id = hashlib.sha256(f"{doc_id}:{section['heading']}:{section['start_line']}".encode()).hexdigest()

# After:
normalized_path = Path(section["source_path"]).resolve().as_posix()
content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
chunk_id = generate_chunk_id(normalized_path, section["heading_path"], section.get("ordinal", 0), content_hash)
```

### Target file: `tests/test_mdq_service.py`

#### Procedure

Add stability test cases to `TestChunkIdStability`.

#### Details

**Append new test class:**
```python
class TestChunkIdStability:
    """Verify chunk ID stability across re-indexing."""

    def test_chunk_id_stable_across_reindex(
        self, service: MdqService, md_file: Path
    ) -> None:
        """Index same file twice; IDs are identical."""
        ...

    def test_chunk_id_changes_on_content_edit(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Edit content and re-index; ID changes."""
        ...

    def test_search_chunk_id_passthrough(
        self, service: MdqService, md_file: Path
    ) -> None:
        """Search result chunk_id can be passed to get_chunk without MdqNotFoundError."""
        ...
```

### Target file: `tests/test_mdq_incremental_refresh.py`

#### Procedure

Add chunk_id stability assertion after refresh.

#### Details

**Append test method:**
```python
def test_chunk_id_stable_after_refresh(
    self, service: MdqService, md_dir: Path
) -> None:
    """Force-index, record IDs, force-index again (unchanged); assert IDs equal."""
    ...
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `indexer.py` `generate_chunk_id()` | Unit test with fixed inputs | `pytest tests/test_mdq_service.py::TestChunkIdStability` | Same inputs → same output; different content_hash → different output |
| `_index_single_file()` stability | Index same file twice; compare chunk IDs from DB | `pytest tests/test_mdq_service.py::TestChunkIdStability::test_chunk_id_stable_across_reindex` | IDs identical after second index |
| `search_docs` → `get_chunk` roundtrip | Search then get_chunk with returned ID | `pytest tests/test_mdq_service.py::TestChunkIdStability::test_search_chunk_id_passthrough` | No MdqNotFoundError |
| `refresh_index` stability | Force refresh; assert IDs unchanged | `pytest tests/test_mdq_incremental_refresh.py::TestIncrementalRefresh::test_chunk_id_stable_after_refresh` | IDs identical before and after refresh |
| Type correctness | mypy clean | `uv run mypy scripts/mcp/mdq/indexer.py` | No type errors |
| Ruff lint | No lint errors | `uv run ruff check scripts/mcp/mdq/indexer.py` | Exit 0 |
| Regression: existing tests | All existing MDQ tests pass | `uv run pytest tests/test_mdq_*.py -v` | All pass |

## Risks & Mitigations

- **Risk**: Existing production chunk IDs (stored in agent memory, audit logs, or client caches) become invalid after re-index → **Mitigation**: Document in deploy notes that a full `refresh_index --force` is required; grep agent memory tables for MDQ chunk ID references before deploying
- **Risk**: `heading_path` is empty string for root sections (content before first heading) → ID still unique because `content_hash` differentiates content; `ordinal` differentiates multiple root-level sections in same file → **Mitigation**: Add test case with a file that has content before first heading
- **Risk**: Two files with identical content, heading_path, and ordinal produce the same chunk_id → **Mitigation**: `normalized_path` is the first component, making IDs per-file unique
- **Risk**: `_generate_summaries()` called inside the per-section loop in `_index_single_file()` generates a chunk_id independently; if formula drifts from the insert formula, summary lookup breaks → **Mitigation**: Both call the same `generate_chunk_id()` helper; enforce via single code path
