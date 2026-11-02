## Goal
- Update `skills/code-implementation/workflow.md` so a procedure's companion test files are in the document's scope, are stale-checked with it, are covered by one archive, and count toward the Step 7 Plan update (`REQ-006`: companions in scope, stale check, archival, Step 7 mapping).

## Scope
- Modify only `skills/code-implementation/workflow.md`: the Allowed file operations scope bullet, Step 2 (file identification and the stale-detection note), the Step 3d baseline sentence, and the Step 7 "Plan Execution Status update" mapping sentence. Documentation-only; High blast radius (the workflow executes every procedure).

## Assumptions
- A1: Step 3a: the scope bullet reads "within the scope specified in the current implementation procedure document's Target file / Scope"; Step 2 says "Identify the target feature and all source files to modify" and runs `uv run python tools/stale_detector.py {proc_path}`; Step 3d's baseline sentence already names "the target file, its tests, matched docs"; Step 7 maps Plan steps to rows and sets row N `Completed` only when every file it modifies "has its procedure archived ... check `implementations/done/` for a document with the same `Source plan` and that file as `Related target files`" (verified by Read, 2026-11-02). Edits are located by those phrases, not line numbers.
- A2: Companion behavior of the stale check is created by the `seq` 07 procedure and the `### Companion test files` format by the `seq` 03 procedure, so both exist when this text lands.
- A3: Step 3a: no explicit stop exists for a file outside the procedure scope in this workflow (flowimp011 adds it; Plan 011 Background); this procedure does not add one and keeps the existing "MUST NOT modify files outside the scope" bullet.
- A4: Overlap judgment (Step 2, `check_plan_target_overlaps.py`, 2026-11-02, Plan A7 to A11): this file is also targeted by flowimp008, flowimp011 and (already procedured) flowimp002, flowimp003, flowimp007. Judged compatible by content, a sequencing dependency by file: edits are anchored by text, not line number; whichever Plan lands later rebases. Specific ranges: flowimp008 replaces the manual Plan update in Step 7 with a command and keeps the mapping rule as documented behavior (this procedure's Step 7 edit is the companion clause of that rule: sequencing dependency, Plan A6, A8); flowimp011 adds a stop rule; flowimp002, 003, 007 edit unit, gated, and stale-note text elsewhere.

## Design decisions
- Companions are part of the one document's scope: no new Step; the executor edits the companion test files as part of Step 3d and runs their targeted tests in Step 4, and Step 7 archives the document once.
- For the Step 7 mapping, a companion's row is covered when the archived document lists the file in `Related target files` (target or companion), so a step citing only a test row is `Completed` with its code row's archive.

## Alternatives considered
- A separate archive step per companion: rejected; companions have no document of their own.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Allowed file operations: extend the scope bullet with "and the files listed in its `### Companion test files` section".
2. Step 2: in "Identify the target feature and all source files to modify" add "including companion test files"; in the stale-detection note add that the tool checks each companion with the document (marks and line citations against the companion).
3. Step 3d: add that companions are among "the files this cycle will edit" for the baseline check.
4. Step 7 "Plan Execution Status update": add that a file counts as having its procedure archived when it is the target or a companion of an archived document with the same `Source plan`.

### Method
- Use Edit with the quoted phrases as anchors; each edit adds a clause and removes nothing.
- Keep the call to `set-step-status` and the "not `--description`" text unchanged.

### Details
- No change to the archive command text: `close-implementation` archives the one document; the companion row's Plan step uses the document's `Related target files`.

## Compatibility considerations
- N/A: additive clauses; documents without companions run exactly as before.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`: no findings.
- `uv run python tools/check_skills_heading_cycles.py`: no findings.

## Completion criteria
- The workflow states companion scope, the stale check, single archival, and the Step 7 mapping rule (AC-5); both checkers pass.

## Out of Scope
- The Step 7 command replacement (flowimp008), the out-of-scope-file stop rule (flowimp011), and any change to `tools/manage_workitem_stage.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the scope bullet, Step 2, Step 3d, and the Step 7 mapping sentence for companions | Completed | 20261102-133730 | 20261102-133730 | scope bullet, Step 2 (+stale note), Step 3d baseline, Step 7 mapping edited; stale check clean; full suite deferred to plan end |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Completed | 20261102-133730 | 20261102-133730 | check_skills_references and check_skills_heading_cycles: no issues |

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
- **Requirement ID**: REQ-006 (companions in code-implementation scope, stale check, archive, Step 7 mapping)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `skills/code-implementation/workflow.md`
