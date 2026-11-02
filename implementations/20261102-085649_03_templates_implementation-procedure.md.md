## Goal
- Add the companion test file section to `templates/implementation-procedure.md` and adjust its three one-file statements so a code row's document can list the test files it covers (`REQ-001`: companion section and conditions; `REQ-005`: the format the generator scaffolds).

## Scope
- Modify only `templates/implementation-procedure.md` outside the fenced `markdown` block: the intro sentence "Exactly one document per `Implementation Target Files` row", the lightweight-fill note, the "Target file" bullet in Notes, a new Notes bullet for `### Companion test files`, and the "Related target files" bullet. Documentation-only; Medium blast radius (every procedure follows the template and the generator copies its fenced block).

## Assumptions
- A1: Step 3a: the one-file text is in three places - the intro ("Exactly one document per `Implementation Target Files` row"), the lightweight-fill bullet ("the one-document-per-row invariant is unchanged"), and the Notes "Target file" bullet ("MUST NOT contain modification instructions for more than one file"); the Plan Background said two and was corrected (verified by Read, 2026-11-02).
- A2: Decision (Plan A2): the companion section is `### Companion test files` under `## Implementation`, documented in Notes and NOT added to the fenced block, so `check_workitem_structure.py` (which reads `## ` headings of the fenced block) and the generator's skeleton (`extract_fenced_skeleton`) are unchanged for single-target documents (AC-6).
- A3: Step 3a: the `(new)` marking note near the end of Notes is edited by flowimp007 (archived Plan; procedure `implementations/20261102-085029_05_*`) and the `## Scope` block by flowimp002 (`implementations/20261102-085047_02_*`); this procedure edits different paragraphs (Plan A7). Judged compatible, text-anchored, whichever lands later rebases.
- A4: The format below is parsed by `tools/stale_detector.py` (seq 07) and `tools/check_workitem_traceability.py` (seq 05): a top-level list item whose first backticked token is the companion path, optional `(new)` after it, with indented `Procedure:` and `Validation:` lines.

## Design decisions
- Companion format: a `### Companion test files` heading after `### Details`, then per companion a top-level bullet `- `path` [(new)]` with two indented bullets, `Procedure:` and `Validation:` (one line each). Placing it after `### Details` keeps `### Target file` followed by its path, which the traceability tool reads.
- `Related target files` lists the target first, then each companion, comma-separated, each backticked (Plan A5).

## Alternatives considered
- Put the heading in the fenced block as an optional section: rejected (A2); it would appear in every single-target scaffold and change the checked heading set.

## Implementation
### Target file
`templates/implementation-procedure.md`

### Procedure
1. Intro paragraph: replace "Exactly one document per `Implementation Target Files` row" with "One document per `Implementation Target Files` row; a test file that qualifies as a companion is covered by its code row's document (see the Companion test files note)".
2. Lightweight-fill bullet: change "the one-document-per-row invariant is unchanged" to say a qualifying test row may be a companion instead of its own document.
3. "Target file" bullet: keep the one-modification-target-per-section sentence and add that companions are listed in `### Companion test files`, not in this section; an additional file is still an additional-target discovery.
4. Add a Notes bullet **Companion test files** with the format in Design decisions, the four eligibility conditions by reference to `skills/plan-to-implementation-procedure/SKILL.md` Core Execution Rules, and the fixed rule that a companion's `(new)` follows its path.
5. "Related target files" bullet: add the target-first list form for a document with companions.

### Method
- Use Edit per item, anchored on the quoted phrases; do not touch the fenced block (byte-identical).

### Details
- Example block to include in the new bullet:
  - `### Companion test files`
  - `- ` + backticked `tests/tools/test_example.py` + ` (new)`, with two indented lines `Procedure: ...` and `Validation: ...`.
- Reference `skills/plan-to-implementation-procedure/SKILL.md` for the conditions without restating them (`check_skills_heading_cycles.py` stays clean).

## Compatibility considerations
- N/A: Notes-only addition; the fenced structure and `check_workitem_structure.py` result are unchanged.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_workitem_structure.py --file {this Plan's generated procedure}`: no findings (fixture check from the Plan).
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`: no findings.
- Confirm the fenced block is unchanged: `git diff` shows no hunk inside it.

## Completion criteria
- The Notes define the companion section, its format and `Related target files` form; the three one-file statements allow it; the fenced block is byte-identical; the checkers pass (AC-1).

## Out of Scope
- The fenced block, the `(new)` marking note (flowimp007), the `## Scope` text (flowimp002), and the tool changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the three one-file statements and add the Companion test files note | Pending | — | — | |
| 2 | Run `check_workitem_structure.py` on a generated procedure, `check_skills_references.py`, `check_skills_heading_cycles.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (companion section in the template), REQ-005 (format the generator scaffolds)
- **Source issue**: issues/20261030-191615_flowimp009_test-row-grouping.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080828_flowimp009_test-row-grouping.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085649
- **Related target files**: `templates/implementation-procedure.md`
