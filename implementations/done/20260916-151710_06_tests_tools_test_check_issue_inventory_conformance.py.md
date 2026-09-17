## Goal

Add `tests/tools/test_check_issue_inventory_conformance.py` with fixture-backed unit tests covering each of the five violation classes in REQ-001, using real current-document examples identified during this Plan's Step 2/3 verification as authentic fixture material.

## Scope

- Create a new test file at `tests/tools/test_check_issue_inventory_conformance.py`.
- Implement one fixture per violation class: vocabulary, template field-count, orphaned bullets, closing-summary consistency, referential integrity.
- Model on `tests/tools/test_check_needs_confirmation_inventory.py` (confirmed to exist via `find tests/tools`).

## Assumptions

- The five violation classes are defined in REQ-001:
  - Vocabulary: Status/Type/Severity/Area/Owner values outside defined sets
  - Template field-count: fewer than 16 fields (Part 1) or 15 fields (Part 2) per entry
  - Orphaned bullets: `- **Field**:` bullets appearing after removal placeholders
  - Closing-summary consistency: Part 1 closing ID list mismatch vs. actual headings
  - Referential integrity: dangling Related/Related NC/Target IDs
- Real current-document examples were identified during this Plan's Step 2/3 verification and can be used as fixture material.

## Design decisions

- Use pytest fixtures to provide test data for each violation class.
- Each fixture should contain a minimal example that triggers exactly one violation class.
- Use `subprocess.run()` or direct Python imports to invoke the checker and capture its output.
- Verify both positive cases (violations detected) and negative cases (no violations).

## Alternatives considered

- Using mock objects instead of real document examples — rejected because the Plan's intent is to use authentic fixture material from the current document.

## Implementation
### Target file

`tests/tools/test_check_issue_inventory_conformance.py`

### Procedure

1. Create the new test file under `tests/tools/`.
2. Import the checker module and pytest fixtures.
3. Define fixtures for each violation class, using real current-document examples as test data.
4. Implement test functions that verify the checker correctly detects each violation class.
5. Include negative test cases (no violations) alongside positive ones.

### Method

Current state: No existing test file implements this checker. A modeled analogue exists:
- `tests/tools/test_check_needs_confirmation_inventory.py` — fixture pattern model

Required structure:
```python
#!/usr/bin/env python3
"""tests/tools/test_check_issue_inventory_conformance.py

Fixture-backed unit tests for tools/check_issue_inventory_conformance.py.

Each fixture contains a minimal example that triggers exactly one violation class.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

# Fixtures for each violation class — using real current-document examples as test data

@pytest.fixture
def vocabulary_violation_doc(tmp_path: Path) -> Path:
    """Document with invalid Status value."""
    doc = tmp_path / "test.md"
    doc.write_text("""
#### RAG-XXX: Test vocabulary violation

- **Status**: resolved
- **Type**: document-code-mismatch
- **Severity**: high
- **Area**: rag
- **Owner**: @data-eng
...
""")
    return doc

@pytest.fixture
def template_field_count_violation_doc(tmp_path: Path) -> Path:
    """Document with fewer than 16 fields (Part 1 full entry)."""
    doc = tmp_path / "test.md"
    doc.write_text("""
#### RAG-XXX: Test template violation

- **Status**: open
- **Type**: document-code-mismatch
- **Severity**: high
- **Area**: rag
- **Owner**: @data-eng
...
""")
    return doc

@pytest.fixture
def orphaned_bullet_doc(tmp_path: Path) -> Path:
    """Document with orphaned bullet after removal placeholder."""
    doc = tmp_path / "test.md"
    doc.write_text("""
RAG-XXX has been removed — do not create a #### RAG-XXX heading.

- **Status**: open
- **Type**: document-code-mismatch
- **Severity**: high
- **Area**: rag
- **Owner**: @data-eng
""")
    return doc

@pytest.fixture
def closing_summary_mismatch_doc(tmp_path: Path) -> Path:
    """Document with closing summary ID list mismatch."""
    doc = tmp_path / "test.md"
    doc.write_text("""
#### RAG-XXX: Test closing summary violation

- **Status**: open
- **Type**: document-code-mismatch
- **Severity**: high
- **Area**: rag
- **Owner**: @data-eng

---

Closing summary: RAG-XXX, RAG-YYY
""")
    return doc

@pytest.fixture
def dangling_reference_doc(tmp_path: Path) -> Path:
    """Document with dangling Related reference."""
    doc = tmp_path / "test.md"
    doc.write_text("""
#### RAG-XXX: Test dangling reference

- **Status**: open
- **Type**: document-code-mismatch
- **Severity**: high
- **Area**: rag
- **Owner**: @data-eng
- **Related**: NC-999
""")
    return doc

# Test functions

def test_vocabulary_violation(vocabulary_violation_doc: Path) -> None:
    result = subprocess.run(
        ["python", str(vocabulary_violation_doc)],
        capture_output=True, text=True, check=False
    )
    assert result.returncode != 0, "Vocabulary violation should be detected"
    assert "resolved" in result.stderr.lower(), "Invalid Status value should be reported"

def test_template_field_count_violation(template_field_count_violation_doc: Path) -> None:
    result = subprocess.run(
        ["python", str(template_field_count_violation_doc)],
        capture_output=True, text=True, check=False
    )
    assert result.returncode != 0, "Template field-count violation should be detected"

def test_orphaned_bullet(orphaned_bullet_doc: Path) -> None:
    result = subprocess.run(
        ["python", str(orphaned_bullet_doc)],
        capture_output=True, text=True, check=False
    )
    assert result.returncode != 0, "Orphaned bullet should be detected"

def test_closing_summary_mismatch(closing_summary_mismatch_doc: Path) -> None:
    result = subprocess.run(
        ["python", str(closing_summary_mismatch_doc)],
        capture_output=True, text=True, check=False
    )
    assert result.returncode != 0, "Closing summary mismatch should be detected"

def test_dangling_reference(dangling_reference_doc: Path) -> None:
    result = subprocess.run(
        ["python", str(dangling_reference_doc)],
        capture_output=True, text=True, check=False
    )
    assert result.returncode != 0, "Dangling reference should be detected"
    assert "NC-999" in result.stderr, "Dangling NC-999 should be reported"

def test_no_violations(tmp_path: Path) -> None:
    """Negative test: valid document should pass all checks."""
    doc = tmp_path / "test.md"
    doc.write_text("""
#### RAG-XXX: Valid entry

- **Status**: open
- **Type**: document-code-mismatch
- **Severity**: high
- **Area**: rag
- **Owner**: @data-eng
- **Related**: NC-036
""")
    result = subprocess.run(
        ["python", str(doc)],
        capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, "Valid document should pass all checks"
```

The exact fixture content may vary slightly depending on the current document structure — verify against the live document at implementation time.

### Details

Each fixture should contain a minimal example that triggers exactly one violation class. The test functions should verify both positive cases (violations detected) and negative cases (no violations). The fixture names should match the violation class they represent.

## Compatibility considerations

- This is a new test file — no backward compatibility concerns.
- The test file reuses the same testing conventions as other tool tests in the repository.

## Security considerations

- No security impact — the test file reads local Markdown files and verifies checker output; it does not modify any files.

## Rollback considerations

- If the test file is found to produce false positives, the test logic can be adjusted without removing the entire test file.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_issue_inventory_conformance.py` | Unit (fixture-backed) | `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -v` | All fixtures pass, each violation class correctly flagged, placeholders not falsely flagged |

## Completion criteria

- The test file includes one fixture per violation class.
- Each test function verifies the checker correctly detects its corresponding violation class.
- A negative test case verifies no violations when given a valid document.
- `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -v` passes clean.

## Out of scope

- Modifying any other test files.
- Adding additional test cases beyond the five violation classes.
- Changing the format of existing test files.

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260915-200449_gov03_add-conformance-and-referential-integrity-checks-for-the-issue-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-151710_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-151710
- **Related target files**: tests/tools/test_check_issue_inventory_conformance.py
