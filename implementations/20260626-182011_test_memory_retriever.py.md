# Implementation: test_memory_retriever.py — branch-aware scoring test

Source plan: `plans/20260626-180404_plan.md` — Phase 2

---

## Goal

Add a test that verifies branch-specific `MemoryEntry` records score higher than global (empty-branch) records when retrieval is performed with a matching branch parameter.

---

## Scope

**In-Scope**
- Test: insert two memory entries — one with `branch="feature-x"`, one with `branch=""` (global) — search with `branch="feature-x"` → assert feature-x entry scores higher
- Test: `on_user_prompt` with `branch` set → confirmed by injection test (can be minimal here)

**Out-of-Scope**
- Testing strict branch exclusion (which is not implemented — boost only)
- Performance benchmarks

---

## Assumptions

1. Existing tests in `test_memory_retriever.py` use a SQLite fixture with `memories` and `memories_fts` tables.
2. `FtsRetriever.search()` calls `_context_boost(entry, project, repo, branch)`.
3. `_CONTEXT_MATCH_BOOST + 0.05 = 0.15` for branch match vs `0.0` for no match — measurable score difference.

---

## Implementation

### Target file
`tests/test_memory_retriever.py`

### Procedure
Read existing test fixture in `test_memory_retriever.py`, then add `test_branch_boost_increases_score`.

### Method

```python
def test_branch_boost_increases_score(memory_db):
    """Branch-matching entry must score higher than global (empty-branch) entry."""
    # Insert two entries with same content but different branch
    branch_entry = make_memory_entry(
        memory_id="m1",
        content="fix login timeout",
        branch="feature-login-fix",
        importance=0.5,
    )
    global_entry = make_memory_entry(
        memory_id="m2",
        content="fix login timeout",
        branch="",
        importance=0.5,
    )
    insert_memory(memory_db, branch_entry)
    insert_memory(memory_db, global_entry)

    retriever = FtsRetriever()
    hits = retriever.search(
        MemoryQuery(query="login timeout", limit=10),
        project="",
        repo="",
        branch="feature-login-fix",
    )
    assert len(hits) == 2
    hit_by_id = {h.entry.memory_id: h for h in hits}
    assert hit_by_id["m1"].score > hit_by_id["m2"].score, (
        "branch-matching entry should score higher than global entry"
    )
```

---

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check tests/test_memory_retriever.py` | 0 errors |
| Tests | `uv run pytest tests/test_memory_retriever.py::test_branch_boost_increases_score -v` | pass |
| Full suite | `uv run pytest -v` | all pass |
