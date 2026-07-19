# `parse_markdown` emits a spurious empty `<root>` section for any file with YAML frontmatter followed by a blank line before the first heading

Discovered while implementing `implementations/20260719-110947_test_mdq_service.py.md`
(tags/token_count test coverage + `parse_markdown` signature migration for
`tests/test_mdq_service.py`).

## Problem

`scripts/mcp_servers/mdq/parser.py`'s `parse_markdown()` decides whether to keep
a section with `if current_section is not None and current_section["content_lines"]:`
(`parser.py:160` and `:192`) — this checks whether the raw `content_lines` list is
**non-empty**, not whether the section's *finalized* content (after
`"\n".join(...).strip()` in `_finalize_section`) is non-empty.

After a YAML frontmatter block is skipped, parsing resumes at the line right
after the closing `---`. If that line is blank (the common case — a blank
line conventionally separates frontmatter from the first heading), the
blank line is appended to a freshly-created `<root>` section's
`content_lines` (`parser.py:144-156`). When the first real heading is then
encountered, `content_lines` has length 1 (containing only `""`), which is
truthy as a list, so `_finalize_section` is called and an **empty `<root>`
section (`content == ""`) is appended to the returned `sections` list** —
even though there is no real content before the first heading.

This contradicts the parser's own established contract, documented and
tested elsewhere in the same file: `test_heading_with_no_content_body_omitted`
(`tests/test_mdq_service.py`) asserts that a heading followed immediately by
another heading with no content between them produces no section for the
empty heading. The `<root>` pseudo-section should follow the same rule, but
does not, because the omission check is list-length-based rather than
finalized-content-based.

## Reproduction

```python
import asyncio
from pathlib import Path
from mcp_servers.mdq.parser import parse_markdown
from mcp_servers.mdq.models import ParseMarkdownRequest

# any frontmatter, even well-formed and valid, followed by a blank line
# before the first heading:
content = "---\ntags: [x]\n---\n\n# Title\n\nBody."
```

Result: `sections == [{"heading": "<root>", ..., "content": "", ...}, {"heading": "Title", ..., "content": "Body.", ...}]`
— two sections instead of the expected one.

This is **not specific to malformed frontmatter** — it reproduces with any
valid frontmatter block (with or without a `tags` key) as long as a blank
line separates the closing `---` from the first heading, which is the
conventional Markdown frontmatter style used throughout this repo's own
fixtures (e.g. `tests/test_mdq_service.py`'s `test_frontmatter_stripped`
fixture: `"---\ntitle: Test\n---\n\n# Title\n\nBody."`).

## Downstream impact

`scripts/mcp_servers/mdq/indexer.py`'s `_index_single_file` iterates every
section returned by `parse_markdown` and inserts one `chunks` row per
section with no empty-content filter. This means **every Markdown file
with frontmatter, indexed by the real indexing pipeline, gets one extra
junk chunk row** in the `chunks` table: `heading="<root>"`, `content=""`,
`char_count=0`, `token_count=1` (the `_estimate_token_count` floor). This
pollutes search/grep/outline results with a spurious empty-heading chunk
for any frontmatter-bearing document.

## Why this wasn't fixed inline

`scripts/mcp_servers/mdq/parser.py` is outside the target-file scope of
`implementations/20260719-110947_test_mdq_service.py.md`, which is
test-file-only (`tests/test_mdq_service.py`). Fixing the root cause
(changing the section-keep check in `parser.py` to test the finalized,
stripped content rather than raw `content_lines` list-truthiness) is a
one-line change but is real production behavior change to
`parser.py`/`indexer.py`'s persisted output, so per this repo's own
"file, don't silently patch" convention (`rules/coding.md`'s "Current
behavior" classification: "Implementation fix required") it is filed here
rather than folded into an unrelated test-only implementation cycle.

Because of this bug, `tests/test_mdq_service.py::TestParseMarkdown::test_malformed_frontmatter_does_not_crash_indexing`
was written to assert only the tags-fallback and `Title`-section contract
(not `len(sections) == 1`, which the doc that authored this test originally
specified but which fails against actual current behav0r) — see that test's
docstring/comment for the cross-reference back to this issue.

## Recommended action

In `parser.py`, change the finalize-and-keep condition (both occurrences,
`:160` and `:192`) from checking `current_section["content_lines"]`
list-truthiness to checking whether the finalized content is non-empty,
e.g. compute `_finalize_section(current_section)` first and only append it
if `finalized["content"]` is non-empty (or equivalently, check
`"\n".join(current_section["content_lines"]).strip()` before finalizing).
Add a regression test asserting that a file with frontmatter followed by a
blank line and then a heading (no other pre-heading content) parses to
exactly one section.
