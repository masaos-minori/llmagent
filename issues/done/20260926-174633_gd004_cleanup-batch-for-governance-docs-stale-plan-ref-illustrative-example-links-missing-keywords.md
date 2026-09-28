# Cleanup batch for governance docs: stale plan ref, illustrative example links, missing Keywords

## Priority
Low

## Summary
A set of small, independent documentation nits across the governance documents. Each is a self-contained fix with no cross-dependency: correct a stale plan reference, make illustrative example-link placeholders unmistakably non-real, and add a missing `## Keywords` section. Two further observations (canonical-map path shorthand and document size limits) are noted for investigation but are not part of the required changes.

## Background
These were surfaced during a routine consistency review of `docs/00_governance/` and by `tools/check_docs_structure.py`. All are documentation-only and do not affect code, tooling behavior, or any other artifact.

## Problem
- **Stale plan reference** (`docs/00_governance/governance_01_documentation-policy.md`, ~lines 195-230): the canonical-source table points at `plans/20260905-185329_plan.md`, which is no longer active — the plan was archived to `plans/done/20260905-185329_plan.md`.
- **Illustrative example links** (`docs/00_governance/governance_02_documentation-metadata.md` lines 137-140 and `docs/00_governance/governance_04_documentation-checks.md` lines 276-279): the "Link Format Examples" cite placeholder filenames (`agent_01_system-overview_00_document-guide.md`, `rag_01_system_overview_00_document-guide.md`) that do not exist anywhere in the repo. They are meant as format illustrations but read as real file references.
- **Missing Keywords** (`docs/00_governance/governance_00_document-guide.md`): the Guide lacks a `## Keywords` body section, which the structure checker flags.

## Reason for Change
Stale links point readers at missing files; unlabeled placeholder links risk being mistaken for real targets; and the missing Keywords section fails the document's own structural contract. None are urgent, but each is a quick, unambiguous improvement.

## Implementation Intent
Apply each fix independently and minimally:
- Point the governance_01 plan reference at its archived location under `plans/done/`.
- Annotate the example-link placeholders so they are clearly illustrative (e.g., wrap in angle brackets or add an explicit "example only" label), without inventing real files.
- Add the missing `## Keywords` section to governance_00 per the metadata policy.

## Target Files or Areas
- `docs/00_governance/governance_01_documentation-policy.md`
- `docs/00_governance/governance_02_documentation-metadata.md`
- `docs/00_governance/governance_04_documentation-checks.md`
- `docs/00_governance/governance_00_document-guide.md`

## Required Changes
- Update the plan reference in `governance_01_documentation-policy.md` from `plans/20260905-185329_plan.md` to `plans/done/20260905-185329_plan.md`.
- Make the example-link placeholders in `governance_02_documentation-metadata.md` (lines 137-140) and `governance_04_documentation-checks.md` (lines 276-279) explicitly illustrative (angle-bracketed names or an "example only" caption), so they cannot be mistaken for existing files.
- Add a `## Keywords` body section to `governance_00_document-guide.md` following the metadata policy.

## Constraints
- Do not alter any semantic content; these are structural, path, and labeling fixes only.
- Keep each change isolated to its own file/section.
- Do not introduce new sections beyond what the policy requires.

## Acceptance Criteria
- The governance_01 plan link resolves to the archived plan under `plans/done/`.
- No example-link placeholder reads as a real, resolvable filename; all are clearly marked illustrative.
- `governance_00_document-guide.md` contains a `## Keywords` section.

## Testing Expectations
Not required (documentation-only). Run `uv run python tools/check_docs_structure.py docs/00_governance/*.md` afterward and confirm none of the above findings remain.

## Documentation Impact
This issue is itself the documentation update. No downstream artifact consumes these sections beyond human review and the structure checker.

## Out of Scope
- Canonical-map path shorthand (see Unresolved Questions) — not part of this batch.
- Document-size decisions (see Unresolved Questions) — not part of this batch.
- Changing any governance rule's substance.
- Editing any document outside `docs/00_governance/`.

## Dependencies
- N/A: none

## Unresolved Questions
- **Canonical-map paths**: `governance_01` lines 236-239 list canonical-source paths without the `00_governance/` subdir, and the same shorthand recurs in `governance_02` (lines 110/114) and `governance_03` prose. These tables are documented as hand-maintained and superseded by `config/documentation_canonical_sources.toml`; decide whether correcting them adds value or should be left as-is.
- **Size limit**: `governance_01` (~30000 B) and `governance_03` (~50410 B) exceed the enforced 24576 B cap. Decide whether these should be split, exempted, or otherwise addressed separately rather than in this cleanup batch.

## AI Implementation Instruction
Apply the three Required Changes in `docs/00_governance/` exactly as listed, keeping each edit minimal and isolated. Do not touch the canonical-map paths or address the size limit unless explicitly asked; instead report your assessment of those two items in your completion notes. Re-run `check_docs_structure.py` on the four files and confirm the flagged findings are cleared.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260926-174633
- **Related target files**: docs/00_governance/governance_00_document-guide.md, docs/00_governance/governance_01_documentation-policy.md, docs/00_governance/governance_02_documentation-metadata.md, docs/00_governance/governance_04_documentation-checks.md
