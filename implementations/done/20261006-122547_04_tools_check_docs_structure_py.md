## Goal

Strengthen `check_docs_structure.py`: detect body `Related Documents` / `Related Docs` / `Related Chapters` heading at ANY level in non-ADR docs (ignore fenced code); validate `related` format (basenames ending in `.md`); keep target/self-ref/dup checks; leave ADR requirement unchanged; update error messages + module docstring. (REQ-004 / AC-4)

## Scope

- Modify `_RELATED_HEADING_RE` to match headings at ANY level (not just `^## `)
- Add `related` format validation (basenames ending in `.md`)
- Keep target-existence, self-reference, and duplicate checks
- Leave the ADR requirement unchanged
- Update error messages and the module docstring

## Assumptions

- The existing `strip_fenced_code()` function correctly strips fenced code blocks before regex matching
- The ADR requirement for `## Related Documents` is intentional and must not be weakened
- The `related` format validation should reject entries that use paths, anchors, or non-`.md` forms

## Design decisions

- Adopt the recommended option: strengthen `_RELATED_HEADING_RE` to match any heading level using `\S*#` prefix instead of `^## `
- Add a new validation function for `related` format (basenames ending in `.md`)
- Keep the existing target-existence, self-reference, and duplicate checks unchanged
- Update error messages to reflect the new behavior

## Alternatives considered

- Using a more complex AST-based approach for fenced-code detection — rejected because `strip_fenced_code()` already works and is simpler
- Strengthening `manage_frontmatter.py` to any-level per owner decision — rejected because UNK-04 recommends documenting it as a one-time migration aid

## Implementation

### Target file

`tools/check_docs_structure.py`

### Procedure

1. Modify `_RELATED_HEADING_RE` to match headings at ANY level (not just `^## `)
2. Add `related` format validation function
3. Keep target-existence, self-reference, and duplicate checks
4. Leave the ADR requirement unchanged
5. Update error messages and the module docstring

### Method

- Edit the regex pattern and add a new validation function
- Update error messages to reflect the new behavior
- Update the module docstring

### Details

**Before (line 184-185):**
```python
 RELATED_HEADING_RE = re.compile(
     r"^## (?:Related Documents|Related Docs|Related Chapters)[ \t]*$", re.MULTILINE
 )
```

**After:**
```python
 RELATED_HEADING_RE = re.compile(
     r"^(?:#{1,6}\s+)(?:Related Documents|Related Docs|Related Chapters)[ \t]*$", re.MULTILINE
 )
```

**New validation function to add:**
```python
def _validate_related_format(related_entries: list[str]) -> list[str]:
    """Validate that related entries are basenames ending in .md."""
    issues = []
    for entry in related_entries:
        basename = Path(entry).name
        if not basename.endswith(".md"):
            issues.append(f"related entry {entry!r}: must end in '.md'")
        if "/" in entry or "#" in entry:
            issues.append(f"related entry {entry!r}: must be a plain basename (no path or anchor)")
    return issues
```

## Compatibility considerations

- This is a public CLI contract change — consumers of `check_docs_structure.py` (CI, pre-commit, tests) will see new error messages
- The strengthened check may flag existing violations that were previously undetected
- The `related` format validation adds a new constraint not previously enforced

## Security considerations

- No security implications — this is a documentation-structure check strengthening
- The new validation prevents malformed `related:` entries from being silently accepted

## Rollback considerations

- Reverting would restore the weaker check — body `### Related Documents` headings would go undetected
- If the `related` format validation causes regressions, it can be relaxed (but the current constraint is correct)

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_docs_structure.py` | Unit: any-level detection, fenced-code ignore, format validation, ADR unchanged | `uv run pytest tests/tools/test_check_docs_structure.py -q -p no:cacheprovider -p no:randomly` | New cases pass; existing cases still pass |
| Changed tool files | Static analysis | `uv run ruff`, `uv run mypy`, `uv run bandit` (per `routing.md`) | Clean |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- `_RELATED_HEADING_RE` matches headings at ANY level (not just `##`)
- `related` format validation added (basenames ending in `.md`)
- Target-existence, self-reference, and duplicate checks preserved
- ADR requirement unchanged
- Error messages and module docstring updated
- All unit tests pass
- Static analysis clean

## Out of scope

- Any change to ADR documents or ADR rules (handled by `rel002`)
- Changing contextual links inside ordinary prose
- Removing `Reading Order`, `Related ADRs` or other purpose-specific navigation sections
- Reorganizing or renaming documents
- Changing front matter fields other than `related:`
- Adding a local gate to `.pre-commit-config.yaml`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Strengthen `_RELATED_HEADING_RE` to any-level detection | Completed | 20261006-222159 | 20261006-222159 | REQ-004 |
| 2 | Add `related` format validation | Completed | 20261006-222159 | 20261006-222159 | REQ-004 |
| 3 | Update error messages and module docstring | Completed | 20261006-222159 | 20261006-222159 | REQ-004 |
| 4 | Add or update tests per Validation plan | Completed | 20261006-222159 | 20261006-222159 | REQ-006 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-222159 | 20261006-222159 |  |
| 6 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-222159 | 20261006-222159 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261005-143453_rel001_consolidate-related-document-information-into-front-matter-related.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-073642_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-122547
- **Related target files**: tools/check_docs_structure.py