# Implementation: Branch-aware memory retrieval — hard SQL branch filter

## Goal

Add hard SQL branch filtering to memory retrieval so that memories tagged to a specific branch are excluded from unrelated branch contexts. Currently, branch is only used for scoring (via `_context_boost`), not as a hard filter.

## Scope

- **In-Scope**:
  - Add hard SQL branch filter `AND (? = '' OR m.branch = '' OR m.branch = ?)` to `FtsRetriever._build_search_query()` and `VectorRetriever.knn_search()`
  - Pass branch from `HybridRetriever.search()` to `VectorRetriever.knn_search()` (currently only passes to FtsRetriever)
  - Fix `MemoryInjectionService.on_user_prompt()` to pass `branch=self._branch` to retriever.search() calls (currently omits this arg despite storing `self._branch`)
  - Add branch context resolution in `factory.py` via `shared.git_helper.get_repo_info()` at build time
  - Add cross-branch isolation tests in `tests/test_memory_retriever.py`
  - Update `docs/05_agent_12_memory.md` to document the branch-awareness contract

- **Out-of-Scope**:
  - Full git integration redesign
  - Replacing the memory metadata model (`MemoryEntry`)
  - Live branch tracking (branch context resolved once at startup)
  - DB schema changes — `branch` column already exists in `memories` table
  - Project/repo context resolution — pre-existing gap, not in scope

## Assumptions

- `shared.git_helper.get_repo_info()` is callable at factory build time without side effects; returns branch from the CWD git repository.
- When `get_repo_info()` fails (not a git repo, detached HEAD, etc.), branch context defaults to `""` (empty = global), and no branch filtering is applied. This is the safe degraded behavior.
- `project` and `repo` context is currently empty strings throughout the memory pipeline — pre-existing gap, not in scope for this ticket.
- "Global" memory is defined as an entry where `branch == ""`. Global memories must always appear in retrieval regardless of current branch.
- The `_context_boost` function in `retriever.py` already applies a small bonus for branch matches; the new hard filter is additive (applied before scoring).
- KNN dedup in `MemoryIngestionService` does NOT need branch filtering — dedup should remain global. Only retrieval/injection paths need the filter.

## Code Verification: Current State

### 1. `FtsRetriever.search()` — accepts `branch` but only uses for scoring (NOT hard filter)

**File**: `scripts/agent/memory/retriever.py:148-163`

```python
def search(
    self,
    query: MemoryQuery,
    project: str = "",
    repo: str = "",
    branch: str = "",
) -> list[MemoryHit]:
    """FTS5 BM25 search; returns [] on error or empty query."""
    fts_query = _build_fts_query(query.query)
    if not fts_query or fts_query == '""':
        return []

    sql, params = self._build_search_query(fts_query, query.memory_type)
    hits = self._fetch_hits(sql, tuple(params), project, repo, branch)  # ← branch passed to _fetch_hits but NOT used as SQL filter
```

**`_build_search_query()` — does NOT include branch in WHERE clause**:

**File**: `scripts/agent/memory/retriever.py:165-187`

```python
def _build_search_query(
    self, fts_query: str, memory_type: str | None
) -> tuple[str, list[object]]:
    """Build FTS5 search SQL and parameter tuple."""
    type_filter = ""
    params: list[object] = [fts_query, self._fts_limit]
    if memory_type:
        type_filter = "AND m.memory_type = ?"
        params.insert(1, memory_type)

    sql = f"""
        SELECT ... FROM memories_fts f
        JOIN memories m ON m.memory_id = f.memory_id
        WHERE memories_fts MATCH ?
        {type_filter}
        ORDER BY f.rank
        LIMIT ?
    """  # ← NO branch filter here — THIS IS THE GAP
```

**`_fetch_hits()` — passes branch to `_score()` only**:

**File**: `scripts/agent/memory/retriever.py:189-208`

```python
def _fetch_hits(
    self, sql: str, params: tuple[object, ...], project: str, repo: str, branch: str = ""
) -> list[MemoryHit]:
    """Execute query and build scored MemoryHit list."""
    with SQLiteHelper("session").open(row_factory=True) as db:
        rows = db.fetchall(sql, params)

    hits: list[MemoryHit] = []
    for row in rows:
        d = dict(row)
        bm25_rank = float(d.pop("bm25_rank", 0.0))
        entry = row_to_entry(d)
        s = _score(bm25_rank, entry, project, repo, self._recency_days, branch)  # ← only for scoring
        hits.append(MemoryHit(entry=entry, score=s))
    return hits
```

### 2. `VectorRetriever.knn_search()` — does NOT accept `branch` param

**File**: `scripts/agent/memory/retriever.py:214-250`

```python
class VectorRetriever:
    """KNN search on memories_vec using sqlite-vec extension."""

    def knn_search(
        self,
        embedding: list[float],
        memory_type: str | None,
        limit: int,
    ) -> list[MemoryHit]:
        """KNN search on memories_vec; raises OperationalError when table missing."""
        type_filter = ""
        params: list[object] = [_floats_to_blob(embedding), limit]
        if memory_type:
            type_filter = "AND m.memory_type = ?"
            params.insert(1, memory_type)

        sql = f"""
            SELECT ... FROM memories_vec mv
            JOIN memories m ON m.memory_id = mv.memory_id
            WHERE mv.embedding MATCH ?
            {type_filter}
            ORDER BY mv.distance
            LIMIT ?
        """  # ← NO branch filter — needs to be added
```

### 3. `HybridRetriever.search()` — passes branch to FtsRetriever but NOT to VectorRetriever

**File**: `scripts/agent/memory/retriever.py:275-307`

```python
def search(
    self,
    query: MemoryQuery,
    embedding: list[float] | None = None,
    project: str = "",
    repo: str = "",
    branch: str = "",
) -> list[MemoryHit]:
    fts_hits = self._fts.search(query, project, repo, branch)  # ← branch passed to FTS
    if embedding is None:
        ...
        return fts_hits

    vec_hits = self._vec.knn_search(
        embedding, query.memory_type, self._fts._fts_limit  # ← NO branch passed here!
    )
```

### 4. `MemoryInjectionService.on_user_prompt()` — does NOT pass branch to retriever

**File**: `scripts/agent/memory/injection.py:31-48`

```python
class MemoryInjectionService:
    def __init__(
        self,
        policy: InjectionPolicy,
        retriever: HybridRetriever,
        embed_client: EmbeddingClient,
        project: str = "",
        repo: str = "",
        branch: str = "",  # ← stored as self._branch
    ) -> None:
        self._policy = policy
        self._retriever = retriever
        self._embed_client = embed_client
        self._project = project
        self._repo = repo
        self._branch = branch
```

**File**: `scripts/agent/memory/injection.py:85-104`

```python
hits_s = self._retriever.search(
    MemoryQuery(query=query, memory_type=MemoryType.SEMANTIC, limit=self._policy.max_semantic),
    embedding=embedding,
    project=self._project,
    repo=self._repo,
)  # ← NO branch=self._branch — THIS IS THE GAP
hits_e = self._retriever.search(
    MemoryQuery(query=query, memory_type=MemoryType.EPISODIC, limit=self._policy.max_episodic),
    embedding=embedding,
    project=self._project,
    repo=self._repo,
)  # ← NO branch=self._branch — THIS IS THE GAP
```

### 5. `factory.py` — does NOT resolve or pass branch context

**File**: `scripts/agent/factory.py:289-306`

```python
def _build_injection_service(
    embed_client: object,
    retriever: object,
    ctx: AgentContext,
    policy_cls: type,
    service_cls: type,
) -> object:
    """Build and return the memory injection service."""
    policy = policy_cls(...)
    return service_cls(
        policy=policy,
        retriever=retriever,
        embed_client=embed_client,
    )  # ← NO branch/project/repo passed to service_cls
```

### 6. Existing pattern: `top_semantic()` already has the hard SQL filter

**File**: `scripts/agent/memory/retriever.py:318-339`

```python
def top_semantic(
    self,
    limit: int = 5,
    min_importance: float = 0.0,
    project: str = "",
    repo: str = "",
    branch: str = "",
) -> list[MemoryEntry]:
    """Return top semantic entries by importance + pin, no FTS needed."""
    with SQLiteHelper("session").open(row_factory=True) as db:
        rows = db.fetchall(
            """SELECT ... FROM memories
               WHERE memory_type = 'semantic' AND importance >= ?
               AND (? = '' OR branch = '' OR branch = ?)  ← THIS IS THE PATTERN TO COPY
               ORDER BY pinned DESC, importance DESC, created_at DESC
               LIMIT ?""",
            (min_importance, branch, branch, limit),
        )
        return [row_to_entry(dict(r)) for r in rows]
```

### 7. Existing tests: `TestBranchBoundary` class already covers `top_semantic`

**File**: `tests/test_memory_retriever.py:720-763`

Tests verify:
- `test_top_semantic_excludes_other_branch` — branch="feat/y" excludes branch="feat/x" entries
- `test_top_semantic_includes_global_memory` — branch="" entries always included
- `test_top_semantic_includes_same_branch` — branch="feat/x" includes branch="feat/x" entries

## Implementation Steps

### Phase 1: Core Logic — Add hard SQL branch filter to retrievers

#### 1.1 `FtsRetriever._build_search_query()` — add branch WHERE clause

**File**: `scripts/agent/memory/retriever.py:165-187`

```python
def _build_search_query(
    self, fts_query: str, memory_type: str | None, branch: str = ""
) -> tuple[str, list[object]]:
    """Build FTS5 search SQL and parameter tuple."""
    type_filter = ""
    params: list[object] = [fts_query, self._fts_limit]
    if memory_type:
        type_filter = "AND m.memory_type = ?"
        params.insert(1, memory_type)

    branch_filter = ""
    if branch:
        branch_filter = "AND (? = '' OR m.branch = '' OR m.branch = ?)"
        params.insert(2, branch)  # placeholder for empty-branch check
        params.insert(4, branch)  # placeholder for branch match check

    sql = f"""
        SELECT m.memory_id, m.memory_type, m.source_type, m.session_id, m.turn_id,
               m.project, m.repo, m.branch, m.content, m.summary, m.tags,
               m.importance, m.pinned, m.created_at, m.updated_at,
               f.rank AS bm25_rank
        FROM memories_fts f
        JOIN memories m ON m.memory_id = f.memory_id
        WHERE memories_fts MATCH ?
        {type_filter}
        {branch_filter}
        ORDER BY f.rank
        LIMIT ?
    """  # nosec B608 — type_filter and branch_filter are literal strings; all values use ? placeholders
    return sql, params
```

#### 1.2 `FtsRetriever.search()` — forward branch to `_build_search_query`

**File**: `scripts/agent/memory/retriever.py:148-163`

```python
def search(
    self,
    query: MemoryQuery,
    project: str = "",
    repo: str = "",
    branch: str = "",
) -> list[MemoryHit]:
    """FTS5 BM25 search; returns [] on error or empty query."""
    fts_query = _build_fts_query(query.query)
    if not fts_query or fts_query == '""':
        return []

    sql, params = self._build_search_query(fts_query, query.memory_type, branch)  # ← add branch param
    hits = self._fetch_hits(sql, tuple(params), project, repo, branch)
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[: query.limit]
```

#### 1.3 `VectorRetriever.knn_search()` — add branch parameter and WHERE clause

**File**: `scripts/agent/memory/retriever.py:214-250`

```python
class VectorRetriever:
    """KNN search on memories_vec using sqlite-vec extension."""

    def knn_search(
        self,
        embedding: list[float],
        memory_type: str | None,
        limit: int,
        branch: str = "",  # ← ADD this parameter
    ) -> list[MemoryHit]:
        """KNN search on memories_vec; raises OperationalError when table missing."""
        type_filter = ""
        params: list[object] = [_floats_to_blob(embedding), limit]
        if memory_type:
            type_filter = "AND m.memory_type = ?"
            params.insert(1, memory_type)

        branch_filter = ""
        if branch:
            branch_filter = "AND (? = '' OR m.branch = '' OR m.branch = ?)"
            params.insert(2, branch)  # placeholder for empty-branch check
            params.insert(4, branch)  # placeholder for branch match check

        sql = f"""
            SELECT m.memory_id, m.memory_type, m.source_type, m.session_id, m.turn_id,
                   m.project, m.repo, m.branch, m.content, m.summary, m.tags,
                   m.importance, m.pinned, m.created_at, m.updated_at,
                   mv.distance
            FROM memories_vec mv
            JOIN memories m ON m.memory_id = mv.memory_id
            WHERE mv.embedding MATCH ?
            {type_filter}
            {branch_filter}
            ORDER BY mv.distance
            LIMIT ?
        """  # nosec B608 — type_filter and branch_filter are literal strings; all values use ? placeholders

        with SQLiteHelper("session").open(row_factory=True) as db:
            rows = db.fetchall(sql, tuple(params))

        hits: list[MemoryHit] = []
        for row in rows:
            d = dict(row)
            distance = float(d.pop("distance", 999.0))
            entry = row_to_entry(d)
            # Negate distance: MemoryHit.score convention is higher-is-better
            hits.append(MemoryHit(entry=entry, score=-distance))
        return hits
```

#### 1.4 `HybridRetriever.search()` — pass branch to VectorRetriever.knn_search()

**File**: `scripts/agent/memory/retriever.py:275-307`

```python
def search(
    self,
    query: MemoryQuery,
    embedding: list[float] | None = None,
    project: str = "",
    repo: str = "",
    branch: str = "",
) -> list[MemoryHit]:
    """Run FTS5 search (and optionally KNN) and return ranked MemoryHit list.

    Falls back to FTS-only when embedding is None or vec table is unavailable.
    When embedding is supplied, merges FTS5 and KNN results via RRF.
    """
    fts_hits = self._fts.search(query, project, repo, branch)
    if embedding is None:
        logger.info("retrieval: fts_only (reason=embedding_disabled_or_none)")
        self.last_retrieval_mode = "fts_only"
        self.fts_fallback_count += 1
        return fts_hits

    vec_hits = self._vec.knn_search(
        embedding, query.memory_type, self._fts._fts_limit, branch  # ← ADD branch param
    )
    if not vec_hits:
        logger.info("retrieval: fts_only (reason=vec_returned_empty)")
        self.last_retrieval_mode = "fts_only"
        self.fts_fallback_count += 1
        return fts_hits

    self.last_retrieval_mode = "hybrid"
    merged = _rrf_merge([fts_hits, vec_hits], k=self._rrf_k)
    # hit.score is set to the RRF score by _rrf_merge; already sorted by _rrf_merge.
    return merged[: query.limit]
```

#### 1.5 `HybridRetriever.knn_search()` — add branch parameter

**File**: `scripts/agent/memory/retriever.py:309-316`

```python
def knn_search(
    self,
    embedding: list[float],
    memory_type: str | None,
    limit: int,
    branch: str = "",  # ← ADD this parameter
) -> list[MemoryHit]:
    """Delegate KNN search to VectorRetriever (used by ingestion dedup)."""
    return self._vec.knn_search(embedding, memory_type, limit, branch)  # ← pass branch through
```

### Phase 2: Injection service — pass branch from `on_user_prompt()`

#### 2.1 `MemoryInjectionService.on_user_prompt()` — add branch to retriever.search() calls

**File**: `scripts/agent/memory/injection.py:85-104`

```python
hits_s = self._retriever.search(
    MemoryQuery(
        query=query,
        memory_type=MemoryType.SEMANTIC,
        limit=self._policy.max_semantic,
    ),
    embedding=embedding,
    project=self._project,
    repo=self._repo,
    branch=self._branch,  # ← ADD this param
)
hits_e = self._retriever.search(
    MemoryQuery(
        query=query,
        memory_type=MemoryType.EPISODIC,
        limit=self._policy.max_episodic,
    ),
    embedding=embedding,
    project=self._project,
    repo=self._repo,
    branch=self._branch,  # ← ADD this param
)
```

### Phase 3: Factory — resolve branch context at build time

#### 3.1 `factory.py` — add branch resolution in `_build_memory_services()`

**File**: `scripts/agent/factory.py`

Add import at top of file:
```python
from shared.git_helper import get_repo_info
```

Add branch resolution in `_build_memory_services()`:
```python
def _build_memory_services(
    embed_client: EmbeddingClient,
    ctx: AgentContext,
) -> MemoryServices:
    """Build and return the memory services (injection + ingestion)."""
    # Resolve branch context at build time
    git_result = get_repo_info()
    branch = ""
    if git_result.success and git_result.data:
        branch = git_result.data.get("branch", "")
        if branch == "HEAD (detached)":
            branch = ""  # detached HEAD → no branch filter

    retriever = HybridRetriever(
        fts_limit=ctx.cfg.memory.memory_fts_candidate_limit,
        rrf_k=ctx.cfg.memory.memory_rrf_k,
        recency_days=ctx.cfg.memory.memory_recency_days,
        embed_client=embed_client,
    )

    injection_service = _build_injection_service(
        embed_client=embed_client,
        retriever=retriever,
        ctx=ctx,
        policy_cls=InjectionPolicy,
        service_cls=MemoryInjectionService,
        branch=branch,  # ← ADD branch param
    )

    ingestion_service = _build_ingestion_service(
        store=store,
        jsonl=jsonl,
        retriever=retriever,
        embed_client=embed_client,
        ctx=ctx,
        dedup_cls=DedupPolicy,
        service_cls=MemoryIngestionService,
        branch=branch,  # ← ADD branch param (for future use in ingestion)
    )

    return MemoryServices(
        injection=injection_service,
        ingestion=ingestion_service,
    )
```

#### 3.2 `_build_injection_service()` — accept and forward branch parameter

**File**: `scripts/agent/factory.py:289-306`

```python
def _build_injection_service(
    embed_client: object,
    retriever: object,
    ctx: AgentContext,
    policy_cls: type,
    service_cls: type,
    branch: str = "",  # ← ADD this parameter
) -> object:
    """Build and return the memory injection service."""
    policy = policy_cls(
        max_semantic=ctx.cfg.memory.memory_max_inject_semantic,
        max_episodic=ctx.cfg.memory.memory_max_inject_episodic,
        min_importance=ctx.cfg.memory.memory_min_importance,
    )
    return service_cls(
        policy=policy,
        retriever=retriever,
        embed_client=embed_client,
        branch=branch,  # ← ADD this param
    )
```

#### 3.3 `_build_ingestion_service()` — accept and forward branch parameter

**File**: `scripts/agent/factory.py:309-327`

```python
def _build_ingestion_service(
    store: object,
    jsonl: object,
    retriever: object,
    embed_client: object,
    ctx: AgentContext,
    dedup_cls: type,
    service_cls: type,
    branch: str = "",  # ← ADD this parameter
) -> object:
    """Build and return the memory ingestion service."""
    dedup_policy = dedup_cls(threshold=ctx.cfg.memory.memory_dedup_threshold)
    return service_cls(
        store=store,
        jsonl=jsonl,
        retriever=retriever,
        embed_client=embed_client,
        dedup_policy=dedup_policy,
        max_content_chars=ctx.cfg.memory.memory_max_content_chars,
        branch=branch,  # ← ADD this param
    )
```

### Phase 4: Tests — cross-branch isolation tests

#### 4.1 Add `TestBranchIsolation` test class to `tests/test_memory_retriever.py`

**File**: `tests/test_memory_retriever.py`

Append after existing `TestBranchBoundary` class:

```python
class TestBranchIsolation:
    """Cross-branch isolation tests for FTS and KNN retrieval paths."""

    def test_fts_search_excludes_other_branch_memory(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """FTS search with branch=feat/a excludes entries from branch=feat/b."""
        _insert(
            db_conn,
            memory_id="feat-b-id",
            memory_type="semantic",
            branch="feat/b",
            importance=0.9,
            content="feat-b specific rule",
        )
        q = MemoryQuery(query="feat-b specific", memory_type="semantic")
        hits = retriever.search(q, branch="feat/a")
        assert not any(e.memory_id == "feat-b-id" for e in hits)

    def test_fts_search_includes_global_memory(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """FTS search with branch=feat/a includes entries with branch='' (global)."""
        _insert(
            db_conn,
            memory_id="global-id",
            memory_type="semantic",
            branch="",
            importance=0.9,
            content="global rule content",
        )
        q = MemoryQuery(query="global rule", memory_type="semantic")
        hits = retriever.search(q, branch="feat/a")
        assert any(e.memory_id == "global-id" for e in hits)

    def test_fts_search_includes_same_branch(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """FTS search with branch=feat/a includes entries from branch=feat/a."""
        _insert(
            db_conn,
            memory_id="feat-a-id",
            memory_type="semantic",
            branch="feat/a",
            importance=0.9,
            content="feat-a specific rule",
        )
        q = MemoryQuery(query="feat-a specific", memory_type="semantic")
        hits = retriever.search(q, branch="feat/a")
        assert any(e.memory_id == "feat-a-id" for e in hits)

    def test_knn_search_excludes_other_branch_memory(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """KNN search with branch=feat/a excludes entries from branch=feat/b."""
        _insert(
            db_conn,
            memory_id="feat-b-id",
            memory_type="semantic",
            branch="feat/b",
            importance=0.9,
            content="feat-b vector content",
        )
        hits = retriever.knn_search([0.1] * 768, "semantic", 10, branch="feat/a")
        assert not any(e.memory_id == "feat-b-id" for e in hits)

    def test_knn_search_includes_global_memory(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """KNN search with branch=feat/a includes entries with branch='' (global)."""
        _insert(
            db_conn,
            memory_id="global-knn-id",
            memory_type="semantic",
            branch="",
            importance=0.9,
            content="global vector content",
        )
        hits = retriever.knn_search([0.1] * 768, "semantic", 10, branch="feat/a")
        assert any(e.memory_id == "global-knn-id" for e in hits)

    def test_hybrid_search_branch_isolation(
        self, retriever: MemoryRetriever, db_conn: sqlite3.Connection
    ) -> None:
        """End-to-end hybrid search with branch filter excludes other-branch entries."""
        _insert(
            db_conn,
            memory_id="feat-b-hybrid",
            memory_type="semantic",
            branch="feat/b",
            importance=0.9,
            content="hybrid feat-b content",
        )
        _insert(
            db_conn,
            memory_id="feat-a-hybrid",
            memory_type="semantic",
            branch="feat/a",
            importance=0.9,
            content="hybrid feat-a content",
        )
        # Hybrid search with branch=feat/a should include feat-a but not feat-b
        q = MemoryQuery(query="hybrid", memory_type="semantic")
        hits = retriever.search(q, embedding=[0.1] * 768, branch="feat/a")
        assert any(e.memory_id == "feat-a-hybrid" for e in hits)
        assert not any(e.memory_id == "feat-b-hybrid" for e in hits)
```

### Phase 5: Documentation — update `docs/05_agent_12_memory.md`

#### 5.1 Add/update "Branch Awareness" section

Document the following points:
- Branch is resolved at startup via `shared.git_helper.get_repo_info()` in `factory.py`
- Retrieval hard-filters to `branch='' OR branch=<current>` (not just scoring)
- Injection passes branch through all retriever paths
- Degraded behavior when git unavailable: defaults to empty branch (no filter, global scope)

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `retriever.py` FTS branch filter | Unit test with in-memory SQLite | `uv run pytest tests/test_memory_retriever.py::TestBranchIsolation::test_fts_search_excludes_other_branch_memory -v` | Other-branch entries absent; global entries present |
| `retriever.py` KNN branch filter | Unit test with mock embedding | `uv run pytest tests/test_memory_retriever.py::TestBranchIsolation::test_knn_search_excludes_other_branch_memory -v` | Same isolation behavior for vector path |
| `retriever.py` Hybrid branch filter | End-to-end test through HybridRetriever | `uv run pytest tests/test_memory_retriever.py::TestBranchIsolation::test_hybrid_search_branch_isolation -v` | Hybrid search respects branch filter |
| `injection.py` branch forwarding | Unit test / existing test suite | `uv run pytest tests/test_error_injection_service.py tests/test_memory_layer.py -v` | No regression; branch arg flows through |
| `factory.py` branch resolution | Manual inspection of build flow | Verify `_build_memory_services()` calls `get_repo_info()` | Branch resolved from git at startup |
| Type correctness | mypy type check | `uv run mypy scripts/agent/memory/retriever.py scripts/agent/memory/injection.py scripts/agent/factory.py` | No new type errors |
| Import layer contract | lint-imports | `uv run lint-imports` | No violations (shared.git_helper is already used in agent layer via context_view.py) |
| Regression suite | Full memory test suite | `uv run pytest tests/ -k "memory" -v` | All existing tests pass |

## Risks & Mitigations

- **Risk**: Adding a hard SQL branch filter could exclude valid semantic memories that were stored without a branch (empty branch) when the branch filter was not yet active → **Mitigation**: Filter is always `AND (? = '' OR m.branch = '' OR m.branch = ?)` — empty-branch entries are always included as global memories, so no data is lost.

- **Risk**: `get_repo_info()` fails or returns detached HEAD at agent startup → **Mitigation**: Default branch to `""` on any failure, disabling the filter (safe, no regression). Detached HEAD ("HEAD (detached)") explicitly resolved to `""`.

- **Risk**: KNN dedup in ingestion now filters by branch, preventing detection of semantic duplicates across branches → **Mitigation**: Dedup KNN call explicitly passes `branch=""` (global scope); retrieval KNN call passes current branch. Separate code paths.

- **Risk**: `VectorRetriever.knn_search()` SQL change could break existing callers that do not pass branch → **Mitigation**: Default `branch=""` preserves existing behavior for all current callers.

- **Risk**: `on_user_prompt()` branch fix changes retrieval results, causing existing tests to fail → **Mitigation**: Existing tests pass `branch=""` (default), which disables filtering, so no existing test is affected by the fix.

## Files Changed

- `scripts/agent/memory/retriever.py` — add branch WHERE clause to `_build_search_query()` and `knn_search()`; forward branch in `HybridRetriever.search()` and `knn_search()`
- `scripts/agent/memory/injection.py` — pass `branch=self._branch` to retriever.search() calls in `on_user_prompt()`
- `scripts/agent/factory.py` — add `get_repo_info()` call; pass branch to injection/ingestion builders
- `tests/test_memory_retriever.py` — add `TestBranchIsolation` test class with 6 tests
- `docs/05_agent_12_memory.md` — document branch-awareness contract
