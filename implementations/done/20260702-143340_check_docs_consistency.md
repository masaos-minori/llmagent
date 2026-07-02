# Implementation Procedure: Add Duplicate Heading Number Detection to `check_docs_consistency.py`

## Goal

Add a new check function `check_duplicate_heading_numbers` to `scripts/checks/check_docs_consistency.py` that detects when two or more headings in the same Markdown file share the same section number prefix (e.g. `## 3.` appearing twice). This prevents the structural defect found in `docs/03_rag_04_data_model_and_interfaces.md` from being silently introduced again in any RAG doc.

## Scope

**In scope:**
- Add one new function `check_duplicate_heading_numbers(content: str, filename: str) -> list[str]` to the checker.
- Register the new function in `check_all()` so it runs as part of every checker invocation.
- Update the module docstring to list the new check.
- Validate the new check against all existing `docs/03_rag_*.md` files to confirm no false positives.

**Out of scope:**
- Changes to any other checker functions (existing logic must not be modified).
- Changes to CI workflow files (the workflow already invokes the checker; no path changes needed).
- Changes to `docs/` files (covered in a separate implementation document).
- Adding unit tests in `tests/` unless a `tests/test_check_docs_consistency.py` already exists (check before deciding; if it exists, add a test case).

## Assumptions

1. The checker is invoked as `python scripts/checks/check_docs_consistency.py [files...]`. The function signature `(content: str, filename: str) -> list[str]` is the established convention; the new function must follow it.
2. Duplicate detection applies only to the numeric prefix of headings (e.g. `## 3.` in `## 3. Data Transfer Objects`). Headings without a numeric prefix are ignored.
3. The check applies to all heading levels (`##`, `###`, `####`, etc.) independently — a `## 3.` and a `### 3.` at the same level prefix are only considered duplicates if they share the same level and the same number string.
4. Fenced code block content must be skipped (headings inside ` ``` ` blocks are not real headings).
5. After adding the check, `python scripts/checks/check_docs_consistency.py` must exit 0 on all current `docs/03_rag_*.md` files except `03_rag_04_data_model_and_interfaces.md` (which will be fixed separately). The two implementation steps may be applied in either order but both must be complete before CI passes.

## Implementation

### Target file

`scripts/checks/check_docs_consistency.py`

### Procedure

**Step 1: Update the module docstring**

Locate the docstring at the top of the module (lines 2-17). Add one line to the bulleted list:

```
- Duplicate heading numbers (same level and number prefix appearing more than once)
```

**Step 2: Add the new check function**

Insert `check_duplicate_heading_numbers` after the last existing check function (`check_stale_issue_routing`, which ends around line 352) and before `check_all`.

**Step 3: Register the new function in `check_all`**

In `check_all()`, add one line after the existing `check_stale_issue_routing` call:

```python
issues.extend(check_duplicate_heading_numbers(content, filename))
```

### Method

Use the `Edit` tool. Insert the new function and the `check_all` registration as two separate edits to keep each change minimal and reviewable.

### Details

**New function signature and logic:**

```python
def check_duplicate_heading_numbers(content: str, filename: str) -> list[str]:
    """Check for duplicate heading numbers at the same heading level.

    Detects headings like '## 3. Foo' and '## 3. Bar' in the same file.
    Only headings with a numeric prefix (e.g. '## 3.', '### 2.1') are checked.
    Headings inside fenced code blocks are skipped.
    """
    issues: list[str] = []
    lines = content.split("\n")
    in_fenced_block = False
    # seen: maps (heading_level, number_prefix) -> first line number seen
    seen: dict[tuple[int, str], int] = {}

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fenced_block = not in_fenced_block
            continue
        if in_fenced_block:
            continue
        # Match headings: one or more '#' followed by space and optional number prefix
        m = re.match(r"^(#{1,6})\s+(\d[\d.]*\.)\s+", stripped)
        if m:
            level = len(m.group(1))
            number = m.group(2)
            key = (level, number)
            if key in seen:
                issues.append(
                    f"{filename}:{i}: duplicate heading number — "
                    f"'{'#' * level} {number}' also at line {seen[key]}: '{stripped}'"
                )
            else:
                seen[key] = i
    return issues
```

**Key design decisions:**

- The regex `r"^(#{1,6})\s+(\d[\d.]*\.)\s+"` matches headings whose title starts with a number followed by a dot (e.g. `## 3.`, `### 3.1.`, `#### 2.1.1.`). Headings without a number prefix (e.g. `## Introduction`) are ignored to avoid false positives.
- Detection is scoped per `(level, number)` pair: a `## 3.` and a `### 3.` are different keys and are not considered duplicates.
- The function reports only the second (and later) occurrence of a duplicate, pointing back to the first occurrence's line number.
- No `--fix` auto-correction is implemented for this check — renumbering requires human judgment about the correct target number.

**Registration in `check_all`:**

The call is added after `check_stale_issue_routing` and before `check_deleted_rag_refs`:

```python
def check_all(content: str, filename: str) -> list[str]:
    issues = []
    issues.extend(check_broken_headings(content, filename))
    issues.extend(check_malformed_tables(content, filename))
    issues.extend(check_unclosed_inline_code(content, filename))
    issues.extend(check_json_not_wrapped(content, filename))
    issues.extend(check_stale_patterns(content, filename))
    issues.extend(check_resolved_in_active(content, filename))
    issues.extend(check_stale_issue_routing(content, filename))
    issues.extend(check_duplicate_heading_numbers(content, filename))  # ← new
    issues.extend(check_deleted_rag_refs(content, filename))
    issues.extend(check_migration_notes_in_active(content, filename))
    return issues
```

**Unit tests (conditional):**

Check whether `tests/test_check_docs_consistency.py` exists:
```bash
ls tests/test_check_docs_consistency.py 2>/dev/null
```

If the file exists, add test cases covering:
1. A file with no duplicate heading numbers → `[]`
2. A file with one duplicate `## 3.` → one issue reported
3. A file with headings inside a fenced code block (must not be flagged)
4. A file with `## 3.` and `### 3.` (different levels, must not be flagged)

## Validation Plan

| Check | Command | Expected outcome |
|---|---|---|
| New check detects the known duplicate | `python scripts/checks/check_docs_consistency.py docs/03_rag_04_data_model_and_interfaces.md` (before doc fix) | Exits 1, reports duplicate `## 3.` |
| No false positives on other RAG docs | `python scripts/checks/check_docs_consistency.py docs/03_rag_00_document-guide.md docs/03_rag_01_system_overview.md docs/03_rag_02_ingestion_pipeline.md docs/03_rag_03_query_pipeline.md docs/03_rag_05_configuration_and_operations.md docs/03_rag_90_inconsistencies_and_known_issues.md` | Exit 0, 0 issues |
| Full checker after both fixes applied | `python scripts/checks/check_docs_consistency.py` | Exit 0, 0 issues |
| Existing unit tests still pass | `uv run pytest tests/ -q -k "docs_consistency"` | All pass (or no tests found — acceptable) |
| Checker syntax is valid | `python -m py_compile scripts/checks/check_docs_consistency.py` | Exit 0, no output |
