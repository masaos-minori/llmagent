## Goal

Extend `check_duplicate_heading_numbers` in `tools/check_docs_quality.py` to detect alphabetic-suffix duplicate headings (e.g., `## 7c.` appearing twice at the same level) and add a new `check_content_similarity` core check that flags sections within the same document whose body text overlaps above a threshold. Closes REQ-001, REQ-002, REQ-003, REQ-004, REQ-005.

## Scope

- Modify `check_duplicate_heading_numbers` regex to add alphabetic-suffix detection alongside the existing purely-numeric pattern
- Add private `_compute_section_similarity` helper function
- Add `check_content_similarity` core check function
- Register both checks with the existing `@register_core_check` mechanism
- All changes stay within `tools/check_docs_quality.py`

## Assumptions

- The alphabetic suffix follows `[a-z]+` (lowercase letters only), consistent with observed `## 7c.` pattern
- Content similarity uses token-level Jaccard similarity on word-token sets
- Section boundaries are determined by Markdown heading markers (`#` through `######`)
- The existing `@register_core_check` decorator is the correct registration point
- The `_compute_section_similarity` utility goes as a private helper in `check_docs_quality.py`, not in `_docs_consistency_lib.py`

## Design decisions

- Two mutually exclusive regex patterns instead of one: keep original `\d[\d.]*\.` for pure numeric, add `\d+[a-z]+\.` for alphabetic-suffix. No overlap between patterns.
- Extract base number (digits before alphabetic suffix, e.g., `2a` → base `2`), group by `(level, base_number)`, flag pairs where base numbers match but full heading numbers differ.
- Content-similarity threshold starts conservatively at 0.85, validated empirically against full `docs/` tree during implementation.
- Skip fenced code blocks and inline code when extracting section bodies for content-similarity.

## Alternatives considered

- Single unified regex capturing both patterns: rejected because it would require complex alternation logic and risk false positives on mixed patterns like `## 2.1a.`.
- Placing `_compute_section_similarity` in `_docs_consistency_lib.py`: rejected because that library's functions all follow `(docs_dir: Path, files: list[DocFile]) -> list[Issue]` signature, which doesn't fit a pure text similarity utility.
- Using TF-IDF or cosine similarity for content comparison: rejected because Jaccard on word tokens is simpler and avoids external dependencies.

## Implementation

### Target file

`tools/check_docs_quality.py`

### Procedure

1. Add private `_compute_section_similarity(section_a_text: str, section_b_text: str, *, threshold: float = 0.85) -> bool` helper function
2. Extend `check_duplicate_heading_numbers` with alphabetic-suffix regex pattern
3. Add `check_content_similarity(docs_dir: Path, files: list[DocFile]) -> list[Issue]` core check function
4. Register `check_content_similarity` with `@register_core_check("content_similarity", ...)`

### Method

#### Step 1: Add `_compute_section_similarity` helper

Add after the existing imports and before the first core check function definition. Tokenize by whitespace/punctuation, compute Jaccard similarity (intersection over union of word sets), return True if similarity >= threshold.

```python
def _compute_section_similarity(section_a_text: str, section_b_text: str, *, threshold: float = 0.85) -> bool:
    """Return True if the two section texts overlap above the given threshold."""
    import re
    
    def tokenize(text: str) -> set[str]:
        # Remove fenced code blocks and inline code
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        # Lowercase and split on non-alphanumeric
        words = re.findall(r'[a-z0-9]+', text.lower())
        return set(words)
    
    set_a = tokenize(section_a_text)
    set_b = tokenize(section_b_text)
    
    if not set_a or not set_b:
        return False
    
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    
    if union == 0:
        return False
    
    return (intersection / union) >= threshold
```

#### Step 2: Extend `check_duplicate_heading_numbers`

In `check_duplicate_heading_numbers`, after the existing regex processing block, add a second regex pass for alphabetic-suffix headings:

```python
# Keep the existing purely-numeric pattern unchanged:
numeric_pattern = r"^(#{1,6})\s+(\d[\d.]*\.)\s+"

# Add alphabetic-suffix pattern alongside it:
alpha_suffix_pattern = r"^(#{1,6})\s+(\d+[a-z]+)\.\s+"
```

After grouping by `(level, heading_number)` using the existing logic, add a second grouping step:

```python
# Group by (level, base_number) for alphabetic-suffix detection
alpha_groups: dict[tuple[int, int], list[tuple[int, str]]] = {}
for line_num, heading_number in alpha_matches:
    # Extract base number: digits before the alphabetic suffix
    base_match = re.match(r"(\d+)[a-z]+", heading_number)
    if base_match:
        base_number = int(base_match.group(1))
        level = int(line_num)  # derived from heading marker count
        key = (level, base_number)
        if key not in alpha_groups:
            alpha_groups[key] = []
        alpha_groups[key].append((line_num, heading_number))

# Flag pairs where base numbers match but full heading numbers differ
for key, entries in alpha_groups.items():
    if len(entries) > 1:
        # Multiple headings with same base number at same level — probable near-duplicate
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                _, num_i = entries[i]
                _, num_j = entries[j]
                if num_i != num_j:
                    issues.append(Issue(
                        kind="duplicate_heading",
                        severity="warning",
                        message=f"Probable near-duplicate heading: '{num_i}' and '{num_j}' at same level {key[0]}",
                        line=entries[j][0],
                        doc=file.path,
                    ))
```

#### Step 3: Add `check_content_similarity` core check

```python
@register_core_check("content_similarity")
def check_content_similarity(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Flag sections within the same document whose body text overlaps above threshold."""
    issues: list[Issue] = []
    
    for file in files:
        try:
            content = file.read_text()
        except OSError:
            continue
        
        # Extract sections: split by heading markers
        sections = _extract_sections(content)
        
        # Compute pairwise similarity
        for i in range(len(sections)):
            for j in range(i + 1, len(sections)):
                if _compute_section_similarity(sections[i]["body"], sections[j]["body"]):
                    issues.append(Issue(
                        kind="content_similarity",
                        severity="warning",
                        message=f"Content similarity detected between sections '{sections[i]['heading']}' and '{sections[j]['heading']}'",
                        line=sections[j]["line"],
                        doc=file.path,
                    ))
    
    return issues
```

Helper for section extraction:

```python
def _extract_sections(content: str) -> list[dict]:
    """Extract sections from markdown content, returning list of dicts with 'heading', 'body', 'line' keys."""
    import re
    
    sections = []
    lines = content.split('\n')
    current_heading = None
    current_body_lines = []
    current_line = None
    
    for idx, line in enumerate(lines, start=1):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            if current_heading is not None:
                sections.append({
                    "heading": current_heading.strip(),
                    "body": "\n".join(current_body_lines).strip(),
                    "line": current_line,
                })
            current_heading = match.group(2)
            current_line = idx
            current_body_lines = []
        else:
            current_body_lines.append(line)
    
    # Don't forget the last section
    if current_heading is not None:
        sections.append({
            "heading": current_heading.strip(),
            "body": "\n".join(current_body_lines).strip(),
            "line": current_line,
        })
    
    return sections
```

### Details

- The alphabetic-suffix regex `r"^(#{1,6})\s+(\d+[a-z]+)\.\s+"` matches headings like `## 2a.`, `## 7c.`, etc. It does NOT match `## 2.1` (pure numeric subsection) — those are handled by the existing `\d[\d.]*\.` pattern.
- Base number extraction: `re.match(r"(\d+)[a-z]+", "2a")` → `"2"`; `re.match(r"(\d+)[a-z]+", "7c")` → `"7"`.
- For the known defect case (`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`), running `uv run python tools/check_docs_quality.py --only duplicate_heading_numbers` should report one Issue for the `## 7c.` duplicate at line 87.
- Content-similarity check processes each DocFile independently (intra-document only). Pairwise comparison of all section pairs within a single document.
- The `_extract_sections` helper splits content by heading markers and accumulates body text until the next heading. Empty bodies are skipped in similarity computation.
- Both checks use the existing `Issue` class and `@register_core_check` mechanism — no changes to the tool's CLI interface.

## Compatibility considerations

- The alphabetic-suffix check adds new warnings but does not change existing behavior for purely-numeric headings.
- The content-similarity check is additive — no existing outputs are affected unless the tool is invoked with `--only content_similarity`.
- No changes to public APIs, configuration schema, or CLI arguments.

## Security considerations

N/A: this change adds quality-checking logic, not data access or network operations.

## Rollback considerations

- To revert the alphabetic-suffix check: remove the second regex pattern and its grouping logic from `check_duplicate_heading_numbers`.
- To revert the content-similarity check: remove the `check_content_similarity` function and its `@register_core_check` registration.
- No database migrations or persistent state changes — rollback is straightforward.

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

- [ ] Two mutually exclusive regex patterns exist in `check_duplicate_heading_numbers`: original `\d[\d.]*\.` for pure numeric, `\d+[a-z]+\.` for alphabetic-suffix
- [ ] Base number extraction correctly handles `2a` → `2`, `7c` → `7`
- [ ] Pairs with matching base numbers but different full heading numbers are flagged as probable near-duplicates
- [ ] Legitimate numeric subsections (`2.1`, `2.2`) are NOT flagged as duplicates
- [ ] `_compute_section_similarity` returns correct Jaccard similarity for known inputs
- [ ] `check_content_similarity` flags overlapping sections above threshold
- [ ] `check_content_similarity` does NOT flag templated-but-distinct sections below threshold
- [ ] Both checks registered via `@register_core_check` and appear in standard invocation output
- [ ] Known defect case (`## 7c.` duplicate) produces exactly one Issue when checked standalone

## Out of scope

- Retroactively scanning all of `docs/` for existing content-similarity duplicates
- Any change to `check_duplicate_heading_numbers`'s existing purely-numeric detection behavior
- Adding cross-document content-similarity checks (only intra-document)
- Configurable thresholds via config file (threshold hardcoded at 0.85 initially)
- Handling edge cases like `## 2.1a.` or `## 2a1.` (silently skipped — acceptable per Risks section)

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260914-112554_qa02_duplicate-section-and-merge-boundary-detection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-091956_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-093651
- **Related target files**: tools/check_docs_quality.py
