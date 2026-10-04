## Goal
Make front matter `related:` the only store of this document's cross-references (REQ-004: merge the body Related entries into it and remove the body section).

## Scope
- In: this file's front matter `related:` block and its body `## Related Docs`, `## Related Documents` section(s).
- Out: all other body content, headings, and links; every other file.

## Assumptions
- Verified by scan on 20261004: 2 body Related section(s), 4 referenced document(s), 3 absent from front matter, 0 non-link line(s).
- General documents drop the body section and ADR documents keep theirs (owner review at the Plan's Step 3 gate, UNK-01).
- Front matter entries use basenames; `related:` shape in this file: block.

## Design decisions
- Apply through the `merge-related` subcommand, one documentation area per commit, rather than by hand.
- Never silently drop information: entries are merged, and sections with non-link lines are reported for a decision.

## Alternatives considered
- Hand edit: rejected; error-prone across about 190 documents.
- Keep the body section as a rendered copy of front matter: rejected; it reintroduces the duplication this Plan removes.

## Implementation
### Target file
`docs/23_agent/agent_08_03_configuration-tools-memory.md`

### Procedure
1. Run the dry-run for this file's documentation area and review this file's entry.
2. Run `merge-related --fix` for the area (after the Plan's Step 3 review).
3. Confirm the diff touches only the front matter `related:` block and the removed body section(s).

### Method
- `uv run python tools/manage_frontmatter.py merge-related docs/23_agent/agent_08_03_configuration-tools-memory.md` (dry-run), then the same command with `--fix`; area commits use the area directory glob.
- Expected: 3 entries added to front matter; body section(s) `## Related Docs`, `## Related Documents` removed when link-only.

### Details
- `## Keywords` must still follow the preceding content, with one blank line between sections, and the file must end with a newline.

## Compatibility considerations
- Link targets and inbound references are unchanged; navigation continuity moves to front matter `related:`, the index, and the area document guides.

## Security considerations
- Documentation only; no secrets or configuration values are involved.

## Rollback considerations
- Revert the commit for this documentation area (`docs/23_agent`); no other area depends on it.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_03_configuration-tools-memory.md`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_content_policy.py`
- `git diff` shows changes only in the front matter and the removed section(s).

## Completion criteria
- Front matter `related:` holds every previous entry plus the merged body entries, with no duplicate and no self-reference.
- No `## Related Documents`, `## Related Docs`, or `## Related Chapters` section remains.
- Structure and quality checkers report no new findings for this file.

## Out of scope
- Any other body edit, heading change, or link change.
- Editing other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the merged front matter and remove the body section(s) via `merge-related --fix` | Completed | 20261004-125246 | 20261004-125246 | applied via merge-related --fix; non-link sections handled per owner review |
| 2 | N/A: documentation file; covered by checker runs | Completed | 20261004-125246 | 20261004-125246 | N/A: documentation file; covered by checker runs |
| 3 | Run `check_docs_structure.py`, `check_docs_quality.py`, and `check_docs_content_policy.py` | Completed | 20261004-125246 | 20261004-125246 | check_docs_structure/quality/content_policy/consistency run over docs (no new findings); full suite 8092 passed, 6 failed (same unrelated baseline) |
| 4 | N/A: this file is the documentation change | Completed | 20261004-125246 | 20261004-125246 | N/A: this file is the documentation change |

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
- **Requirement ID**: `REQ-004` (merge body Related entries into front matter and remove the body section)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: docs/23_agent/agent_08_03_configuration-tools-memory.md