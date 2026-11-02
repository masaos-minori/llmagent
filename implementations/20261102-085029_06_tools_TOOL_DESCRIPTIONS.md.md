## Goal
- Update the `stale_detector.py` description in `tools/TOOL_DESCRIPTIONS.md` with sibling resolution, the order rule, and the two options (`REQ-005`: tool description registered).

## Scope
- Modify only the `stale_detector.py` table row and the "Stale Detector Rules" section of `tools/TOOL_DESCRIPTIONS.md`. Documentation-only; Low blast radius, churn is high so edits stay local.

## Assumptions
- A1: Step 3a: the description appears as one table row (`stale_detector.py`, Consistency checker) and a "Stale Detector Rules" section with bullets for `(new)` on symbols, imports, and target files (verified by Read, 2026-11-02). The Plan's "`stale_detector.py` entry" is read as this row plus the rules section; both are in the same row-scoped file, so no additional target file is involved.
- A2: The option names (`--sibling-order`, `--no-siblings`) and the behavior come from the `seq` 01 procedure, so the text matches the implemented tool when it lands.
- A3: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02): this file is targeted by six Frozen Plans (flowimp001, 003, 007, 008, 010, 011). Judged compatible: each adds or updates its own row or section (Plan A7); this Plan touches only the `stale_detector.py` row and the rules section.
- A4: `tools/check_tool_descriptions_sync.py` compares tool file names with table rows; no tool is added or removed here, so it passes unchanged.

## Design decisions
- Keep the table row short: add one clause saying the tool also resolves names declared `(new)` by earlier sibling procedures of the same Plan.
- Put the detail in the rules section as a new bullet group after the target-file `(new)` bullets: Source plan matching by basename, default earlier-`seq` order, the options, the informational line, warnings for unreadable siblings, and no change for documents without a `Source plan`.

## Alternatives considered
- N/A: placement fixed by the existing file structure.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the `stale_detector.py` row and the "Stale Detector Rules" heading at execution time (other Plans edit this file).
2. Edit the row and add the bullet group; do not touch other rows.

### Method
- Use Edit with the unique row text of `stale_detector.py` and the unique bullet `A missing name without the marker is stale as before.` as anchors.

### Details
- Bullets: sibling resolution (what and where it searches: `implementations/` and `implementations/done/`); order rule (earlier `seq`); `--sibling-order any`; `--no-siblings`; output line wording `resolved from sibling: {name} declared (new) in {document}`; unreadable sibling is a warning; no `Source plan` or no siblings behaves as before.

## Compatibility considerations
- N/A: description text only.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`: passes (AC-4).

## Completion criteria
- The row and rules section describe sibling resolution, the order rule, and both options (REQ-005); the sync check passes.

## Out of Scope
- Other tool rows and sections; rows that other Plans add.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `stale_detector.py` row and the Stale Detector Rules section in `tools/TOOL_DESCRIPTIONS.md` | Pending | — | — | |
| 2 | Run `check_tool_descriptions_sync.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261030-191457_flowimp007_stale-sibling-new.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080513_flowimp007_stale-sibling-new.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085029
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
