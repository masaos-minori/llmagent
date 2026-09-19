# Implementation Procedure: Add stale detection and auto-archive documentation to SKILL.md

## Goal

Add documentation for pre-execution stale detection (Step 2.5) and post-execution auto-archive with collision handling (Step 7) to the `code-implementation` skill's SKILL.md, satisfying REQ-006.

## Scope

- Modify `.opencode/skills/code-implementation/SKILL.md` only
- Document the stale detection behavior: when it triggers, what it reports
- Document the auto-archive behavior: when it triggers, how collisions are handled
- No behavioral changes to the skill itself — documentation-only update

## Assumptions

- The stale detector utility (`scripts/agent/stale_detector.py`) already exists and works correctly (verified in Phase 2 of the parent plan)
- The auto-archive collision handling logic in workflow.md Step 7 is correct
- Both behaviors are already implemented in workflow.md; SKILL.md needs to reflect them

## Design decisions

- Document both behaviors inline in the Core Execution Rules section of SKILL.md, referencing the corresponding workflow.md steps
- Keep documentation concise — a few bullets each, not a broad architecture description
- Use cross-references to workflow.md rather than duplicating procedural detail

## Alternatives considered

- Adding a separate subsection under "Phase overview" for each new step — rejected because the steps are already listed there and Core Execution Rules is the canonical location for behavioral summaries
- Creating a separate documentation file — rejected because the scope is small and SKILL.md is the natural home for skill-level behavioral descriptions

## Implementation

### Target file

`.opencode/skills/code-implementation/SKILL.md`

### Procedure

1. Read the current SKILL.md content
2. Identify the Core Execution Rules section
3. Add/update bullet points documenting:
   - Pre-execution stale detection (referencing workflow.md Step 2.5)
   - Auto-archive with collision handling (referencing workflow.md Step 7)
4. Verify the documentation accurately reflects the current workflow.md

### Method

Edit-based modification of the existing SKILL.md file.

### Details

**Stale detection documentation** (add to Core Execution Rules):
- **Pre-execution stale detection**: see `workflow.md` Step 2.5 — abort execution if any referenced construct is missing from current source. This prevents wasted effort on procedures whose targets have been modified by another process or prior execution. Any single mismatch constitutes "stale"; report all failures in a single pass.

**Auto-archive documentation** (add to Core Execution Rules):
- **Auto-archive with collision handling**: see `workflow.md` Step 7 — if the archive destination already exists, generate a disambiguated path per `rules/filename-collision.md` (zero-padded sequence suffix, max 3 retries). The move does not require human approval — gated on Steps 3/4/6 passing instead.

**Phase overview table** — verify Step 2.5 and Step 7 rows are present:
- Step 2.5: Pre-execution stale detection — verify its description matches the current workflow.md
- Step 7: Move the completed implementation procedure file — verify its description includes auto-archive behavior

## Compatibility considerations

- This change is documentation-only — no behavioral impact on the code-implementation skill
- Existing procedure documents that reference SKILL.md will now have accurate descriptions of stale detection and auto-archive behavior
- The documentation must remain consistent with workflow.md — if workflow.md changes later, SKILL.md should be updated accordingly

## Security considerations

- None — documentation-only change

## Rollback considerations

- Simple revert of the SKILL.md edit restores the previous state
- No data loss risk since no code or configuration is changed

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|------------------|----------------|------------------|
| SKILL.md stale detection docs | Manual review | Read SKILL.md | Documentation accurately describes Step 2.5 behavior |
| SKILL.md auto-archive docs | Manual review | Read SKILL.md | Documentation accurately describes Step 7 auto-archive behavior |
| Cross-reference consistency | Manual review | Compare SKILL.md ↔ workflow.md | All cross-references point to correct step numbers |
| Markdown structure | Lint check | `uv run ruff check .opencode/skills/code-implementation/SKILL.md` | Clean |

## Completion criteria

- [ ] Stale detection behavior documented in Core Execution Rules section
- [ ] Auto-archive behavior documented in Core Execution Rules section
- [ ] Phase overview table includes Step 2.5 and Step 7 with accurate descriptions
- [ ] All cross-references to workflow.md steps are correct
- [ ] Documentation is consistent with workflow.md content
- [ ] ruff lint clean on the modified file

## Out of scope

- Implementing the actual stale detection logic (covered by `scripts/agent/stale_detector.py`)
- Implementing the actual auto-archive logic (covered by workflow.md Step 7)
- Moving existing stale procedures out of `implementations/`
- Archival policies for `implementations/done/`
- Changes to other pipeline phases

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read the current SKILL.md content | Pending | — | — | |
| 2 | Update Core Execution Rules with stale detection and auto-archive documentation | Pending | — | — | |
| 3 | Update phase overview table if needed | Pending | — | — | |
| 4 | Validate documentation accuracy and cross-references | Pending | — | — | |
| 5 | Run lint check on modified file | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260919-121342_impl_proc_stale-detection-and-auto-archive.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-122149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-234412
- **Related target files**: .opencode/skills/code-implementation/SKILL.md
