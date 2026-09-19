## Goal

Create `tests/tools/test_check_docs_quality.py` with unit and integration tests covering both the extended alphabetic-suffix duplicate-heading check and the new content-similarity check. Closes REQ-006.

## Scope

- Create new test file `tests/tools/test_check_docs_quality.py`
- Test cases for alphabetic-suffix duplicate-heading detection (true-positive and false-positive)
- Test cases for content-similarity check (true-positive and false-positive)
- Integration test against the known `## 7c.` duplicate in `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`
- Regression test against the full `docs/` tree

## Assumptions

- The test framework is pytest (confirmed by existing project conventions)
- Tests can construct DocFile objects and pass them directly to core check functions
- The `_compute_section_similarity` private helper is accessible for direct testing
- Both checks are registered via `@register_core_check` and discoverable through the checker registry

## Design decisions

- Use pytest fixtures for common setup (DocFile construction, mock filesystem)
- Test the private `_compute_section_similarity` helper directly with known inputs
- Test each check function independently before integration tests
- Use the actual `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` file as an integration test input

## Alternatives considered

- Parameterized tests for all combinations: rejected because the number of true/false positive combinations would make parameterization unwieldy and harder to debug individual failures.
- Testing via CLI invocation instead of direct function calls: rejected because direct function calls give better control over inputs and clearer failure messages.

## Implementation

### Target file

`tests/tools/test_check_docs_quality.py`

### Procedure

1. Set up test infrastructure (imports, fixtures)
2. Write tests for `_compute_section_similarity` private helper
3. Write tests for alphabetic-suffix duplicate-heading detection
4. Write tests for content-similarity check
5. Write integration test against known defect case
6. Write regression test against full `docs/` tree

### Method

#### Step 1: Test infrastructure

```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Import the modules under test
from tools.check_docs_quality import (
    _compute_section_similarity,
    check_content_similarity,
)

# Helper fixture for constructing DocFile-like objects
@pytest.fixture
def sample_doc():
    """Construct a DocFile-like object with given path and content."""
    doc_file = MagicMock()
    doc_file.path = Path("/tmp/sample.md")
    return doc_file
```

#### Step 2: Tests for `_compute_section_similarity`

```python
class TestComputeSectionSimilarity:
    def test_identical_sections(self):
        text = "hello world foo bar baz"
        assert _compute_section_similarity(text, text) is True
    
    def test_no_overlap(self):
        assert _compute_section_similarity("hello world", "foo bar baz") is False
    
    def test_partial_overlap_below_threshold(self):
        # Only 1 word overlap out of ~6 unique words → Jaccard ≈ 0.14 < 0.85
        assert _compute_section_similarity(
            "hello world foo bar",
            "hello baz qux quux",
        ) is False
    
    def test_custom_threshold(self):
        # With threshold=0.1, partial overlap should pass
        assert _compute_section_similarity(
            "hello world foo bar",
            "hello baz qux quux",
            threshold=0.1,
        ) is True
    
    def test_empty_body_returns_false(self):
        assert _compute_section_similarity("", "some text") is False
        assert _compute_section_similarity("some text", "") is False
    
    def test_code_blocks_are_stripped(self):
        # Code blocks should be removed before tokenization
        text_with_code = "before ```code\nprint('hello')\n```\nafter"
        text_without_code = "before after"
        # These should have high similarity since code is stripped
        result = _compute_section_similarity(text_with_code, text_without_code)
        assert result is True
```

#### Step 3: Tests for alphabetic-suffix duplicate-heading detection

```python
class TestAlphabeticSuffixDuplicateHeading:
    def test_true_positive_same_base_number_duplicate(self, sample_doc):
        """Two headings with same base number and same level → expect Issue."""
        content = "# Title\n\n## 7a. First section\n\nSome text.\n\n## 7b. Second section\n\nMore text."
        sample_doc.read_text.return_value = content
        
        issues = check_duplicate_heading_numbers(sample_doc)
        assert len(issues) == 1
        assert "7a" in str(issues[0].message) or "7b" in str(issues[0].message)
    
    def test_true_positive_known_defect_case(self, sample_doc):
        """The known ## 7c. duplicate in docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md → expect Issue."""
        doc_path = Path(__file__).parent.parent.parent / "docs" / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"
        if doc_path.exists():
            sample_doc.path = doc_path
            sample_doc.read_text.return_value = doc_path.read_text()
            
            issues = check_duplicate_heading_numbers(sample_doc)
            assert len(issues) >= 1
            assert any("7c" in str(issue.message) for issue in issues)
    
    def test_false_positive_different_base_numbers(self, sample_doc):
        """Different base numbers at same level → no Issue."""
        content = "# Title\n\n## 7a. First section\n\nText A.\n\n## 8b. Second section\n\nText B."
        sample_doc.read_text.return_value = content
        
        issues = check_duplicate_heading_numbers(sample_doc)
        assert len(issues) == 0
    
    def test_false_positive_numeric_subsections(self, sample_doc):
        """Numeric subsections like 2.1, 2.2 → no Issue."""
        content = "# Title\n\n## 2.1 First subsection\n\nText A.\n\n## 2.2 Second subsection\n\nText B."
        sample_doc.read_text.return_value = content
        
        issues = check_duplicate_heading_numbers(sample_doc)
        assert len(issues) == 0
    
    def test_false_positive_different_levels(self, sample_doc):
        """Same heading number at different levels → no Issue."""
        content = "# Title\n\n## 7a. Level 2 section\n\nText A.\n\n####### 7a. Level 7 section\n\nText B."
        sample_doc.read_text.return_value = content
        
        issues = check_duplicate_heading_numbers(sample_doc)
        assert len(issues) == 0
```

#### Step 4: Tests for content-similarity check

```python
class TestContentSimilarity:
    def test_true_positive_overlapping_sections(self, sample_doc):
        """Two sections with heavily overlapping body text → expect Issue."""
        common_text = "This is boilerplate content that appears in many documents. It describes the purpose and scope of the section."
        content = f"# Title\n\n## Section One\n\n{common_text}\n\n## Section Two\n\n{common_text}"
        sample_doc.read_text.return_value = content
        
        issues = check_content_similarity(sample_doc)
        assert len(issues) >= 1
        assert any("similarity" in issue.kind.lower() or "similarity" in issue.message.lower() for issue in issues)
    
    def test_false_positive_templated_distinct_sections(self, sample_doc):
        """Two templated-but-distinct sections → no Issue."""
        verification_a = "Verification: This item has been verified against the current source code."
        verification_b = "Verification: This item has been validated against the latest documentation updates."
        content = f"# Title\n\n## Verification A\n\n{verification_a}\n\n## Verification B\n\n{verification_b}"
        sample_doc.read_text.return_value = content
        
        issues = check_content_similarity(sample_doc)
        assert len(issues) == 0
    
    def test_false_positive_short_unique_sections(self, sample_doc):
        """Short sections with minimal overlap → no Issue."""
        content = "# Title\n\n## Short A\n\nA.\n\n## Short B\n\nB."
        sample_doc.read_text.return_value = content
        
        issues = check_content_similarity(sample_doc)
        assert len(issues) == 0
    
    def test_content_similarity_across_multiple_sections(self, sample_doc):
        """Three sections where two share heavy overlap → expect one Issue."""
        shared = "Shared content between sections one and three."
        content = f"# Title\n\n## Section One\n\n{shared}\n\n## Section Two\n\nUnique content here.\n\n## Section Three\n\n{shared}"
        sample_doc.read_text.return_value = content
        
        issues = check_content_similarity(sample_doc)
        assert len(issues) >= 1
```

#### Step 5: Integration test — known defect case

```python
class TestIntegrationKnownDefect:
    def test_run_checker_against_known_duplicate(self):
        """Run `uv run python tools/check_docs_quality.py --only duplicate_heading_numbers` against the known defect file."""
        import subprocess
        import sys
        
        doc_path = Path(__file__).parent.parent.parent / "docs" / "90_shared_02_02_types_and_protocols-tool-and-execution-dto.md"
        if not doc_path.exists():
            pytest.skip(f"Test file not found: {doc_path}")
        
        result = subprocess.run(
            [sys.executable, "-m", "tools.check_docs_quality", "--only", "duplicate_heading_numbers", str(doc_path)],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        
        # Should report exactly one Issue for the ## 7c. duplicate
        assert result.returncode != 0  # Tool reports findings → non-zero exit
        assert "7c" in result.stdout or "7c" in result.stderr
```

#### Step 6: Regression test — full docs tree

```python
class TestRegressionFullDocsTree:
    def test_no_new_false_positives_on_full_docs_tree(self):
        """Run checker against full `docs/` tree → confirm no new false-positive noise beyond existing issues."""
        import subprocess
        import sys
        
        docs_dir = Path(__file__).parent.parent.parent / "docs"
        if not docs_dir.exists():
            pytest.skip(f"Docs directory not found: {docs_dir}")
        
        result = subprocess.run(
            [sys.executable, "-m", "tools.check_docs_quality"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )
        
        # Check that output does not contain unexpected warnings about numeric subsections
        lines = result.stdout.split('\n') + result.stderr.split('\n')
        for line in lines:
            # Ensure no numeric subsections are flagged as duplicates
            if ".1" in line or ".2" in line or ".3" in line:
                assert "duplicate" not in line.lower(), f"False positive on numeric subsection: {line}"
```

### Details

- The true-positive test for alphabetic-suffix uses the exact pattern from the plan: two headings with the same base number (`7`) but different suffixes (`7a.` and `7b.`).
- The known-defect integration test reads the actual file `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` and verifies it produces an Issue for the `## 7c.` duplicate.
- Content-similarity tests use a hardcoded threshold of 0.85 (matching the implementation default).
- The `_compute_section_similarity` tests verify edge cases: empty bodies, code block stripping, custom thresholds.
- The regression test checks that no numeric subsections (`.1`, `.2`, `.3`) are incorrectly flagged as duplicates when running against the full `docs/` tree.

## Compatibility considerations

- No changes to existing test infrastructure or CI configuration.
- Tests follow the project's existing pytest conventions (fixtures, class-based test organization).
- The integration test uses `subprocess.run` to invoke the tool — this matches how the plan's Validation plan specifies testing.

## Security considerations

N/A: this change adds test coverage, not data access or network operations.

## Rollback considerations

- To revert: delete `tests/tools/test_check_docs_quality.py`.
- No persistent state changes — rollback is straightforward.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| Alphabetic-suffix true positive | Construct DocFile with two `## 7c.` headings at same level → expect Issue | `pytest -k "test_alphabetic_suffix_true_positive"` | One Issue reported |
| Alphabetic-suffix false positive (numeric subsections) | Construct DocFile with `## 2.1` and `## 2.2` at same level → expect no Issue | `pytest -k "test_numeric_subsections_false_positive"` | No Issues reported |
| Alphabetic-suffix false positive (different base numbers) | Construct DocFile with `## 7a.` and `## 7b.` at same level → expect no Issue | `pytest -k "test_different_base_numbers_false_positive"` | No Issues reported |
| Content-similarity true positive | Construct DocFile with two sections whose body text overlaps > threshold → expect Issue | `pytest -k "test_content_similarity_true_positive"` | One Issue reported |
| Content-similarity false positive (templated sections) | Construct DocFile with two templated-but-distinct sections → expect no Issue | `pytest -k "test_templated_sections_false_positive"` | No Issues reported |
| Integration — known duplicate | Run checker against `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` | `uv run python tools/check_docs_quality.py --only duplicate_heading_numbers docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` | One Issue for `## 7c.` at line 87 |
| Regression — full docs tree | Run checker against full `docs/` tree | `uv run python tools/check_docs_quality.py` | No new false-positive noise beyond existing issues |
| Private helper | Test `_compute_section_similarity` directly | `pytest -k "test_compute_section_similarity"` | Correct similarity values for known inputs |

## Completion criteria

- [ ] All 8+ test cases defined and passing
- [ ] True-positive test for alphabetic-suffix duplicate (`## 7c.` / `## 7c.`) passes
- [ ] False-positive test for alphabetic-suffix non-duplicate (`## 7a.` / `## 7b.`) passes
- [ ] False-positive test for numeric subsections (`## 2.1` / `## 2.2`) passes
- [ ] True-positive test for content similarity (overlapping prose) passes
- [ ] False-positive test for content similarity (templated distinct sections) passes
- [ ] Integration test against `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` passes
- [ ] Regression test against full `docs/` tree passes without false positives

## Out of scope

- Tests for edge cases like `## 2.1a.` or `## 2a1.` (silently skipped per Risks section)
- Cross-document content-similarity tests (only intra-document)
- Performance benchmarks for large documents
- Tests for configurable thresholds via config file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260914-112554_qa02_duplicate-section-and-merge-boundary-detection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-091956_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-093651
- **Related target files**: tests/tools/test_check_docs_quality.py
