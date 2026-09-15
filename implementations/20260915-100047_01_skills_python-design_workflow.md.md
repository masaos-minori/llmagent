## Goal
Add an exit condition to Step 3 (Define Architecture) for the unjustifiable-
component-count case, and a "Completed when" line to each of Step 5 (Design Data and
Persistence), Step 6 (Define Error Handling), and Step 7 (Define Test Strategy) in
`skills/python-design/workflow.md` (REQ-001 through REQ-004).

## Scope
In scope: one exit-condition line appended to Step 3's existing "Completed when";
one "Completed when" line each at the end of Step 5, Step 6, and Step 7. Out of
scope: `SKILL.md` line 77's "justified" abstraction wording (already adequate, no
change); Steps 1, 2, 4, 8, 9 (unchanged); adding a numeric threshold to any new line.

## Assumptions
- Adding 1 exit-condition line and 3 "Completed when" lines will not push this file
  over the 400-line File Split Rule trigger in `skills/DESIGN.md`.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), Step 4's existing "Completed when" line (per-module completion style)
models REQ-002 through REQ-004's format. REQ-001's exit condition follows this
project's existing "stop and report {specific item}" pattern rather than inventing
new phrasing, and ties justification to Step 2's use cases, not a numeric threshold,
per the Issue's own Constraint.

## Alternatives considered
- Adding a numeric component-count threshold to REQ-001's exit condition (e.g. "no
  more than N components") — rejected: the Plan's Constraint explicitly forbids
  introducing a numeric threshold; completion is about coverage/justification, not an
  arbitrary count.

## Implementation
### Target file
skills/python-design/workflow.md

### Procedure
1. Locate the end of Step 3's existing "Completed when" sentence (after "...the
   component count is justified against Step 2's use cases."), insert the exit
   condition (REQ-001) before the `---` separator.
2. Locate the end of Step 5's content (after "...avoid exhaustive field listings
   unless required to explain a design decision."), insert the "Completed when" line
   (REQ-002) before the `---` separator.
3. Locate the end of Step 6's content (after "...specify the `with`/`async with`
   boundary for each resource the design introduces, before implementation begins."),
   insert the "Completed when" line (REQ-003) before the `---` separator.
4. Locate the end of Step 7's content (after "Failure-path tests: what happens when a
   dependency fails"), insert the "Completed when" line (REQ-004) before the `---`
   separator.
5. Leave Steps 1, 2, 4, 8, 9 unchanged.

### Method
Use `Edit` with 4 separate `old_string`/`new_string` pairs, each anchored on the exact
final sentence of the corresponding Step (unique in the file).

### Details
- Step 3 (after "...the component count is justified against Step 2's use cases."):
  add `If the component count cannot be justified against Step 2's use cases even
  after attempting to merge components per the rule above: stop and report the
  specific components that could not be justified or merged, rather than proceeding
  with an unjustified count.`
- Step 5 (after "...avoid exhaustive field listings unless required to explain a
  design decision."): add `**Completed when**: every entity identified has Fields and
  types, Validation rules, Storage, and Serialization all specified.`
- Step 6 (after "...specify the \`with\`/\`async with\` boundary for each resource
  the design introduces, before implementation begins."): add `**Completed when**:
  every failure mode identified has Detection, Response, Logging, and User visibility
  all specified, and every resource requiring a \`with\`/\`async with\` boundary has
  it stated.`
- Step 7 (after "Failure-path tests: what happens when a dependency fails"): add
  `**Completed when**: every module has at least one specified test category (unit,
  integration, edge case, or failure-path) matching its actual I/O/boundary
  characteristics from Step 4.`

Do not alter Steps 1, 2, 4, 8, 9, and do not introduce a numeric threshold in any new
line.

## Compatibility considerations
This file is referenced by 16+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file edit adding 4 independent blocks; revertable via `git checkout --
skills/python-design/workflow.md` (pre-commit) or a follow-up commit reverting this
file only.

## Validation plan
- `git diff skills/python-design/workflow.md` — confirm exactly 4 additions (Step 3
  exit condition, Step 5/6/7 completion lines), no other Step touched, no numeric
  threshold introduced.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
Step 3 has an explicit exit condition for the unjustifiable-component-count case;
Step 5, 6, and 7 each have an explicit "Completed when" line; no new line introduces
a numeric threshold; `tools/check_skills_references.py` passes (Plan AC-1, AC-2).

## Out of scope
`SKILL.md` line 77's "justified" wording (already adequate); Steps 1, 2, 4, 8, 9 of
this same file; any other file; any other evaluation criterion from the source
review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-110556 | 20260915-110556 | 4 insertions: Step 3 exit condition, Step 5/6/7 completion lines |
| 2 | Add or update tests per Validation plan | Completed | 20260915-110556 | 20260915-110556 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-110556 | 20260915-110556 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-110556 | 20260915-110556 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 through REQ-004 (Step 3 exit condition; Step 5/6/7 completion)
- **Source issue**: issues/20260914-115701_skillqa13_python-design-workflow-step-completion-and-exit-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-090624_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-100047
- **Related target files**: skills/python-design/workflow.md