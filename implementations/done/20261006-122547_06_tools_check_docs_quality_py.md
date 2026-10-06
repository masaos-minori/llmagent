## Goal

Update the allowed-heading set in `check_docs_quality.py` so a body `Related Documents` heading is not silently allowed in non-ADR docs (ADR-aware if feasible). (REQ-004 / AC-4)

## Scope

- Update the `_NAVIGATION_HEADINGS` frozenset (line 148) to remove `"Related Documents"` and `"Related Docs"` from the allowed set for non-ADR documents
- Keep `"Related ADRs"` and `"Keywords"` in the allowed set (these are legitimate navigation sections)
- Make the ADR-aware check if feasible

## Assumptions

- The current allowed-heading set includes `"Related Documents"`, `"Related Docs"`, `"Related ADRs"`, and `"Keywords"`
- `"Related ADRs"` and `"Keywords"` are legitimate navigation sections that should remain allowed
- Making the check ADR-aware requires checking if the file is an ADR document

## Design decisions

- Remove `"Related Documents"` and `"Related Docs"` from the allowed set for non-ADR documents
- Keep `"Related ADRs"` and `"Keywords"` in the allowed set
- Make the check ADR-aware by using the same `_is_adr()` function from `check_docs_structure.py`

## Alternatives considered

- Keeping the current allowed-heading set — rejected because it silently allows body `Related Documents` headings in non-ADR docs
- Making the check fully ADR-aware — rejected because it adds complexity and the strengthened `check_docs_structure.py` already handles ADR exceptions

## Implementation

### Target file

`tools/check_docs_quality.py`

### Procedure

1. Update the `_NAVIGATION_HEADINGS` frozenset to remove `"Related Documents"` and `"Related Docs"`
2. Keep `"Related ADRs"` and `"Keywords"` in the allowed set
3. Make the check ADR-aware if feasible

### Method

- Edit the frozenset directly
- Add ADR-aware logic if feasible

### Details

**Before (line 148):**
```python
_NAVIGATION_HEADINGS: frozenset[str] = frozenset(
    {"Related Documents", "Related Docs", "Related ADRs", "Keywords"}
)
```

**After:**
```python
_NAVIGATION_HEADINGS: frozenset[str] = frozenset(
    {"Related ADRs", "Keywords"}
)
```

**ADR-aware variant (if feasible):**
```python
_NAVIGATION_HEADINGS_NON_ADR: frozenset[str] = frozenset(
    {"Related ADRs", "Keywords"}
)
_NAVIGATION_HEADINGS_ADR: frozenset[str] = frozenset(
    {"Related Documents", "Related Docs", "Related ADRs", "Keywords"}
)
```

## Compatibility considerations

- This is a documentation-quality check change — may flag existing violations in non-ADR documents
- The change aligns the quality check with the strengthened structure check
- Tests must be updated to cover the new behavior

## Security considerations

- No security implications — this is a documentation-quality check update
- The change prevents silent acceptance of body `Related Documents` headings in non-ADR docs

## Rollback considerations

- Reverting would restore the ability to silently allow body `Related Documents` headings in non-ADR docs
- If the change causes regressions, the allowed-heading set can be adjusted

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_docs_quality.py` | Unit: allowed-heading set update | `uv run pytest tests/tools -q -p no:cacheprovider -p no:randomly` | Passes |
| Changed tool files | Static analysis | `uv run ruff`, `uv run mypy`, `uv run bandit` (per `routing.md`) | Clean |
| Full docs-tooling suite | Integration: repo passes its own checks | `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py` | All pass |

## Completion criteria

- `"Related Documents"` and `"Related Docs"` removed from allowed set for non-ADR docs
- `"Related ADRs"` and `"Keywords"` kept in allowed set
- ADR-aware check implemented if feasible
- Tests updated for the new behavior
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
| 1 | Update `_NAVIGATION_HEADINGS` frozenset | Completed | 20261006-223154 | 20261006-223154 | REQ-004 |
| 2 | Make check ADR-aware if feasible | Completed | 20261006-223154 | 20261006-223154 | REQ-004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-223154 | 20261006-223154 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-223154 | 20261006-223154 |  |

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
- **Related target files**: tools/check_docs_quality.py