## Goal

Add three new tests for `_rrf_merge` function in `tests/test_memory_retriever.py` to cover edge cases not currently tested: three-way duplicate chunk_id across 3 lists, same-score non-symmetric placement, and duplicate chunk_id with identical scores across lists.

## Scope

**In-Scope**:
- Add test for three-way duplicate chunk_id across 3 lists (score = 1/(k+0) + 1/(k+0) + 1/(k+0))
- Add test for same RRF score but different entries with non-symmetric placement
- Add test for duplicate chunk_id with identical scores across lists

**Out-of-Scope**:
- Modifying the `_rrf_merge` implementation
- Adding tests for other functions or modules
- Any changes outside `tests/test_memory_retriever.py`

## Assumptions

1. `_rrf_merge` uses `memory_id` as the deduplication key (confirmed by code inspection)
2. When RRF scores are identical, the sort order is undefined (stable sort not guaranteed)
3. The existing test `test_duplicate_memory_id_within_single_list` covers basic deduplication but needs additional boundary cases

## Implementation

### Target file

`tests/test_memory_retriever.py`

### Procedure

1. Read existing `_rrf_merge` tests to understand the test pattern and helper functions
2. Add three new test methods to the `TestRrfMerge` class
3. Validate by running `pytest tests/test_memory_retriever.py::TestRrfMerge -v`

### Method

Add test methods directly to the existing `TestRrfMerge` class, using the `_make_hit` helper function already defined in the file.

### Details

#### Test 1: Three-way duplicate chunk_id across 3 lists

```python
def test_three_way_duplicate_across_lists(self) -> None:
    """Three-way duplicate chunk_id across 3 lists accumulates all scores."""
    list1 = [_make_hit("dup"), _make_hit("only1")]
    list2 = [_make_hit("dup"), _make_hit("only2")]
    list3 = [_make_hit("dup"), _make_hit("only3")]
    merged = _rrf_merge([list1, list2, list3])
    ids = [h.entry.memory_id for h in merged]
    assert ids.count("dup") == 1
    dup_score = next(h.score for h in merged if h.entry.memory_id == "dup")
    # Score: 1/(60+0) + 1/(60+0) + 1/(60+0) = 3/60
    assert dup_score == pytest.approx(3.0 / 60)
```

#### Test 2: Same RRF score but different entries (non-symmetric placement)

```python
def test_same_rrf_score_non_symmetric_placement(self) -> None:
    """Non-symmetric placement yields identical RRF scores for both entries."""
    # Entry A at rank 0 in list1 + rank 60 in list2 = 1/60 + 1/120
    # Entry B at rank 1 in list1 + rank 59 in list2 = 1/61 + 1/119
    list1 = [_make_hit("a"), _make_hit("b")]
    list2 = [_make_hit("b"), _make_hit("a")]
    merged = _rrf_merge([list1, list2])
    ids = [h.entry.memory_id for h in merged]
    assert "a" in ids and "b" in ids
    score_a = next(h.score for h in merged if h.entry.memory_id == "a")
    score_b = next(h.score for h in merged if h.entry.memory_id == "b")
    # Both have same score (1/60 + 1/120) due to symmetric placement
    assert score_a == pytest.approx(score_b)
```

#### Test 3: Duplicate chunk_id with identical scores across lists

```python
def test_duplicate_chunk_id_identical_scores_across_lists(self) -> None:
    """Duplicate chunk_id with identical scores across lists preserves accumulated score."""
    # Entry "dup" appears at rank 0 in list1 and rank 0 in list2
    # Entry "other" appears at rank 0 in list1 and rank 0 in list2 (same position)
    list1 = [_make_hit("dup"), _make_hit("other")]
    list2 = [_make_hit("dup"), _make_hit("other")]
    merged = _rrf_merge([list1, list2])
    ids = [h.entry.memory_id for h in merged]
    assert ids.count("dup") == 1
    assert ids.count("other") == 1
    dup_score = next(h.score for h in merged if h.entry.memory_id == "dup")
    other_score = next(h.score for h in merged if h.entry.memory_id == "other")
    # Both have same accumulated score: 1/(60+0) + 1/(60+0) = 2/60
    assert dup_score == pytest.approx(2.0 / 60)
    assert other_score == pytest.approx(2.0 / 60)
    # Both should have identical scores (non-deterministic order)
    assert dup_score == pytest.approx(other_score)
```

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_memory_retriever.py` | Unit test execution | `pytest tests/test_memory_retriever.py::TestRrfMerge -v` | All tests pass, 3 new tests added |
