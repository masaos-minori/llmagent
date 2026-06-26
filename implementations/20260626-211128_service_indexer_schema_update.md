# Goal

Update mdq-mcp operational code to use new documents/chunks schema instead of legacy sections table.

## Scope

**In-Scope**:
- Update `scripts/mcp/mdq/indexer.py` — write to documents/chunks tables, compute content_hash
- Update `scripts/mcp/mdq/service.py` — update stats(), get_chunk(), grep_docs() to use new schema
- Update `scripts/mcp/mdq/search.py` — query chunks_fts instead of sections_fts
- Update `scripts/mcp/mdq/models.py` — change chunk_id types from int to str

**Out-of-Scope**:
- Token counting implementation (placeholder for now)
- Adding new tools or features

## Assumptions

1. content_hash uses SHA-256 of the content text
2. normalized_content = content with extra whitespace collapsed
3. doc_id = SHA-256 hash of source_path for stability
4. chunk_id = SHA-256 hash of (doc_id + heading + start_line) for uniqueness

## Implementation

### Target file 1: `scripts/mcp/mdq/indexer.py`

#### Procedure

1. Add hashlib import for content_hash computation
2. Replace DELETE FROM sections with DELETE FROM chunks where doc_id = ?
3. Replace INSERT INTO sections with INSERT INTO documents (upsert) and INSERT INTO chunks
4. Compute and store content_hash for both documents and chunks
5. Compute and store normalized_content, char_count

#### Method

Use Edit tool to replace the indexing logic in indexer.py.

#### Details

```python
# Add at top of file:
import hashlib

# Replace lines 39-50 (index_paths function):
# Before:
conn.execute("DELETE FROM sections WHERE file_path = ?", (str(path),))
for section in sections:
    conn.execute(
        "INSERT INTO sections (file_path, heading, content, file_mtime) VALUES (?, ?, ?, ?)",
        (str(path), section["heading"], section["content"], path.stat().st_mtime),
    )

# After:
doc_id = hashlib.sha256(str(path).encode()).hexdigest()
content_hash = hashlib.sha256(section["content"].encode()).hexdigest()
normalized_content = " ".join(section["content"].split())
char_count = len(section["content"])

# Upsert document (INSERT OR REPLACE)
conn.execute(
    "INSERT OR REPLACE INTO documents (doc_id, source_path, mtime_ns, size_bytes, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?, ?)",
    (doc_id, str(path), int(path.stat().st_mtime_ns), path.stat().st_size, content_hash, now),
)

# Insert chunk with new schema
conn.execute(
    "INSERT INTO chunks (chunk_id, doc_id, source_path, heading, heading_path, heading_level, ordinal, content, normalized_content, start_line, end_line, char_count, token_count, content_hash, tags_json, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (
        hashlib.sha256(f"{doc_id}:{section['heading']}:{section['start_line']}".encode()).hexdigest(),
        doc_id,
        str(path),
        section["heading"],
        section.get("heading_path", ""),
        section.get("heading_level", 0),
        section.get("ordinal", 0),
        section["content"],
        normalized_content,
        section["start_line"],
        section["end_line"],
        char_count,
        None,  # token_count placeholder
        content_hash,
        json.dumps(section.get("tags", [])),
        now,
    ),
)

# Delete old chunks for this document
conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
```

### Target file 2: `scripts/mcp/mdq/service.py`

#### Procedure

1. Update stats() method to query new schema
2. Update get_chunk() method to query chunks table
3. Update grep_docs() method to query chunks/chunks_fts

#### Method

Use Edit tool to replace the affected methods in service.py.

#### Details

**stats() method replacement (lines 344-356):**
```python
def stats(self) -> StatsResponse:
    """Return index statistics."""
    conn = self._db_conn
    chunk_count = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()["cnt"]
    doc_count = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()["cnt"]
    
    # Get index metadata from index_state table
    rows = conn.execute("SELECT key, value FROM index_state").fetchall()
    index_metadata = dict((row["key"], row["value"]) for row in rows)
    
    return StatsResponse(
        document_count=doc_count,
        chunk_count=chunk_count,
        index_metadata=index_metadata,
    )
```

**get_chunk() method replacement (lines 299-311):**
```python
def get_chunk(self, req: GetChunkRequest) -> ChunkRecord:
    """Retrieve a single chunk by its chunk_id."""
    conn = self._db_conn
    row = conn.execute(
        "SELECT * FROM chunks WHERE chunk_id = ?", (req.chunk_id,)
    ).fetchone()
    if not row:
        raise MdqServiceError(f"Chunk not found: {req.chunk_id}")
    
    # Convert row to ChunkRecord TypedDict
    return ChunkRecord(
        chunk_id=row["chunk_id"],
        doc_id=row["doc_id"],
        source_path=row["source_path"],
        heading=row["heading"],
        heading_path=row["heading_path"],
        heading_level=row["heading_level"],
        ordinal=row["ordinal"],
        content=row["content"],
        normalized_content=row["normalized_content"],
        start_line=row["start_line"],
        end_line=row["end_line"],
        char_count=row["char_count"],
        token_count=row["token_count"],
        content_hash=row["content_hash"],
        tags=row.get("tags_json"),  # TODO: parse JSON
        indexed_at=row["indexed_at"],
    )
```

**grep_docs() method replacement (lines 358-378):**
```python
def grep_docs(self, req: GrepDocRequest) -> list[GrepDocMatch]:
    """Search for content within indexed documents using FTS5."""
    conn = self._db_conn
    
    # Use chunks_fts for FTS search
    rows = conn.execute(
        "SELECT chunk_id, source_path, heading FROM chunks_fts WHERE chunks_fts MATCH ?",
        (req.query,),
    ).fetchall()
    
    matches = []
    for row in rows:
        matches.append(GrepDocMatch(
            chunk_id=row["chunk_id"],
            source_path=row["source_path"],
            heading=row["heading"],
        ))
    
    return matches
```

### Target file 3: `scripts/mcp/mdq/search.py`

#### Procedure

1. Replace sections_fts queries with chunks_fts queries
2. Update joins to use chunks table instead of sections

#### Method

Use Edit tool to replace the affected queries in search.py.

#### Details

```python
# Replace lines 46-53 (FTS search query):
# Before:
fts_query = f"""
    SELECT s.id, s.file_path, s.heading, s.content
    FROM sections_fts s
    JOIN sections s2 ON s.id = s2.id
    WHERE sections_fts MATCH ?
    ORDER BY sections_fts.rank
    LIMIT ? OFFSET ?
"""

# After:
fts_query = f"""
    SELECT c.chunk_id, c.source_path, c.heading, c.content
    FROM chunks_fts cf
    JOIN chunks c ON cf.chunk_id = c.chunk_id
    WHERE chunks_fts MATCH ?
    ORDER BY chunks_fts.rank
    LIMIT ? OFFSET ?
"""

# Replace lines 57-64 (count query):
# Before:
count_query = "SELECT COUNT(*) FROM sections_fts WHERE sections_fts MATCH ?"

# After:
count_query = "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts MATCH ?"
```

### Target file 4: `scripts/mcp/mdq/models.py`

#### Procedure

1. Change GetChunkRequest.chunk_id type from int to str
2. Change GrepDocMatch.chunk_id type from int to str

#### Method

Use Edit tool to replace the affected type annotations in models.py.

#### Details

```python
# Line 70: Change chunk_id type
class GetChunkRequest(BaseModel):
    chunk_id: str  # was: int

# Line 133: Change chunk_id type
class GrepDocMatch(BaseModel):
    chunk_id: str  # was: int
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| indexer.py | Verify indexing writes to documents/chunks tables | Create test file, run index_paths | New records in documents and chunks tables |
| indexer.py | Verify content_hash is computed | Check document record content_hash field | SHA-256 hash present |
| service.py | Verify stats() returns correct counts | Call stats() method | document_count and chunk_count match DB |
| service.py | Verify get_chunk() returns chunk by ID | Call get_chunk with known chunk_id | ChunkRecord returned with all fields |
| service.py | Verify grep_docs() uses FTS5 search | Call grep_docs with known query | Matches from chunks_fts |
| search.py | Verify FTS search queries chunks_fts | Run search with known query | Results from chunks_fts, not sections_fts |
| models.py | Verify chunk_id is str type | Check type annotations | str, not int |