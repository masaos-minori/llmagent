# Implementation: Fix ordinal tracking and empty-section handling bugs in MDQ parser

## Goal

Fix ordinal computation logic in `scripts/mcp/mdq/parser.py` and expand unit test coverage to cover code fences, frontmatter, repeated headings, and nested heading paths.

## Scope

- **In-Scope**:
  - `scripts/mcp/mdq/parser.py` — fix ordinal computation logic; add ordinal tracking per `(level, parent_path)` key
  - `tests/test_mdq_service.py` — add unit tests for: code fences, frontmatter stripping, repeated headings, nested paths, malformed headings, headings with no content body
- **Out-of-Scope**:
  - DB schema changes (no changes needed)
  - `indexer.py`, `service.py`, `models.py` — no interface changes required
  - Setext heading support (explicitly unsupported per parser docstring)
  - RAG ingestion pipeline (`rag/ingestion/chunk_splitter.py`) — separate module

## Verification Results

### 1. Current state: ordinal is always 0

**File**: `scripts/mcp/mdq/parser.py:173`
```python
"ordinal": section.get("ordinal", 0),
```

- No ordinal computation exists in the parser — all sections get `ordinal=0`
- This means repeated headings at the same level will have identical chunk_ids (since ordinal is part of the chunk_id hash input)
- The plan's description of the bug (`same_level_headings` computed after popping) doesn't match current code — it appears the ordinal computation was never implemented

### 2. Current state: empty-body headings are omitted

**File**: `scripts/mcp/mdq/parser.py:130,157`
```python
if current_section is not None and current_section["content_lines"]:
```

- Empty-body sections (headings with no content lines) are silently omitted
- This is acceptable per the plan's assumption — headings with no content body should be omitted

### 3. Existing test coverage is minimal

**File**: `tests/test_mdq_service.py:114-143`
- Only 3 tests for `TestParseMarkdown`:
  - `test_returns_sections_with_headings` — basic happy path
  - `test_returns_root_for_content_before_heading` — root section handling
  - `test_raises_for_missing_file` — error handling

### 4. Ordinal scope resolution (UNK-01)

**Decision**: Ordinal should be scoped per `(level, parent_path)` tuple:
- Two `## API` headings under `# Getting Started` should have ordinal=1 and ordinal=2 respectively
- Two `## API` headings under `# Reference` should also have ordinal=1 and ordinal=2 (different parent scope)
- This ensures unique chunk_ids while keeping ordinals meaningful within their parent context

## Implementation

### Target file: `scripts/mcp/mdq/parser.py`

#### Procedure

Add ordinal counter keyed by `(level, parent_path)` tuple.

#### Details

**Add before the main loop (after line 107):**
```python
# Ordinal counter: tracks rank of each heading among same-level headings with the same parent
ordinal_counter: dict[tuple[int, str], int] = {}
```

**After building `heading_path` and `parent_heading` (after line 140):**
```python
# Compute ordinal for this heading within its parent scope
parent_path = heading_path if heading_path else "<root>"
key = (heading_level_val, parent_path)
ordinal_counter[key] = ordinal_counter.get(key, 0) + 1
current_section["ordinal"] = ordinal_counter[key]
```

**Remove or keep the existing `heading_path` computation** — it's already correct and used for the ordinal key.

### Target file: `tests/test_mdq_service.py`

#### Procedure

Add new test cases to `TestParseMarkdown`.

#### Details

**Append after existing `TestParseMarkdown` tests:**
```python
class TestParseMarkdown:
    ...existing tests...

    def test_code_fence_hash_not_treated_as_heading(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """# inside a code fence must not create a new section."""
        f = tmp_path / "fence.md"
        f.write_text(
            "# Title\n\n```text\n# Not a heading\n```\n\nBody.", encoding="utf-8"
        )
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "Title" in headings
        assert "# Not a heading" not in headings
        assert len([s for s in sections if s["heading"] == "Title"]) == 1

    def test_frontmatter_stripped(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """YAML frontmatter is skipped; first ATX heading becomes first section."""
        f = tmp_path / "frontmatter.md"
        f.write_text(
            "---\ntitle: Test\n---\n\n# Title\n\nBody.", encoding="utf-8"
        )
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "# Title" not in headings  # frontmatter not treated as heading
        assert "Title" in headings

    def test_repeated_headings_have_distinct_ordinals(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Two ## API headings produce ordinal=1 and ordinal=2."""
        f = tmp_path / "repeated.md"
        f.write_text(
            "# Title\n\n## API\n\nFirst body.\n\n## API\n\nSecond body.", encoding="utf-8"
        )
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        api_sections = [s for s in sections if s["heading"] == "API"]
        assert len(api_sections) == 2
        ordinals = sorted(s["ordinal"] for s in api_sections)
        assert ordinals == [1, 2], f"Expected [1, 2], got {ordinals}"

    def test_nested_heading_path(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """### C under # A / ## B produces heading_path='A > B'."""
        f = tmp_path / "nested.md"
        f.write_text("# A\n\n## B\n\n### C\n\nBody.", encoding="utf-8")
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        c_section = next(s for s in sections if s["heading"] == "C")
        assert c_section["heading_path"] == "A > B"
        assert c_section["parent_heading"] == "B"

    def test_malformed_heading_treated_as_content(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """#NoSpace (no space after #) is treated as plain content."""
        f = tmp_path / "malformed.md"
        f.write_text("#NoSpace\n\nBody.", encoding="utf-8")
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "#NoSpace" not in headings  # not parsed as heading

    def test_heading_level_returned_correctly(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Verify heading_level field equals the ATX # count."""
        f = tmp_path / "levels.md"
        f.write_text("# A\n\n## B\n\n### C\n\nBody.", encoding="utf-8")
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        levels = {s["heading"]: s["heading_level"] for s in sections}
        assert levels["A"] == 1
        assert levels["B"] == 2
        assert levels["C"] == 3

    def test_heading_with_no_content_body_omitted(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        """Heading with no content lines is omitted from results."""
        f = tmp_path / "empty.md"
        f.write_text("# Title\n\n## Empty\n\n## Has Content\n\nBody.", encoding="utf-8")
        sections = asyncio.run(
            parse_markdown(service, ParseMarkdownRequest(path=str(f)))
        )
        headings = [s["heading"] for s in sections]
        assert "Empty" not in headings  # empty body → omitted
        assert "Has Content" in headings

    def test_empty_allowlist_denies_all(self) -> None:
        """Empty allowed_dirs denies all paths."""
        ...
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `parser.py` ordinal computation | Unit test repeated headings have distinct ordinals | `uv run pytest tests/test_mdq_service.py::TestParseMarkdown::test_repeated_headings_have_distinct_ordinals` | PASS — ordinal=1 and ordinal=2 |
| `parser.py` code fence isolation | Unit test fence-interior `#` not parsed as heading | `uv run pytest tests/test_mdq_service.py::TestParseMarkdown::test_code_fence_hash_not_treated_as_heading` | PASS |
| `parser.py` frontmatter stripping | Unit test YAML frontmatter skipped | `uv run pytest tests/test_mdq_service.py::TestParseMarkdown::test_frontmatter_stripped` | PASS — first ATX heading is first section |
| `parser.py` nested paths | Unit test heading_path contains ancestor labels | `uv run pytest tests/test_mdq_service.py::TestParseMarkdown::test_nested_heading_path` | PASS — heading_path = "A > B" |
| `parser.py` malformed headings | Unit test #NoSpace treated as content | `uv run pytest tests/test_mdq_service.py::TestParseMarkdown::test_malformed_heading_treated_as_content` | PASS |
| `parser.py` heading levels | Unit test heading_level equals ATX # count | `uv run pytest tests/test_mdq_service.py::TestParseMarkdown::test_heading_level_returned_correctly` | PASS |
| `parser.py` empty body omission | Unit test empty-body headings omitted | `uv run pytest tests/test_mdq_service.py::TestParseMarkdown::test_heading_with_no_content_body_omitted` | PASS — Empty heading not in results |
| Regression suite | Existing mdq tests unbroken | `uv run pytest tests/test_mdq_service.py -v` | All pass |
| Lint / type | No new errors | `uv run ruff check scripts/mcp/mdq/parser.py && uv run mypy scripts/mcp/mdq/parser.py --ignore-missing-imports` | No errors |

## Risks & Mitigations

- **Risk**: Fixing ordinal changes `chunk_id` hashes for files with repeated headings, making previously stored chunk IDs invalid → **Mitigation**: Require a forced re-index (`refresh_index force=True`) after deploy; document in deploy notes.
- **Risk**: Ordinal scope ambiguity (global vs. per-parent) could lead to a second fix cycle → **Mitigation**: Resolved UNK-01 by reading `indexer.py` chunk_id generation before writing any code; chose per-parent `(level, parent_path)` scope for unique chunk_ids.
- **Risk**: `parse_markdown` complexity D (29) makes isolated changes risky → **Mitigation**: Add behavior-lock tests before modifying the function; run full test suite after each sub-step.
