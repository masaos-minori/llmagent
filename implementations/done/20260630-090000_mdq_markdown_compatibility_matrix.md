## Goal
- Add Markdown compatibility matrix to the mdq-mcp section in `docs/04_mcp_04_server_catalog.md`, clarifying fallback behavior for unsupported syntax.

## Scope
- **In-Scope**:
  - Add Markdown compatibility table to mdq-mcp section in `docs/04_mcp_04_server_catalog.md`
  - Supported: ATX headings (all levels), fenced code blocks, YAML frontmatter, root section (content before first heading), duplicate headings
  - Unsupported: Setext headings (=== / ---), HTML blocks, MDX, GFM tables, inline tags
  - Clarify fallback behavior for unsupported syntax (treated as plain text)
- **Out-of-Scope**:
  - Implementation changes to `parser.py`
  - Adding new Markdown feature support
  - Test changes

## Assumptions
1. `scripts/mcp/mdq/parser.py` module docstring (L10-L30) is the authoritative source for compatibility info
2. mdq-mcp section in `docs/04_mcp_04_server_catalog.md` (L283-294) is the target for update
3. Setext headings (`===`, `---`) are treated as plain text (parser.py:L25-L28)
4. GFM tables are not parsed but do not affect section splitting (kept as content)

## Implementation

### Target file
`docs/04_mcp_04_server_catalog.md` — mdq-mcp section

### Procedure
1. Read `scripts/mcp/mdq/parser.py` module docstring to extract compatibility info
2. Design a 3-column table: Markdown Feature | Support | Fallback Behavior
3. Insert the table after the existing mdq-mcp section content (around L283)

### Method
- Add the compatibility table as a Markdown table block within the mdq-mcp section
- Use consistent terminology matching parser.py docstring
- Reference `scripts/mcp/mdq/parser.py` as the authoritative source for compatibility details

### Details

```markdown
| Markdown Feature         | Support | Fallback Behavior                         |
|--------------------------|---------|-------------------------------------------|
| ATX headings (H1–H6)     | Yes     | —                                         |
| Fenced code blocks       | Yes     | # inside fences not treated as headings   |
| YAML frontmatter         | Yes     | Parsed and stripped at file start         |
| Content before H1        | Yes     | Stored as <root> section                  |
| Duplicate headings       | Yes     | Distinct chunk IDs via ordinal            |
| Setext headings (===,---) | No     | Treated as plain text                     |
| HTML blocks              | No      | Treated as plain text                     |
| MDX                      | No      | Not indexed (.mdx excluded by glob)       |
| GFM tables               | No      | Stored as plain text in parent section    |
| Inline HTML tags         | No      | Treated as plain text                     |
```

## Validation plan
- Run `pre-commit run --all-files` to confirm docs check passes
- Manual verification: `grep -n "Setext\|frontmatter\|MDX" docs/04_mcp_04_server_catalog.md` — confirm new table exists
