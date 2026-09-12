# Implementation Procedure: Narrow check_docs_content_policy.py's "full file tree" check (regression test)

## Goal

Add a regression test in `tests/tools/test_check_docs_content_policy.py` using a non-tree diagram (e.g. a state-transition diagram like the issue's example) to confirm it is no longer flagged, alongside a real file-tree fixture that must still be flagged.

## Scope

- **In-Scope**: Add a regression test in `tests/tools/test_check_docs_content_policy.py` confirming non-tree box-drawing diagrams are no longer falsely flagged.
- **Out-of-Scope**: Modifying the tool logic itself — handled in the companion implementation procedure for `tools/check_docs_content_policy.py`. Editing any `docs/*.md` file.

## Assumptions

- The heading-based heuristic implemented in the companion procedure will correctly distinguish real file trees from non-tree diagrams.
- The existing test `test_full_file_tree_detected()` uses a real file-tree fixture and should continue to pass after the tool logic change.

## Design decisions

- Add a new test function specifically for the non-tree diagram case (state-transition diagram).
- Keep the existing `test_full_file_tree_detected()` test unchanged — it validates true-positive detection.
- Use the exact state-transition diagram from the issue as the false-positive fixture.

## Alternatives considered

- Combine both assertions (true positive + false negative) into a single test function. Separate functions provide clearer failure diagnostics if one fails.
- Use a different non-tree diagram (sequence diagram, wiring diagram). The state-transition diagram is the most directly relevant since it was the original false positive.

## Implementation

### Target file

`tests/tools/test_check_docs_content_policy.py`

### Procedure

Add a new regression test function that verifies non-tree box-drawing diagrams are no longer falsely flagged by `check_full_file_tree()`.

### Method

1. Locate the existing `test_full_file_tree_detected()` function in `tests/tools/test_check_docs_content_policy.py`.
2. Add a new test function `test_non_tree_diagram_not_flagged()` that:
   - Creates a DocFile with the state-transition diagram from the issue.
   - Calls `check_full_file_tree([doc])`.
   - Asserts zero issues are returned.
3. Ensure the existing `test_full_file_tree_detected()` test continues to pass (validates true-positive detection).

### Details

**Current test (line 26):**
```python
def test_full_file_tree_detected() -> None:
    doc = _doc("## File Structure\n├─ rag-src/\n│   └─ chunk/\n└─ sqlite-vec/\n")
    issues = check_full_file_tree([doc])
    assert len(issues) >= 1
    assert all(i.severity == "WARNING" for i in issues)
    assert all("full file tree" in i.message for i in issues)
```

**New test to add:**
```python
def test_non_tree_diagram_not_flagged() -> None:
    """State-transition diagram should NOT be flagged as a full file tree."""
    doc = _doc(
        "## McpServerHealthRegistry State Transitions\n"
        "\n"
        "HEALTHY ──(failure × threshold)──→ UNAVAILABLE\n"
        "   ↑                                    │\n"
        "   │                            (cooldown 30s elapsed)\n"
        "   │                                    ↓\n"
        "   └──(record_success)────────── HALF_OPEN (trial probe)\n"
        "                                         │\n"
        "                               (failure)─┘ → UNAVAILABLE (cooldown reset)\n"
    )
    issues = check_full_file_tree([doc])
    assert issues == []
```

**Verification steps:**
1. Run `uv run pytest tests/tools/test_check_docs_content_policy.py::test_non_tree_diagram_not_flagged -v` to verify the new test passes.
2. Run `uv run pytest tests/tools/test_check_docs_content_policy.py::test_full_file_tree_detected -v` to verify the existing test still passes.
3. Run the full suite: `uv run pytest tests/tools/test_check_docs_content_policy.py -v`.

## Compatibility considerations

- The new test must pass only after the tool logic change (heading-based heuristic) is applied. Before the change, this test would fail because the state-transition diagram IS currently flagged.
- The existing `test_full_file_tree_detected()` test must continue to pass — it validates true-positive detection.

## Security considerations

N/A: test-only addition; no security impact.

## Rollback considerations

- Remove the new test function if the tool logic change introduces regressions elsewhere.
- Verify against the full test suite before considering the rollback complete.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/tools/test_check_docs_content_policy.py | New regression test | `uv run pytest tests/tools/test_check_docs_content_policy.py::test_non_tree_diagram_not_flagged -v` | Test passes |
| tests/tools/test_check_docs_content_policy.py | Existing test preserved | `uv run pytest tests/tools/test_check_docs_content_policy.py::test_full_file_tree_detected -v` | Test passes |
| tests/tools/test_check_docs_content_policy.py | Full test suite | `uv run pytest tests/tools/test_check_docs_content_policy.py -v` | All tests pass |

## Completion criteria

- A new regression test in `tests/tools/test_check_docs_content_policy.py` covers a non-tree box-drawing diagram (REQ-002)
- All existing tests in `tests/tools/test_check_docs_content_policy.py` continue to pass (REQ-006)

## Out of scope

- Modifying the tool logic itself — handled in the companion implementation procedure for `tools/check_docs_content_policy.py`.
- Adding additional regression tests for other non-tree ASCII art types (sequence diagrams, wiring diagrams).
- Editing any `docs/*.md` file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-074000 | 20260913-074100 | Added regression test for non-tree diagram case |
| 2 | Add or update tests per Validation plan | Completed | — | — | This procedure IS the test addition; 10 tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-074100 | 20260913-074200 | All 10 tests pass (new + existing) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs changes required |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20260909-200213_dcp008_transport_health_full_file_tree_false_positive.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-070336_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-071927
- **Related target files**: tests/tools/test_check_docs_content_policy.py
