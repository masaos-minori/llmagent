# Implementation Procedure: ADR Size Reduction Part 2

## Target Files

- `docs/10_adr/ADR-004-environment-failure-handling-policy.md` (currently 43639 bytes, target ≤ 24576)
- `docs/10_adr/ADR-008-sqlite-4db-separation.md` (currently 32051 bytes, target ≤ 24576)

## Scope

This is part 2 of the ADR size reduction effort. Part 1 handled boilerplate removal, Keywords placeholder cleanup, Status list removal, and alternative verbosity trimming for ADR-002, ADR-003, and ADR-006.

Part 2 handles additional structural changes beyond the original scope:
- Adding missing Reason for Rejection / Reconsideration Conditions
- Compressing Known Deviations entries that are already Resolved
- Trimming verbose Verification section entries
- Collapsing Related Documents cross-references
- Removing empty sections (Exceptions, Implementation Notes)
- Trimming Alternative Reason for Rejection sections

**Constraints:**
- Do NOT change any decision, invariant, status, identifier, or architectural intent
- Do NOT restructure large tables (e.g., Recovery Policy Matrix)
- Preserve all INV references and their mappings
- Keep English language for docs/ files

## Step-by-step Procedure

### ADR-004 Changes

#### 1. Alternative D: Add Reason for Rejection and Reconsideration Conditions

Alternative D currently has Description, Advantages, and Disadvantages but lacks Reason for Rejection and Reconsideration Conditions. Add these based on the pattern used by Alternatives A-C.

#### 2. Known Deviations: Compress resolved entries

The following Known Deviation entries are marked as Resolved and contain excessive detail about what was fixed. Compress each entry to its essential information:

- **ADR-004-D1**: Already resolved (2026-09-04). Compress the Observed Implementation and Recommended Action fields.
- **ADR-004-D2**: Already resolved (2026-09-04). Same compression approach.
- **ADR-004-D3**: Already resolved. Compress.
- **ADR-004-D4**: Already resolved. Compress.
- **CI-016**: Already resolved. Compress.

Keep: Known Issue name, Type, Summary, Impact, Resolution Target, Owner, Status, Resolution Target.

Remove/reduce: Observed Implementation details, Recommended Action verbosity, Conflicting Source redundancy.

#### 3. Verification: Trim verbose test references

Several Verification entries have overly detailed test references. Trim to essential information:
- Reduce long parenthetical test descriptions
- Remove redundant "Confirmed (executed and confirmed to pass)" where Status already says Confirmed
- Keep: Test description, Verifies, Type, Blocking, Status

#### 4. Related Documents: Collapse cross-references

The Related Documents section has many links. Collapse where multiple links point to the same document or where links are redundant with Decision section content.

#### 5. Decision Groups: Minor trimming

Some Decision Group bullet points are verbose. Trim where the meaning is preserved.

### ADR-008 Changes

#### 1. Exceptions: Remove empty section

Section "## Exceptions" contains only "None". Remove this section entirely.

#### 2. Implementation Notes: Remove empty section

Section "## Implementation Notes" is empty. Remove this section entirely.

#### 3. Related Documents: Collapse cross-references

Similar to ADR-004, collapse redundant cross-references in Related Documents.

#### 4. Alternatives: Trim Reason for Rejection sections

Several Alternative Reason for Rejection sections are brief but could be more concise while preserving meaning.

#### 5. Recovery Policy Matrix: Row trimming

Review each row of the Recovery Policy Matrix table. If a row's content is identical across all four columns (or follows a predictable pattern), consider whether it can be collapsed into a single note rather than repeated per column.

### Validation

After applying changes, verify:
1. File sizes are ≤ 24576 bytes
2. All INV references are preserved
3. All decision identifiers (Group numbers, Decision numbers) are preserved
4. No structural changes to large tables
5. Run `python tools/check_docs_structure.py` if available

### Commit

Create a clear commit message explaining the reason for changes.
