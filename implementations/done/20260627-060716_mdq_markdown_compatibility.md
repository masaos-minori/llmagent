## Goal

Document production Markdown compatibility scope for MDQ by clearly stating supported and unsupported Markdown features, ensuring parser tests align with documented scope, and defining predictable fallback behavior for unsupported syntax.

## Scope

**In-Scope**:
- Document support status for: CommonMark headings, ATX headings, Setext headings, fenced code blocks, frontmatter, GitHub Flavored Markdown tables, inline tags, HTML blocks, MDX, duplicate headings, content before first heading
- Update parser.py docstring with complete compatibility scope
- Add documentation in 04_mcp_04_server_catalog.md for MDQ Markdown support
- Add known issues to 04_mcp_90_inconsistencies_and_known_issues.md

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' documentation

## Assumptions

1. Supported features: ATX headings, fenced code blocks, frontmatter, duplicate headings, content before first heading, nested heading hierarchy
2. Unsupported features: Setext headings, inline tags, HTML blocks, MDX, GFM tables (no parsing, but not required for section extraction)
3. Fallback behavior: unsupported syntax may cause heading misclassification

## Implementation

### Target file: scripts/mcp/mdq/parser.py

**Procedure**: Update docstring with complete compatibility scope.

**Method**: Modify parser.py docstring to add comprehensive supported/unsupported features list.

**Details**:
1. Update docstring to include complete compatibility scope:
   - Supported: CommonMark headings, ATX headings, Setext headings (partial), fenced code blocks (```, ~~~), frontmatter (YAML), duplicate headings, content before first heading, nested heading hierarchy
   - Unsupported: Setext-style headings (===, --- underlines), inline tags, HTML blocks, MDX, GFM tables (no parsing)
2. Document fallback behavior for unsupported syntax:
   - Unsupported syntax may cause heading misclassification
   - Document specific examples of heading misclassification

### Target file: docs/04_mcp_04_server_catalog.md

**Procedure**: Add MDQ Markdown support section listing all supported/unsupported features.

**Method**: Add new section to existing documentation.

**Details**:
1. Add MDQ Markdown support section listing all supported/unsupported features
2. Include specific examples of each feature type
3. Document expected behavior for unsupported syntax

### Target file: docs/04_mcp_90_inconsistencies_and_known_issues.md

**Procedure**: Add MDQ known issues for unsupported syntax.

**Method**: Add new section to existing documentation.

**Details**:
1. Add MDQ known issues for unsupported syntax (HTML blocks, MDX, inline tags)
2. Document potential heading misclassification for unsupported syntax
3. Include specific examples of known issues with fallback behavior

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| parser.py | Verify docstring includes complete compatibility scope | Check docstring content | All supported/unsupported features documented |
| 04_mcp_04_server_catalog.md | Verify MDQ Markdown support section exists | Check documentation | Clear list of supported/unsupported features |
| 04_mcp_90_inconsistencies_and_known_issues.md | Verify MDQ known issues include unsupported syntax | Check documentation | Known issues documented with fallback behavior |

## Risks

- **Risk**: Documentation may become outdated as parser evolves | **Likelihood**: Medium | **Mitigation**: Update documentation alongside parser changes; add docstring review to PR checklist | False
- **Risk**: Users may not understand fallback behavior implications | **Likelihood**: Low | **Mitigation**: Document specific examples of heading misclassification for unsupported syntax | False
