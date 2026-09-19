# Implementation Procedure: Add stale detection and auto-archive documentation to SKILL.md

## Goal

Add documentation for pre-execution stale detection (Step 2.5) and post-execution auto-archive with collision handling (Step 7) to the `code-implementation` skill's SKILL.md, satisfying REQ-006.

## Scope

- Modify `skills/code-implementation/SKILL.md` only

**Correction (Step 3a adversarial verification, applied before implementation)**:
the original version of this document cited `.opencode/skills/code-implementation/SKILL.md`
throughout. `.opencode/skills` is a broken symlink in this repository (its target,
`/home/sugimoto/llmagent/skills/`, does not exist on this host — confirmed via
`realpath`), so that path never resolves. Every other Plan/Issue/implementation
procedure document in this repository consistently references this file as
`skills/code-implementation/SKILL.md` (no `.opencode/` prefix) — the correct,
resolvable path is used throughout this correction.
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

`skills/code-implementation/SKILL.md`

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
| Markdown structure | Reference check | `uv run python tools/check_skills_references.py` | Clean — `ruff` does not lint Markdown; this repo's `routing.md` Tools table names `check_skills_references.py` as the checker for a `skills/*.md` edit |

## Completion criteria

- [ ] Stale detection behavior documented in Core Execution Rules section
- [ ] Auto-archive behavior documented in Core Execution Rules section
- [ ] Phase overview table includes Step 2.5 and Step 7 with accurate descriptions
- [ ] All cross-references to workflow.md steps are correct
- [ ] Documentation is consistent with workflow.md content
- [ ] `tools/check_skills_references.py` passes clean

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
| 1 | Read the current SKILL.md content | Completed | 20260920-080000 | 20260920-080000 | Read `skills/code-implementation/SKILL.md` in full (Step 3a). Corrected this document's Target file path from the non-resolving `.opencode/skills/...` (broken symlink; target `/home/sugimoto/llmagent/skills/` does not exist on this host) to `skills/code-implementation/SKILL.md`, matching every other Plan/Issue in this repository. |
| 2 | Update Core Execution Rules with stale detection and auto-archive documentation | Completed | 20260920-080000 | 20260920-080000 | Both bullets already existed in Core Execution Rules from prior work (this Plan's own Execution Status Phase 3 row already records this as Completed on 20260919). Enhanced both bullets with the procedure's additional explanatory sentences (stale-detection rationale; no-approval-gate cross-reference) that were missing from the condensed existing text — a small, safe addition, not a duplicate. |
| 3 | Update phase overview table if needed | Completed | 20260920-080000 | 20260920-080000 | Step 2.5 and Step 7 rows already present with accurate descriptions; no change needed (kept concise per this document's own Design decisions). |
| 4 | Validate documentation accuracy and cross-references | Completed | 20260920-080000 | 20260920-080000 | Cross-checked against current `workflow.md` (already loaded this session): Step 2.5 "Pre-execution Stale Detection" and Step 7's "Auto-archive collision handling (REQ-005)" subsection both exist and match. |
| 5 | Run lint check on modified file | Completed | 20260920-080000 | 20260920-080000 | Corrected Validation plan: `ruff` does not lint Markdown — the applicable checker per `routing.md` Tools table for a `skills/*.md` edit is `tools/check_skills_references.py`, run and passed ("No issues found."). |

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
- **Related target files**: skills/code-implementation/SKILL.md
