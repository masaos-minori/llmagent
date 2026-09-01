## Goal

Fix `tools/check_needs_confirmation_inventory.py` so it reads the Needs Confirmation inventory from its current location (`docs/00_governance_03_issue-and-uncertainty-management.md`, Part 2) instead of the removed standalone file, enabling the automated consistency check to run correctly. (REQ-001 through REQ-006)

## Scope

Update the tool's inventory source path, parsing logic for the new document structure, and meta-doc exclusion list to reflect the consolidation.

## Assumptions

- The Part 2 section boundary in `docs/00_governance_03_issue-and-uncertainty-management.md` is stable and will not change in the near term
- The `#### NC-\d+` heading format is consistent across all NC entries in Part 2
- The status vocabulary (`open`, `investigating`, `deferred`, `fixed`) is stable and will not change

## Design decisions

- Use section-scoped parsing (skip until `## Part 2: Needs Confirmation Inventory`, then parse NC entries until next `##` heading or EOF) rather than relying on a separate file, because the consolidated document structure is the canonical source
- Support both `"resolved"` and `"fixed"` as valid resolved status values during transition, matching the current inventory's usage (NC-020 uses `"fixed"`)
- Keep backward compatibility for 3-level headings (`### NC-\d+`) during transition period per the plan's risk mitigation, though current evidence shows only 4-level headings exist

## Alternatives considered

- Keeping the old filename constant and adding a fallback search for the new location: rejected because the old file does not exist and the tool should fail fast if the expected path is missing
- Adding a deprecation shim that maps the old filename to the new one: rejected because the old file was deleted and no migration path exists
- Using a TOML/YAML config file for the inventory path: rejected because this is a simple constant change; introducing external config adds unnecessary complexity

## Implementation

### Target file

`tools/check_needs_confirmation_inventory.py`

### Procedure

Phase 1: Update constants and metadata. Phase 2: Update parsing logic. Phase 3: Verify execution.

### Method

#### Phase 1: Preparation / Refactoring

1. Update `INVENTORY_DOC_NAME` constant from `"00_governance_07_needs-confirmation-inventory.md"` to `"00_governance_03_issue-and-uncertainty-management.md"` (line 44).

2. Update `_GOVERNANCE_META_DOCS` frozenset: replace the `INVENTORY_DOC_NAME` variable reference with the literal `"00_governance_03_issue-and-uncertainty-management.md"` string (lines 49-60). This ensures the consolidated governance doc is excluded from the untracked-inline-markers check, since it contains NC inventory entries rather than inline "Needs confirmation" markers.

3. Update the module docstring comment referencing the old standalone file path (`docs/00_governance_07_needs-confirmation-inventory.md` appears in lines 4-6). Replace references to the old filename with the new consolidated document path.

#### Phase 2: Core Logic Implementation

4. Update `_NC_ENTRY_RE` regex from `r"^### (NC-\d+)\s*$"` to `r"^#### (NC-\d+)\s*$"` (line 63). Current state verified: the regex matches 3-level headings; the new inventory uses 4-level headings (confirmed at lines 96, 113, 131 of `docs/00_governance_03_issue-and-uncertainty-management.md`).

5. Add section-scoping logic to `_parse_inventory_entries()`: before parsing NC entries, skip lines until reaching `## Part 2: Needs Confirmation Inventory`; then parse NC entries until the next `##` heading or end of file. This prevents Part 1 Known Issue entries from being misinterpreted as NC entries. Use robust regex matching on `## Part 2:` rather than exact string comparison (per plan's risk mitigation).

   Implementation approach:
   - Add a new regex: `_PART2_HEADER_RE = re.compile(r"^## Part 2:")`
   - Add a new regex: `_SECTION_HEADER_RE = re.compile(r"^## ")`
   - In `_parse_inventory_entries()`, add a `in_part2` flag initialized to `False`
   - For each line: if `in_part2` is False and `_PART2_HEADER_RE.match(line)` matches, set `in_part2 = True` and continue
   - If `in_part2` is True and `_SECTION_HEADER_RE.match(line)` matches, break out of parsing
   - Only process NC entry lines when `in_part2` is True

6. Update `check_stale_resolved_markers()` to treat both `"resolved"` and `"fixed"` as resolved statuses. Change the condition at line 140 from `if entry.status != "resolved"` to `if entry.status not in ("resolved", "fixed")`. Current state verified: NC-020 at line 122 of the governance doc uses `"fixed"` as its status.

#### Phase 3: Deployment & Verification

7. Run `uv run python tools/check_needs_confirmation_inventory.py` to verify the tool executes without errors (REQ-006). Expected outcome: exit code 0, no ERROR output.

8. Verify the tool correctly identifies NC-019, NC-020, NC-021 as active items (REQ-001, REQ-002). Expected outcome: the tool reports these three entries as active.

9. Verify the tool does not flag Part 1 Known Issue entries as NC entries (REQ-002). Expected outcome: no false positives from Part 1 content.

10. Check `tests/tools/` for existing test coverage patterns (UNK-01). Evidence: grep found no existing test for `check_needs_confirmation_inventory.py` under `tests/tools/`. Consider adding a basic test exercising the corrected path resolution if an appropriate test pattern exists among the other `tests/tools/` scripts.

## Compatibility considerations

- The tool's public interface (CLI invocation, exit codes, issue reporting format via `Issue` class from `_docs_consistency_lib`) remains unchanged.
- The `_GOVERNANCE_META_DOCS` frozenset update means the consolidated governance doc is now excluded from the untracked-inline-markers check — this is correct because the file contains NC inventory entries (which use the same text pattern) but those are intentional, not untracked items.
- Backward compatibility: if a future governance document reverts to using 3-level headings for NC entries, the updated regex would miss them. Per the design decision above, support for 3-level headings could be added as a transition measure.

## Security considerations

No security impact. This is a bug fix for a documentation consistency checker. The tool reads local files and produces local output.

## Rollback considerations

Rollback is straightforward: revert the four code changes (constants, regex, scoping logic, status check) plus the docstring update. No data migration or configuration rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_needs_confirmation_inventory.py` | Manual execution against current repo | `uv run python tools/check_needs_confirmation_inventory.py` | Exit code 0, no ERROR output |
| `tools/check_needs_confirmation_inventory.py` | Verify NC entry identification | `uv run python tools/check_needs_confirmation_inventory.py` | Reports NC-019, NC-020, NC-021 as active items |
| `tools/check_needs_confirmation_inventory.py` | Verify Part 1 isolation | `uv run python tools/check_needs_confirmation_inventory.py` | No Known Issue entries flagged as NC entries |

## Completion criteria

- `uv run python tools/check_needs_confirmation_inventory.py` runs to completion against the current `docs/` tree without a not-found error (REQ-006)
- The tool correctly identifies the three currently active NC entries (NC-019, NC-020, NC-021) in `docs/00_governance_03_issue-and-uncertainty-management.md` (REQ-001, REQ-002)
- The tool's existing checks (stale resolved-marker detection, "Needs confirmation" mentions registered in the inventory) produce correct results against a deliberately introduced test case (REQ-003, REQ-005)
- No NC entry from Part 1 (Known Issues) is misinterpreted as an NC entry (REQ-002)

## Out of scope

- Changing the tool's check semantics (what counts as a violation)
- Modifying the governance document itself
- Reintroducing a standalone inventory document
- Fixing other unrelated tool/documentation mismatches
- Adding comprehensive unit tests (only consider if an appropriate test pattern exists in `tests/tools/`)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | All 6 changes applied |
| 2 | Add or update tests per Validation plan | Completed | — | — | No existing test pattern found in tests/tools/ |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | Tool executes without not-found error |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope per procedure |

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
- **Requirement ID**: REQ-001 through REQ-006
- **Source issue**: issues/20260831-162016_tool001_needs_confirmation_inventory_path_stale.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260831-221114_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-105439
- **Related target files**: tools/check_needs_confirmation_inventory.py
