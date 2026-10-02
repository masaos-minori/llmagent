# Implementation Procedure: Detect orphaned Needs Confirmation markers in governance docs

## Goal

Modify `_GOVERNANCE_META_DOCS` handling in `check_untracked_inline_markers()` to distinguish between definitional/discussion uses of the "Needs Confirmation" label and actual unresolved-item markers inside governance documents, so that orphaned markers in governance docs are detected without flooding false positives from definition text.

## Scope

- Modify `check_untracked_inline_markers()` to detect unresolved-item markers while exempting definitional mentions.
- Add regression tests: a governance doc fixture with a definitional mention (not reported) and a status-cell marker (reported).
- Record the decision on whether untracked-marker warnings should cause a non-zero exit.

## Assumptions

- Each unresolved-item marker form can be identified by a specific pattern (table cell status value or parenthesized annotation) that does not overlap with definitional text.
- The existing `_GOVERNANCE_META_DOCS` exemption mechanism can be extended with conditional logic rather than requiring a complete rewrite.
- The current output format and severities are sufficient for reporting these findings.

## Design decisions

- Extend the exemption logic in `check_untracked_inline_markers()` rather than removing it entirely. This avoids flooding false positives from definitional text while enabling detection of genuine unresolved-item markers.
- Classify each "Needs Confirmation" occurrence as either **definitional** (exempt) or **unresolved-item marker** (report) based on context: table cell status values and parenthesized annotations are markers; prose references to the label itself are definitional.
- Encode the classification rule as a regex pattern or section-scoped exclusion list, depending on what the inspection reveals.

## Alternatives considered

- Remove the exemption entirely and rely on a whitelist of known definitional sections — rejected because it would require maintaining a fragile list of exempt sections and could miss new definitional content.
- Use a full NLP classifier to distinguish marker vs. definitional usage — rejected because it adds unnecessary complexity and runtime dependency for a problem solvable with pattern-based heuristics.
- Report all occurrences and let downstream consumers filter — rejected because it defeats the purpose of the checker and floods users with noise.

## Implementation

### Target file

`tools/check_needs_confirmation_inventory.py`

### Procedure

1. Inspect every current `needs confirmation` occurrence in the five governance docs (`governance_00_document-guide.md`, `governance_01_documentation-policy.md`, `governance_02_documentation-metadata.md`, `governance_03_issue-and-uncertainty-management.md`, `governance_04_documentation-checks.md`) and classify each as definitional or unresolved-item marker.
2. Define which marker forms inside governance docs count as unresolved-item markers (REQ-001): e.g., Needs Confirmation status value in a table cell, parenthesized status annotation like `(Needs Confirmation)`.
3. Report those markers when they have no matching Inventory entry (REQ-002): modify `check_untracked_inline_markers()` to allow detection of unresolved-item markers while still exempting definitional/discussion uses.
4. Record the decision on whether untracked-marker warnings should cause a non-zero exit (REQ-004): document as decision; no code change needed if exit 0 is intended.

### Method

After inspecting the five governance docs, determine the classification rule. Then modify `check_untracked_inline_markers()` as follows:

1. Replace the blanket exemption at line 222 (`if doc.rel_path in _GOVERNANCE_META_DOCS: continue`) with conditional logic that distinguishes marker types.
2. For each line containing an `_INLINE_MARKER_RE` match in a governance doc, apply the classification rule:
   - If the match is a definitional mention → skip (current behavior preserved).
   - If the match is an unresolved-item marker → report (new behavior).
3. The classification rule will be encoded as a regex pattern or section-scoped exclusion list, depending on what the inspection reveals.

### Details

```python
# Current code (line 222):
#     if doc.rel_path in _GOVERNANCE_META_DOCS:
#         continue

# Proposed replacement:
#     if doc.rel_path in _GOVERNANCE_META_DOCS:
#         # Only process governance docs for unresolved-item markers
#         for line_no, line in enumerate(doc.lines, start=1):
#             if _INLINE_MARKER_RE.search(line):
#                 if _is_definitional_mention(line, doc.rel_path):
#                     continue  # Skip definitional mentions
#                 # Report unresolved-item marker
#                 issues.append(...)
#         continue  # Already processed this doc
#     # ... rest of original logic for non-governance docs
```

A helper function `_is_definitional_mention(line, rel_path)` will implement the classification rule determined during Phase 1 inspection. The exact implementation depends on the patterns found during inspection but may include checks such as:
- Whether the line contains a table cell boundary (`|`) suggesting a status value.
- Whether the match appears in parentheses `(Needs Confirmation)`.
- Whether the surrounding text discusses the label itself (e.g., "defines", "refers to", "see").

## Compatibility considerations

- The change only affects `check_untracked_inline_markers()`. Other functions (`check_missing_nc_fields`, etc.) are unaffected.
- Output format and severities remain unchanged unless the confirmed intent requires change.
- The `_GOVERNANCE_META_DOCS` frozenset structure is preserved; only its usage logic changes.

## Security considerations

- No security impact. The change only modifies how inline markers are classified and reported within the checker tool.

## Rollback considerations

- Revert the conditional logic in `check_untracked_inline_markers()` back to the blanket exemption (`if doc.rel_path in _GOVERNANCE_META_DOCS: continue`).
- Remove the `_is_definitional_mention` helper function if added.
- Remove the regression test class added in Step 2.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_needs_confirmation_inventory.py` | Format + lint | `uv run ruff format tools/check_needs_confirmation_inventory.py` then `uv run ruff check tools/check_needs_confirmation_inventory.py` | Clean (no diffs, no errors) |
| `tools/check_needs_confirmation_inventory.py` | Type check | `uv run mypy tools/check_needs_confirmation_inventory.py` | Pass |
| `tools/check_needs_confirmation_inventory.py` | Security lint | `uv run bandit tools/check_needs_confirmation_inventory.py` | No new findings |
| `tests/tools/test_check_needs_confirmation_inventory.py` | Regression tests | `uv run pytest tests/tools/test_check_needs_confirmation_inventory.py -v --tb=short` | All pass |
| Smoke run | Real Registry check | `uv run python tools/check_needs_confirmation_inventory.py` | Reports orphaned markers in governance docs without false positives on definitional text |

## Completion criteria

- Against the current repository, the checker reports the Area Canonical Maps status markers in `governance_01_documentation-policy.md` as untracked (until canon001 resolves them).
- Definitional mentions of the label in governance docs are not reported.
- New regression tests fail before and pass after the change; existing tests pass.
- The exit-status decision for untracked markers is implemented or documented.

## Out of scope

- Registering or resolving existing untracked markers in `docs/23_agent/` and `docs/21_rag/`.
- Resolving Policy Area Canonical Maps markers (canon001).
- Changing Inventory entry format.
- Editing `docs/00_governance/governance_01_documentation-policy.md` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Inspect governance docs and classify marker forms | Pending | — | — | REQ-001 |
| 2 | Implement conditional exemption logic in check_untracked_inline_markers() | Pending | — | — | REQ-001, REQ-002 |
| 3 | Add regression tests for definitional vs. marker distinction | Pending | — | — | REQ-003 |
| 4 | Record exit-status decision for untracked-marker warnings | Pending | — | — | REQ-004 |
| 5 | Validate: format, lint, type-check, security scan | Pending | — | — | REQ-001 |
| 6 | Validate: run tests | Pending | — | — | REQ-003 |
| 7 | Validate: smoke run on live docs/ | Pending | — | — | REQ-002 |
| 8 | Validate: check_tool_descriptions_sync.py | Pending | — | — | REQ-004 |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004
- **Source issue**: issues/20261001-103602_ncinv001_detect-orphaned-needs-confirmation-markers-in-governance-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261002-070708_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261002-113925
- **Related target files**: tools/check_needs_confirmation_inventory.py
